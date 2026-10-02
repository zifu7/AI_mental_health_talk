"""检索策略层：向量检索 / BM25 关键词检索 / RRF 混合检索

为什么要有这个文件：rag.py 里的 search() 只有一种策略（纯向量）。
要"改进"它，必须先能"对比"它——所以把三种策略放在同一层里，
输入输出格式统一（都返回 (分块下标, 分数) 的完整排序），
评测脚本才能用同一套指标横向比。

三种策略的分工（也是面试要讲的核心）：
  向量检索（dense）：靠语义相似，能命中"换了个说法"的问题；
                     弱点是精确词、专有名词、罕见术语容易糊（bge-m3 也救不了）。
  BM25（sparse）：靠词面匹配，专有名词一抓一个准；
                  弱点是同义改写完全没辙（用户说"睡不着"，文档写"入睡困难"，词面对不上）。
  混合（RRF）：两边各排一份榜单，用"排名倒数求和"融合——
              不需要把两种分数归一化到同一量纲，简单且鲁棒。

RRF（Reciprocal Rank Fusion）公式：
    score(d) = Σ  1 / (k + rank_i(d))        k 通常取 60
只关心"在各自榜单里排第几"，不关心原始分数是多少——这是它能跨策略融合的关键。
"""
import asyncio
import logging
import math
import re
from collections import Counter
from typing import Any, Dict, List, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article_chunk import ArticleChunk
from app.services.rag import cosine_similarity, get_embedding

logger = logging.getLogger(__name__)

# ==================== 分词（中文：字级 bigram） ====================

# 连字符/下划线算词内字符：CBT-I、4-7-8、bge-m3 必须是一个词
# （早期版本只写 [a-z0-9]+，"CBT-I" 被拆成 "cbt" + "i"，
#   评测里表现为：查询里 idf 最高的词变成了"么是"这种句式功能词，BM25 被带偏 → 见 v3 报告）
_ASCII_RE = re.compile(r"[a-z0-9]+(?:[-_][a-z0-9]+)*")
_CJK_RE = re.compile(r"[一-鿿]")   # 汉字区间，用转义写避免肉眼看错字


def tokenize(text: str) -> List[str]:
    """中文用"相邻两字"切成 bigram，英文/数字整体保留。

    为什么不装 jieba：一是少一个依赖，二是原理更透明——
    "睡不着" → ["睡不", "不着"]，只要查询和文档用同一套切法，
    匹配依然成立（这是 CJK 检索的经典做法）。
    真实项目中中文检索建议上 jieba 或 jieba 的分词 + 同义词表，效果更稳。
    """
    text = text.lower()
    tokens = _ASCII_RE.findall(text)          # 英文、数字（如 ssri、cbt-i、4-7-8）
    cjk = _CJK_RE.findall(text)               # 只留汉字，标点自然被过滤掉
    tokens += ["".join(pair) for pair in zip(cjk, cjk[1:])]   # 相邻两字
    return tokens


# ==================== BM25（手写，公式就这几行） ====================

class BM25:
    """Okapi BM25：TF 饱和 + 文档长度归一化 + IDF 稀有度加权

    score(q, d) = Σ_t idf(t) * [ f(t,d) * (k1+1) / ( f(t,d) + k1 * (1 - b + b * |d|/avgdl) ) ]

    三个直觉：
      1. idf：词越稀有越值钱——"失眠"比"的"重要得多
      2. k1 控制 TF 饱和：一个词出现 10 次不等于重要 10 倍（k1=1.5 时收益很快递减）
      3. b 控制长度归一化：长文档天然更容易命中词，需要打折（b=0.75）
    """

    def __init__(self, docs_tokens: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.n_docs = len(docs_tokens)
        self.tf: List[Counter] = [Counter(tokens) for tokens in docs_tokens]
        self.doc_len = [len(tokens) for tokens in docs_tokens]
        self.avgdl = (sum(self.doc_len) / self.n_docs) if self.n_docs else 0.0

        df = Counter()
        for tokens in docs_tokens:
            df.update(set(tokens))                    # 每个词在多少篇文档里出现过
        # 加 0.5 平滑，避免 df 为 0 时除零；+1 保证 idf 非负
        self.idf = {
            term: math.log(1 + (self.n_docs - d + 0.5) / (d + 0.5))
            for term, d in df.items()
        }

    def scores(self, query_tokens: List[str]) -> List[float]:
        # 查询里的重复词去重：BM25 不考虑查询词频（避免同一个词刷分）
        terms = set(query_tokens)
        result: List[float] = []
        for i, tf in enumerate(self.tf):
            score = 0.0
            norm = self.k1 * (1 - self.b + self.b * self.doc_len[i] / (self.avgdl or 1))
            for term in terms:
                f = tf.get(term)
                if not f:
                    continue
                score += self.idf.get(term, 0.0) * f * (self.k1 + 1) / (f + norm)
            result.append(score)
        return result


# ==================== 语料加载 ====================

async def load_chunks(db: AsyncSession) -> List[Dict[str, Any]]:
    """一次性把所有分块读进内存（id / article_id / content / embedding）

    评测和多策略检索都基于这份快照，保证各策略看到的语料完全一致——
    对照实验的基本要求：一次只变一个变量。
    """
    rows = (await db.execute(select(ArticleChunk))).scalars().all()
    return [
        {
            "chunk_id": row.id,
            "article_id": row.article_id,
            "content": row.content,
            "embedding": row.embedding,
        }
        for row in rows
    ]


# ==================== 索引缓存（语料快照 + BM25 跨请求复用） ====================

# 之前每个请求都要：全表读分块 + 全量分词 + 重建 BM25。几百个分块时只是
# 几十毫秒的浪费，分块上千后就是每个请求 O(语料) 的灾难——检索层不能
# 随语料线性变慢。缓存后只有"冷启动"和"语料真的变了"才重建。

# 失效判断用 (COUNT, MAX(id)) 做版本探针，而不是 TTL：
#   1. 比如"全表读取 + 全量分词"，版本探针是一次走主键索引的轻量查询；
#   2. 任何写路径都是"先删后插"（见 rag.save_chunks），新分块的自增 id
#      必然更大，所以这两项一变就说明语料变了——不需要等 TTL，改完即生效；
#   3. 局限：绕过应用层直接改库（手工 SQL）探针测不到，需要重启服务或
#      调用 invalidate_index_cache()。
_index_lock = asyncio.Lock()
_index_cache: Dict[str, Any] = {"key": None, "chunks": [], "bm25": None}


async def _corpus_key(db: AsyncSession) -> Tuple[int, int]:
    """语料版本探针：(分块总数, 最大分块 id)"""
    row = (
        await db.execute(select(func.count(ArticleChunk.id), func.max(ArticleChunk.id)))
    ).one()
    return (row[0] or 0, row[1] or 0)


async def load_index(db: AsyncSession) -> Tuple[List[Dict[str, Any]], BM25]:
    """取 (分块快照, BM25 索引)，命中缓存时零重建开销。"""
    key = await _corpus_key(db)
    if _index_cache["key"] == key:
        return _index_cache["chunks"], _index_cache["bm25"]

    # 加锁防惊群：冷启动瞬间并发请求如果各自重建一遍，等于没有缓存
    async with _index_lock:
        key = await _corpus_key(db)          # 双重检查：等锁期间可能已有人建好
        if _index_cache["key"] != key:
            chunks = await load_chunks(db)
            _index_cache["chunks"] = chunks
            _index_cache["bm25"] = BM25([tokenize(c["content"]) for c in chunks])
            _index_cache["key"] = key
            logger.info("检索索引重建完成：%d 个分块", len(chunks))
        return _index_cache["chunks"], _index_cache["bm25"]


def invalidate_index_cache() -> None:
    """强制下次请求重建索引（手工改库后用；正常写入会自动失效）"""
    _index_cache["key"] = None


# ==================== 三种排序策略（统一返回完整排序） ====================

def vector_rank(query_vec: List[float], chunks: List[Dict]) -> List[Tuple[int, float]]:
    """纯向量：余弦相似度全量打分（和 rag.search 的算法一致）"""
    scored = [
        (idx, cosine_similarity(query_vec, chunk["embedding"]))
        for idx, chunk in enumerate(chunks)
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def bm25_rank(query: str, chunks: List[Dict], bm25: BM25) -> List[Tuple[int, float]]:
    """纯 BM25：只做词面匹配"""
    scores = bm25.scores(tokenize(query))
    scored = list(enumerate(scores))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def rrf_fuse(
    rankings: List[List[Tuple[int, float]]],
    weights: List[float] | None = None,
    k: int = 60,
    cutoffs: List[int] | None = None,
) -> List[Tuple[int, float]]:
    """RRF 融合：只吃"排名"，不吃原始分数

    两个旋钮：
      weights  给不同榜单加权（更信向量就 [2.0, 1.0]）——比调"分数怎么归一化"稳得多；
      cutoffs  限制每个榜单只有前 N 名有投票权。
               为什么要截断：弱策略（这里是 BM25）把几百个无关文档也排出一二三四名，
               这些"垃圾排名"会和高分榜单的中游分数相加，把噪声顶上来。
               截断 = 只采纳它的"强观点"。
    """
    weights = weights or [1.0] * len(rankings)
    fused: Dict[int, float] = {}
    for i, (ranking, weight) in enumerate(zip(rankings, weights)):
        limit = cutoffs[i] if cutoffs else len(ranking)
        for rank, (idx, _score) in enumerate(ranking[:limit], start=1):
            fused[idx] = fused.get(idx, 0.0) + weight / (k + rank)
    return sorted(fused.items(), key=lambda x: x[1], reverse=True)


def hybrid_rank(
    query: str,
    query_vec: List[float],
    chunks: List[Dict],
    bm25: BM25,
    weights: Tuple[float, float] = (1.0, 1.0),
) -> List[Tuple[int, float]]:
    """混合检索 = 向量榜 + BM25 榜 → RRF 融合"""
    return rrf_fuse(
        [vector_rank(query_vec, chunks), bm25_rank(query, chunks, bm25)],
        weights=list(weights),
    )


def hybrid_rank_cut(
    query: str,
    query_vec: List[float],
    chunks: List[Dict],
    bm25: BM25,
    weights: Tuple[float, float] = (2.0, 1.0),
    bm25_top: int = 10,
) -> List[Tuple[int, float]]:
    """混合检索（截断版）：向量全榜有票，BM25 只有前 10 名有票"""
    return rrf_fuse(
        [vector_rank(query_vec, chunks), bm25_rank(query, chunks, bm25)],
        weights=list(weights),
        cutoffs=[len(chunks), bm25_top],
    )


def hybrid_rerank(
    query: str,
    query_vec: List[float],
    chunks: List[Dict],
    bm25: BM25,
    candidate_k: int = 20,
) -> List[Tuple[int, float]]:
    """另一种融合思路：先"扩召回"，再用向量精排

    RRF 是"两家一起投票决定排名"；这个是"两家各出 20 个候选，最后由向量拍板"。
    区别在分工：稀疏检索负责召回（把可能相关的都捞进来），稠密检索负责排序。

    局限也很明确：如果正确答案压根不在两个候选集里，这个方案同样救不回来——
    重排只能改变"已召回内容"的顺序。
    """
    vec_ranking = vector_rank(query_vec, chunks)
    bm_ranking = bm25_rank(query, chunks, bm25)
    candidates = {idx for idx, _ in vec_ranking[:candidate_k]}
    candidates |= {idx for idx, _ in bm_ranking[:candidate_k]}
    scored = [
        (idx, cosine_similarity(query_vec, chunks[idx]["embedding"]))
        for idx in candidates
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def dedupe_by_article(ranking: List[Tuple[int, float]], chunks: List[Dict]) -> List[Tuple[int, float]]:
    """同一篇文章只保留排名最靠前的那一段

    为什么：一个问题的答案通常集中在文章的一两段里，top-3 如果塞进同篇文章的三段，
    等于浪费了另外两篇可能更相关文章的位置。这是"结果多样性"后处理，
    和排序策略是两个独立层次的问题。
    """
    seen = set()
    result = []
    for idx, score in ranking:
        article_id = chunks[idx]["article_id"]
        if article_id in seen:
            continue
        seen.add(article_id)
        result.append((idx, score))
    return result


# ==================== 生产入口（给 rag.answer_sources 用） ====================

# 拒答阈值 τ：融合榜单 top1 的余弦低于它 → 判定为库外问题，返回空结果。
# 取值依据 eval/results/report_v3_tokenizer.md 的阈值扫描（生产候选 hybrid_cut_dedup）：
#   τ=0.55 → 放行率 0.93 / 误召率 0.12
#   τ=0.60 → 放行率 0.80 / 误召率 0.00
# 选 0.55 的理由：0.60 会拒掉 20% 的正常问题，代价太大；误召的那 12% 还有
# prompt 里"资料没查到就说没查到"兜第二道防线。宁可查了再拒，不要一上来就拒。
# 改动这个值必须同步重跑评测并在报告里留档——生产参数和评测报告对不上，报告就白做了。
MIN_TOP1_COSINE = 0.55


async def hybrid_search(db: AsyncSession, query: str, top_k: int = 5) -> List[Dict]:
    """混合检索（生产入口）：返回格式与 rag.search 完全一致，可以原地替换

    参数和评测里胜出的 hybrid_cut_dedup 严格一致，不许"生产偷偷换参数"——
    否则线上表现和评测报告对不上，报告就白做了。
        weights=(2.0, 1.0)  更信向量，BM25 只做补充
        bm25_top=10         只采纳 BM25 的"强观点"，不让它的中游噪声参与投票
        文章去重             一个回答里不塞两段同源内容
        阈值拒答             top1 余弦 < MIN_TOP1_COSINE 时返回 []（库外问题）
    """
    chunks, bm25 = await load_index(db)
    if not chunks:
        return []
    query_vec = await get_embedding(query)
    ranking = hybrid_rank_cut(query, query_vec, chunks, bm25)

    # 拒答判断算的是"融合榜单 top1 的余弦"，和评测报告里 top1_cos 的口径
    # 完全一致（不是全库最大余弦——那等于偷偷换参数，报告就对不上了）。
    top1_cos = cosine_similarity(query_vec, chunks[ranking[0][0]]["embedding"])
    if top1_cos < MIN_TOP1_COSINE:
        logger.info(
            "拒答：top1 余弦 %.3f < 阈值 %.2f，判定库外问题 | query=%s",
            top1_cos, MIN_TOP1_COSINE, query[:50],
        )
        return []

    results = []
    seen_articles = set()
    for idx, score in ranking:
        chunk = chunks[idx]
        # 同一个文章只取最相关的一段：一次回答里塞两段同源内容纯属浪费 token
        if chunk["article_id"] in seen_articles:
            continue
        seen_articles.add(chunk["article_id"])
        results.append({
            "article_id": chunk["article_id"],
            "content": chunk["content"],
            "score": round(score, 6),
        })
        if len(results) >= top_k:
            break
    return results


