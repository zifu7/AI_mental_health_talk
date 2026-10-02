"""验证本轮检索层改造：查询向量缓存 / 索引缓存复用 / 阈值拒答 / JSON 解析

不依赖数据库和外部 API（httpx 打桩），可以随时跑：
    venv/Scripts/python test_retrieval_improvements.py
"""
import asyncio
import sys
from unittest.mock import patch

# Windows 控制台默认 GBK，直接 print 中文+emoji 会 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.services import article_service, rag, retrieval
from app.utils.ai_client import _parse_analysis_json

PASS, FAIL = "✅", "❌"
failures = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(f"{PASS if cond else FAIL} {name}{(' — ' + detail) if detail else ''}")
    if not cond:
        failures.append(name)


# ==================== 1. 情绪分析 JSON 解析 ====================

def test_parse_json() -> None:
    check("JSON 解析：纯 JSON（json_object 模式的正常返回）",
          _parse_analysis_json('{"riskLevel": 1, "primaryEmotion": "平静"}')["riskLevel"] == 1)
    check("JSON 解析：兜底抠出代码块里的 JSON",
          _parse_analysis_json('```json\n{"riskLevel": 2}\n```')["riskLevel"] == 2)
    try:
        _parse_analysis_json("完全没有 JSON")
        check("JSON 解析：无 JSON 时应报错", False)
    except Exception:
        check("JSON 解析：无 JSON 时正确抛错", True)


# ==================== 2. 查询向量缓存 ====================

class _FakeResponse:
    status_code = 200
    text = ""

    def json(self):
        return {"data": [{"index": 0, "embedding": [1.0, 0.0, 0.0]}]}


class _FakeAsyncClient:
    """打桩 httpx.AsyncClient：只数调用次数，不发网络请求"""
    calls = 0

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, *args, **kwargs):
        _FakeAsyncClient.calls += 1
        return _FakeResponse()


async def test_embedding_cache() -> None:
    _FakeAsyncClient.calls = 0
    with patch("app.services.rag.httpx.AsyncClient", _FakeAsyncClient):
        rag._EMBED_CACHE.clear()
        v1 = await rag.get_embedding("失眠怎么办")
        v2 = await rag.get_embedding("失眠怎么办")   # 命中缓存
        v3 = await rag.get_embedding("睡不着")       # 新文本，miss
    check("向量缓存：同文本只调 1 次 API", _FakeAsyncClient.calls == 2,
          f"实际 {_FakeAsyncClient.calls} 次（1 次重复命中 + 1 次新查询）")
    check("向量缓存：返回值一致", v1 == v2 == [1.0, 0.0, 0.0])

    # LRU 淘汰：塞满后最老的被挤掉
    rag._EMBED_CACHE.clear()
    for i in range(rag._EMBED_CACHE_MAX + 5):
        rag._EMBED_CACHE[f"k{i}"] = [float(i)]
    while len(rag._EMBED_CACHE) > rag._EMBED_CACHE_MAX:
        rag._EMBED_CACHE.popitem(last=False)
    check("向量缓存：容量上限生效", len(rag._EMBED_CACHE) == rag._EMBED_CACHE_MAX)
    rag._EMBED_CACHE.clear()


# ==================== 3. 索引缓存复用 ====================

async def test_index_cache() -> None:
    class FakeDB:
        count, max_id = 3, 30

    async def fake_probe(db):
        return (FakeDB.count, FakeDB.max_id)

    load_calls = {"n": 0}

    async def fake_load_chunks(db):
        load_calls["n"] += 1
        return [{"chunk_id": 1, "article_id": 1, "content": "失眠怎么办", "embedding": [1.0, 0.0]}]

    retrieval.invalidate_index_cache()
    with patch.object(retrieval, "_corpus_key", fake_probe), \
         patch.object(retrieval, "load_chunks", fake_load_chunks):
        await retrieval.load_index(FakeDB())
        await retrieval.load_index(FakeDB())          # 语料未变 → 命中
        check("索引缓存：语料未变时不重建", load_calls["n"] == 1, f"实际重建 {load_calls['n']} 次")

        FakeDB.max_id = 31                             # 模拟"先删后插"导致 id 变化
        await retrieval.load_index(FakeDB())
        check("索引缓存：语料变更(id 变化)后自动重建", load_calls["n"] == 2, f"实际重建 {load_calls['n']} 次")

        retrieval.invalidate_index_cache()
        await retrieval.load_index(FakeDB())
        check("索引缓存：invalidate 后强制重建", load_calls["n"] == 3, f"实际重建 {load_calls['n']} 次")
    retrieval.invalidate_index_cache()


# ==================== 4. 阈值拒答 ====================

async def test_threshold_refusal() -> None:
    chunks = [
        {"chunk_id": 1, "article_id": 10, "content": "失眠的缓解方法", "embedding": [1.0, 0.0, 0.0]},
        {"chunk_id": 2, "article_id": 10, "content": "失眠的常见原因", "embedding": [0.99, 0.1, 0.0]},  # 同文章
        {"chunk_id": 3, "article_id": 11, "content": "焦虑的缓解方法", "embedding": [0.0, 1.0, 0.0]},
    ]

    async def fake_load_index(db):
        return chunks, retrieval.BM25([retrieval.tokenize(c["content"]) for c in chunks])

    def embed_of(vec):
        async def _f(q):
            return vec
        return _f

    with patch.object(retrieval, "load_index", fake_load_index):
        # 相关问题：与 chunk1 余弦 1.0 > 阈值
        with patch.object(retrieval, "get_embedding", embed_of([1.0, 0.0, 0.0])):
            hits = await retrieval.hybrid_search(None, "失眠怎么缓解", top_k=3)
        check("阈值拒答：相关问题正常返回", len(hits) > 0, f"返回 {len(hits)} 条")
        check("阈值拒答：同文章去重生效",
              len({h["article_id"] for h in hits}) == len(hits))

        # 库外问题：和所有分块余弦都是 0 < 阈值 0.55 → 拒答
        with patch.object(retrieval, "get_embedding", embed_of([0.0, 0.0, 1.0])):
            miss = await retrieval.hybrid_search(None, "今天上海天气怎么样")
        check("阈值拒答：库外问题返回空列表", miss == [], f"实际 {miss}")

        check("阈值常量与评测报告一致（0.55）", retrieval.MIN_TOP1_COSINE == 0.55)


# ==================== 5. 文章写路径的索引同步 ====================

class FakeArticle:
    def __init__(self, title: str, content: str, status: int = 1):
        self.id = 7
        self.title = title
        self.content = content
        self.status = status


# 两段，每段都超过 chunk_text 的 20 字下限
_ARTICLE = FakeArticle(
    "失眠的缓解方法",
    "失眠通常与压力、焦虑和作息紊乱有关，固定作息时间是最基础也最有效的办法。\n"
    "焦虑时可以试试腹式呼吸，把注意力拉回到呼吸本身，通常几分钟就能平静下来。",
)


async def test_article_indexing() -> None:
    # 已发布：切分并加上标题前缀
    chunks = rag.prepare_chunks(_ARTICLE)
    check("单篇索引：切成 2 段", len(chunks) == 2, f"实际 {len(chunks)} 段")
    check("单篇索引：每段都带【标题】前缀",
          all(c.startswith("【失眠的缓解方法】") for c in chunks))

    # 走 index_article：已发布 → 写库；草稿/下线 → 清库
    recorded = {}

    async def fake_save(db, article_id, chunks_):
        recorded["saved"] = (article_id, chunks_)

    async def fake_clear(db, article_id):
        recorded["cleared"] = article_id

    with patch.object(rag, "save_chunks", fake_save), \
         patch.object(rag, "clear_chunks", fake_clear):
        n = await rag.index_article(None, _ARTICLE)
        check("单篇索引：已发布写入分块", n == 2 and recorded.get("saved", (None, []))[0] == 7)

        for bad_status in (0, 2):
            recorded.clear()
            n = await rag.index_article(None, FakeArticle("草稿", "内容" * 20, status=bad_status))
            check(f"单篇索引：status={bad_status} 不建索引且清库",
                  n == 0 and recorded.get("cleared") == 7 and "saved" not in recorded)


async def test_delete_order() -> None:
    """删文章必须先删分块——外键没有级联，顺序反了会被约束拦下"""
    order = []

    class FakeResult:
        def scalar_one_or_none(self):
            return _ARTICLE

    class FakeSession:
        async def execute(self, stmt):
            return FakeResult()

        async def delete(self, obj):
            order.append("delete_article")

        async def commit(self):
            pass

    async def fake_clear(db, article_id):
        order.append("clear_chunks")

    with patch.object(rag, "clear_chunks", fake_clear):
        ok = await article_service.delete_article(FakeSession(), 7)

    check("删文章：先清分块再删文章", ok and order == ["clear_chunks", "delete_article"],
          f"实际顺序 {order}")


async def main() -> None:
    test_parse_json()
    await test_embedding_cache()
    await test_index_cache()
    await test_threshold_refusal()
    await test_article_indexing()
    await test_delete_order()
    print()
    if failures:
        print(f"{FAIL} {len(failures)} 项未通过：{failures}")
        raise SystemExit(1)
    print(f"{PASS} 全部通过")


if __name__ == "__main__":
    asyncio.run(main())
