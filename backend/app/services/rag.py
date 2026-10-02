"""RAG 检索增强生成服务

核心流程（RAG 的全部秘密就在这条链路里）:
    文章 → 切分 → 向量化 → 存库
    提问 → 向量化 → 检索 top-k → 拼 prompt → DeepSeek 回答（带引用）

机械部分（调 API、算余弦、查库）已经写好，你只需要写两个函数：
    chunk_text()   —— 怎么把文章切成小段（决策：切多大、怎么切）
    build_prompt() —— 怎么把检索结果拼进提示词（决策：引用格式、人设、防幻觉）
"""
import logging
import re
import httpx
from collections import OrderedDict
from typing import List, Dict
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.article import Article
from app.models.article_chunk import ArticleChunk

logger = logging.getLogger(__name__)


# ==================== 机械部分（已完成，看懂即可） ====================

# 查询向量缓存（LRU）：同一个问题不必反复调 API——一次调用几十到几百毫秒，
# 而"最近大家爱问什么"明显是重复的（多用户问同一类问题是常态）。
# 只缓存"查询"，不缓存建索引时的分块文本：查询是每请求都走的热路径，
# 分块只在重建索引时用一次，缓存它收益低、占内存还翻倍。
# key 带模型名：换 embedding 模型后旧向量自动失效，不会串味。
# 内存账：128 * 1024 维 * 约 32 字节/元素 ≈ 4MB，2G 服务器可接受。
# 局限：进程内缓存，多 worker 各存一份；单 worker 部署（当前就是这个）命中率最高。
_EMBED_CACHE: "OrderedDict[str, List[float]]" = OrderedDict()
_EMBED_CACHE_MAX = 128


async def get_embedding(text: str) -> List[float]:
    """把文本变成向量：调用 embedding API（带内存缓存，命中则零网络开销）"""
    cache_key = f"{settings.EMBEDDING_MODEL}\x00{text}"
    cached = _EMBED_CACHE.get(cache_key)
    if cached is not None:
        _EMBED_CACHE.move_to_end(cache_key)   # 标记为最近使用
        return cached

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.EMBEDDING_BASE_URL}/embeddings",
            headers={
                "Authorization": f"Bearer {settings.EMBEDDING_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"model": settings.EMBEDDING_MODEL, "input": text},
        )
        if response.status_code != 200:
            raise Exception(f"Embedding 调用失败: {response.status_code} {response.text}")
        vector = response.json()["data"][0]["embedding"]

    _EMBED_CACHE[cache_key] = vector
    if len(_EMBED_CACHE) > _EMBED_CACHE_MAX:
        _EMBED_CACHE.popitem(last=False)      # 淘汰最久未使用的
    return vector


async def embed_batch(texts: List[str]) -> List[List[float]]:
    """批量向量化：一次请求发 10 条，比逐条调 API 快一个数量级

    建索引时用（140 个分块逐条调要两分钟，批量只要十几秒）。
    注意返回顺序：API 不保证按输入顺序返回，必须按 index 字段重排。
    """
    vectors: List[List[float]] = []
    for i in range(0, len(texts), 10):
        batch = texts[i:i + 10]
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.EMBEDDING_BASE_URL}/embeddings",
                headers={
                    "Authorization": f"Bearer {settings.EMBEDDING_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={"model": settings.EMBEDDING_MODEL, "input": batch},
            )
            if response.status_code != 200:
                raise Exception(f"Embedding 批量调用失败: {response.status_code} {response.text}")
            data = sorted(response.json()["data"], key=lambda d: d["index"])
            vectors += [d["embedding"] for d in data]
    return vectors


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """余弦相似度：两个向量夹角的余弦，越接近 1 越相似（比长度更关心方向）"""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(x * x for x in vec_a) ** 0.5
    norm_b = sum(x * x for x in vec_b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


async def load_published_articles(db: AsyncSession) -> List[Article]:
    """取所有已发布文章作为语料"""
    result = await db.execute(select(Article).where(Article.status == 1))
    return result.scalars().all()


async def save_chunks(db: AsyncSession, article_id: int, chunks: List[str]) -> None:
    """切分结果向量化后存入 article_chunks 表（重建索引时先清掉旧数据）

    用批量向量化：140 个分块逐条调 API 要两分钟，批量只要十几秒。
    """
    await db.execute(delete(ArticleChunk).where(ArticleChunk.article_id == article_id))
    if chunks:
        vectors = await embed_batch(chunks)
        for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
            db.add(ArticleChunk(
                article_id=article_id,
                chunk_index=idx,
                content=chunk,
                embedding=vector,
            ))
    await db.commit()


# 索引时是否把标题拼进每个分块——留成开关是为了做 A/B 对比（见 eval/run_eval.py）
INCLUDE_TITLE_IN_CHUNK = True


async def build_index(db: AsyncSession) -> int:
    """全量重建索引：所有已发布文章 → 切分 → 向量化 → 存库，返回分块总数

    切分之后、向量化之前，给每个分块加上【文章标题】前缀。
    为什么：标题是整篇文章最强的主题信号，而它原本不参与检索——
    比如"运动与情绪：为什么跑步能让人变好"这篇，正文里根本没有"心情"两个字，
    用户搜"运动能让心情变好吗"就只能靠语义碰运气。
    加上前缀后，标题里的词同时进入了向量（语义）和词面（BM25）两条通道。
    注意：标题只影响"送去向量化的文本"，chunk_text 的切分逻辑不动。
    """
    articles = await load_published_articles(db)
    total = 0
    for article in articles:
        chunks = chunk_text(article)          # ← 调用你写的函数
        if INCLUDE_TITLE_IN_CHUNK:
            chunks = [f"【{article.title}】{chunk}" for chunk in chunks]
        await save_chunks(db, article.id, chunks)
        total += len(chunks)
        logger.info("文章[%s]已切分 %d 段", article.title, len(chunks))
    return total


async def search(db: AsyncSession, query: str, top_k: int = 3) -> List[Dict]:
    """检索：把问题变成向量，和所有 chunk 向量比余弦，返回最像的 top_k

    为什么暴力全量扫描：你的数据规模（几百个分块）全算一遍也就几毫秒。
    等数据量上来再考虑向量数据库——面试能讲出这个决策就是加分点。
    """
    query_vec = await get_embedding(query)
    result = await db.execute(select(ArticleChunk))
    chunks = result.scalars().all()

    scored = []
    for chunk in chunks:
        score = cosine_similarity(query_vec, chunk.embedding )
        scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)

    return [
        {
            "article_id": chunk.article_id,
            "content": chunk.content,
            "score": round(score, 4),
        }
        for score, chunk in scored[:top_k]
    ]


# ==================== 决策部分（你来写） ====================

def chunk_text(article: Article) -> List[str]:
    """TODO【你来写】把一篇文章切成若干小段，返回字符串列表

    提示（先跑通，别追求完美，之后回来优化就是面试里的"迭代过程"）：
      1. article.content 先按段落切（\n\n 或 \n）
      2. 单段超过 300 字再切成更小的块（按句号）
      3. 太短的段（< 20 字）可以丢弃
      4. 想一想：切太大会怎样（检索到太多无关内容）？切太小会怎样（语义不完整）？
    """
    final_chunks = []
    paragraphs = article.content.split("\n")
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(para)<20:
            continue
        if len(para)<=300:
            final_chunks.append(para)
            continue
        else:
            sentences = para.split("。")
            temp_buffer = ""
            for sent in sentences:
                if not sent:
                    continue
                sent = sent + "。"
                if len(temp_buffer + sent)>300:
                    if len(temp_buffer)>20:
                        final_chunks.append(temp_buffer)
                        temp_buffer = sent
                else:
                    temp_buffer += sent  
            if len(temp_buffer)>20:
                final_chunks.append(temp_buffer)   
    return final_chunks


def build_prompt(question: str, contexts: List[Dict]) -> str:
    """把检索结果拼成系统提示词：人设 + 编号资料 + 回答规则 + 问题

    提示词工程的第一课：提示词 = 几块固定文字拼起来，每块各管一件事
    """
    # 第 1 块：人设（和 ai_client 里小暖的风格保持一致）
    parts = ["你是心理健康助手小暖。请先阅读以下参考资料，然后回答用户的问题。\n"]

    # 第 2 块：编号资料（enumerate 从 1 开始编号，ctx 是 dict，用 ["content"] 取值）
    for i, ctx in enumerate(contexts, 1):
        parts.append(f"【资料{i}】\n{ctx['content']}\n")

    # 第 3 块：回答规则（第 1 条是防幻觉的关键，第 2 条就是"引用来源"）
    parts.append(
        "回答要求：\n"
        "1. 只依据以上资料回答，资料里没有的信息要说明“没有查到相关资料”，不要编造\n"
        "2. 引用资料内容时，在句末标注编号，如 [1][2]\n"
        "3. 语气保持温暖、专业\n"
    )

    # 第 4 块：用户的问题
    parts.append(f"用户的问题：{question}")

    # 用空行连接所有块
    return "\n".join(parts)


async def answer_sources(db: AsyncSession, question: str, top_k: int = 3) -> List[Dict]:
    """检索资料并补上文章标题（参考资料展示用）

    生产走混合检索（retrieval.hybrid_search）——评测结论见 eval/results/report_v3_tokenizer.md：
    hybrid_cut_dedup 在 Hit@3 / Recall@5 / 口语化类上都是最优。

    返回空列表有两种情况，调用方都要当作"没查到资料"处理：
      1. 知识库里确实没有相关分块（空库 / 完全不相关的问法）
      2. 答案相关度低于拒答阈值（retrieval.MIN_TOP1_COSINE）——库外问题
    """
    # 函数内 import 打破循环依赖：retrieval 需要 rag 的 get_embedding，
    # 顶层互相 import 会在模块加载时成环。有依赖环时把 import 下沉到函数里是最省事的解法。
    from app.services.retrieval import hybrid_search

    contexts = await hybrid_search(db, question, top_k)
    article_ids = {c["article_id"] for c in contexts}
    if article_ids:
        rows = (
            await db.execute(select(Article).where(Article.id.in_(article_ids)))
        ).scalars().all()
        titles = {a.id: a.title for a in rows}
        for c in contexts:
            c["title"] = titles.get(c["article_id"], f"文章{c['article_id']}")
            c["content"] = strip_title_prefix(c["content"])
    return contexts


_TITLE_PREFIX_RE = re.compile(r"^【[^】]*】\s*")


def strip_title_prefix(content: str) -> str:
    """去掉分块开头的【标题】前缀

    索引时故意加上它，是为了让标题参与检索（向量和 BM25 都能吃到）；
    但展示给模型时标题已经作为独立字段给出，正文里再留一遍纯属重复，
    还会白占 _search_kb_impl 那 150 字的截断额度。
    ——"索引用的文本"和"展示用的文本"本来就可以不是同一个，这是 RAG 的常见做法。
    """
    return _TITLE_PREFIX_RE.sub("", content, count=1)


def format_citations(contexts: List[Dict]) -> str:
    """生成回答末尾的"参考资料"文本

    编号顺序和 build_prompt 里的【资料n】一致，模型回答的 [n] 就对应这里的第 n 条
    这段文本会拼进消息内容存库，刷新聊天记录后引用依然可见
    """
    lines = ["\n\n**📚 参考资料：**"]
    for i, ctx in enumerate(contexts, 1):
        lines.append(f"{i}. {ctx['title']}")
    return "\n".join(lines)
