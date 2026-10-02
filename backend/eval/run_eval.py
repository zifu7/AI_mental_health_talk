"""RAG 检索评测：在固定语料上跑同一套问题，横向对比五种检索策略

运行（backend 目录下，先跑 eval.seed_corpus 建好语料）：
    venv/Scripts/python -m eval.run_eval

指标口径（全部按【文章】级算，不是分块级）：
    Hit@k     top-k 里有没有命中任何一篇相关文章（0/1）——最宽松的"有没有找着"
    Recall@k  top-k 覆盖了几成相关文章（multi 类才有区分度）——"找全了没有"
    MRR@10    第一篇相关文章排在第几位的倒数——"排得靠不靠前"

对照实验的纪律：
  1. 语料、切块、查询向量全部固定，一次只变"排序策略"这一个变量；
  2. 查询向量只算一次，五个策略共用（否则 API 抖动能解释掉策略差异）；
  3. 查询向量带磁盘缓存，调参时可以反复跑不改动结果。
"""
import asyncio
import io
import json
import os
import sys
import time
from typing import Any, Callable, Dict, List, Tuple

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.article import Article
from app.services.rag import cosine_similarity, get_embedding
from app.services.retrieval import (
    BM25,
    bm25_rank,
    dedupe_by_article,
    hybrid_rank,
    hybrid_rank_cut,
    hybrid_rerank,
    load_chunks,
    tokenize,
    vector_rank,
)
from eval.golden import QUERIES, TYPES

RESULT_DIR = os.path.join(os.path.dirname(__file__), "results")
CACHE_PATH = os.path.join(RESULT_DIR, "query_vec_cache.json")
# 版本标签：每次"改进"都留一份独立报告，才能做前后对比
#     venv/Scripts/python -m eval.run_eval v1_基线
TAG = sys.argv[1] if len(sys.argv) > 1 else "latest"
# 生产候选策略：阈值扫描以它为准（跑完第一轮再根据结果改这个常量）
PRODUCTION = "hybrid_cut_dedup"
KS = (1, 3, 5)
MAX_RANK = 10          # MRR 截断位

# 五种策略：前三种是"纯策略"，第四个是调过 RRF 权重的，最后一个是生产用的（带文章去重）
STRATEGIES: Dict[str, Callable[[str, List[float], List[Dict], BM25], List[Tuple[int, float]]]] = {
    "vector": lambda q, qv, chunks, bm25: vector_rank(qv, chunks),
    "bm25": lambda q, qv, chunks, bm25: bm25_rank(q, chunks, bm25),
    "hybrid": lambda q, qv, chunks, bm25: hybrid_rank(q, qv, chunks, bm25),
    "hybrid_w2": lambda q, qv, chunks, bm25: hybrid_rank(q, qv, chunks, bm25, weights=(2.0, 1.0)),
    "hybrid_rerank": lambda q, qv, chunks, bm25: hybrid_rerank(q, qv, chunks, bm25),
    "hybrid_w3": lambda q, qv, chunks, bm25: hybrid_rank(q, qv, chunks, bm25, weights=(3.0, 1.0)),
    "hybrid_cut": lambda q, qv, chunks, bm25: hybrid_rank_cut(q, qv, chunks, bm25),
    "hybrid_cut_dedup": lambda q, qv, chunks, bm25: dedupe_by_article(
        hybrid_rank_cut(q, qv, chunks, bm25), chunks
    ),
}


# ==================== 查询向量缓存（省钱 + 保证可复现） ====================

def load_vec_cache() -> Dict[str, List[float]]:
    if os.path.exists(CACHE_PATH):
        with io.open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_vec_cache(cache: Dict[str, List[float]]) -> None:
    os.makedirs(RESULT_DIR, exist_ok=True)
    with io.open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f)


# ==================== 指标 ====================

def eval_ranking(
    ranking: List[Tuple[int, float]],
    chunks: List[Dict],
    relevant_articles: set,
) -> Dict[str, float]:
    """给一条查询的排序结果打分"""
    ranked_articles = [chunks[idx]["article_id"] for idx, _ in ranking[:MAX_RANK]]
    result: Dict[str, float] = {}

    for k in KS:
        top = ranked_articles[:k]
        result[f"hit@{k}"] = 1.0 if any(a in relevant_articles for a in top) else 0.0
        result[f"recall@{k}"] = (
            len({a for a in top if a in relevant_articles}) / len(relevant_articles)
            if relevant_articles else 0.0
        )

    mrr = 0.0
    for rank, article_id in enumerate(ranked_articles, start=1):
        if article_id in relevant_articles:
            mrr = 1.0 / rank
            break
    result[f"mrr@{MAX_RANK}"] = mrr
    return result


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


# ==================== 主流程 ====================

async def main() -> None:
    async with AsyncSessionLocal() as db:
        chunks = await load_chunks(db)
        rows = (await db.execute(select(Article.id, Article.title))).all()
        title_to_id = {title: aid for aid, title in rows}

    print(f"语料：{len(title_to_id)} 篇文章，{len(chunks)} 个分块")

    # 标签校验：标题写错必须当场报错，否则所有策略一起"变差"，排查方向全错
    missing = []
    for item in QUERIES:
        for title in item["relevant"]:
            if title not in title_to_id:
                missing.append((item["q"], title))
    if missing:
        print("❌ 评测集里的标题在数据库里找不到，请先修正 golden.py：")
        for q, title in missing:
            print(f"   - 查询「{q}」引用了不存在的文章：{title}")
        return

    cache = load_vec_cache()
    bm25 = BM25([tokenize(c["content"]) for c in chunks])
    id_to_title = {aid: title for aid, title in rows}

    # 每条查询：向量只算一次，五个策略共用
    query_vecs: Dict[str, List[float]] = {}
    for item in QUERIES:
        q = item["q"]
        if q not in cache:
            cache[q] = await get_embedding(q)
        query_vecs[q] = cache[q]
    save_vec_cache(cache)

    # 跑评测
    per_strategy: Dict[str, Dict[str, Any]] = {}
    for name, fn in STRATEGIES.items():
        rows_out = []
        for item in QUERIES:
            q = item["q"]
            relevant_ids = {title_to_id[t] for t in item["relevant"]}
            t0 = time.perf_counter()
            ranking = fn(q, query_vecs[q], chunks, bm25)
            cost_ms = (time.perf_counter() - t0) * 1000

            metrics = eval_ranking(ranking, chunks, relevant_ids)
            top1_idx = ranking[0][0] if ranking else None
            top1_cos = (
                cosine_similarity(query_vecs[q], chunks[top1_idx]["embedding"])
                if top1_idx is not None else 0.0
            )
            rows_out.append({
                "q": q,
                "type": item["type"],
                "relevant_titles": item["relevant"],
                "top3_titles": [id_to_title.get(chunks[idx]["article_id"], "?") for idx, _ in ranking[:3]],
                "top1_cos": round(top1_cos, 4),
                "cost_ms": round(cost_ms, 2),
                **metrics,
            })
        per_strategy[name] = {"queries": rows_out}

    write_report(per_strategy)
    save_json(per_strategy)


# ==================== 报告输出 ====================

def write_report(per_strategy: Dict[str, Dict[str, Any]]) -> None:
    os.makedirs(RESULT_DIR, exist_ok=True)
    lines: List[str] = []
    add = lines.append

    add("# RAG 检索评测报告\n")
    add(f"查询数：{len(QUERIES)}　策略数：{len(per_strategy)}\n")

    # ---- 总表 ----
    header = "| 策略 | Hit@1 | Hit@3 | Hit@5 | Recall@3 | Recall@5 | MRR@10 | 平均耗时 |"
    add("## 总指标（全部查询）\n")
    add(header)
    add("|---|---|---|---|---|---|---|---|")
    for name, data in per_strategy.items():
        qs = data["queries"]
        add(
            f"| {name} "
            f"| {mean([r['hit@1'] for r in qs]):.3f} "
            f"| {mean([r['hit@3'] for r in qs]):.3f} "
            f"| {mean([r['hit@5'] for r in qs]):.3f} "
            f"| {mean([r['recall@3'] for r in qs]):.3f} "
            f"| {mean([r['recall@5'] for r in qs]):.3f} "
            f"| {mean([r[f'mrr@{MAX_RANK}'] for r in qs]):.3f} "
            f"| {mean([r['cost_ms'] for r in qs]):.1f} ms |"
        )

    # ---- 分类型（只看有答案的四类） ----
    answerable_types = [t for t in TYPES if t != "no_answer"]
    add("\n## 分类型 Hit@3 / Recall@3（no_answer 类不适用）\n")
    add("| 类型 | 条数 | " + " | ".join(per_strategy.keys()) + " |")
    add("|---|---|" + "---|" * len(per_strategy))
    for t in answerable_types:
        cells = []
        n = 0
        for name, data in per_strategy.items():
            qs = [r for r in data["queries"] if r["type"] == t]
            n = len(qs)
            cells.append(f"{mean([r['hit@3'] for r in qs]):.2f} / {mean([r['recall@3'] for r in qs]):.2f}")
        add(f"| {t} | {n} | " + " | ".join(cells) + " |")

    # ---- 无答案问题：阈值能不能拦住 ----
    add("\n## 库外问题（no_answer）：top1 余弦分布与阈值扫描\n")
    add("| 策略 | 有答案组 top1 余弦(均值/最小) | 库外组 top1 余弦(均值/最大) |")
    add("|---|---|---|")
    for name, data in per_strategy.items():
        qs = data["queries"]
        ans = [r["top1_cos"] for r in qs if r["type"] != "no_answer"]
        noa = [r["top1_cos"] for r in qs if r["type"] == "no_answer"]
        add(f"| {name} | {mean(ans):.3f} / {min(ans):.3f} | {mean(noa):.3f} / {max(noa):.3f} |")

    add(f"\n阈值扫描（取生产候选 {PRODUCTION}）：放行率 = 有答案问题中 top1 余弦 ≥ τ 的比例（越高越好）；"
        "误召率 = 库外问题中 top1 余弦 ≥ τ 的比例（越低越好）\n")
    add("| τ | 放行率 | 误召率 |")
    add("|---|---|---|")
    qs = per_strategy[PRODUCTION]["queries"]
    ans = [r["top1_cos"] for r in qs if r["type"] != "no_answer"]
    noa = [r["top1_cos"] for r in qs if r["type"] == "no_answer"]
    for tau in (0.40, 0.45, 0.50, 0.55, 0.60):
        add(f"| {tau:.2f} | {mean([1.0 if s >= tau else 0.0 for s in ans]):.2f} "
            f"| {mean([1.0 if s >= tau else 0.0 for s in noa]):.2f} |")

    # ---- 失败案例（定性分析的材料） ----
    add("\n## 失败案例（Hit@3 未命中，按策略列）\n")
    for name, data in per_strategy.items():
        fails = [r for r in data["queries"] if r["type"] != "no_answer" and r["hit@3"] == 0]
        add(f"\n### {name}（{len(fails)} 条未命中）\n")
        if not fails:
            add("全部命中 ✅")
            continue
        for r in fails:
            add(f"- **[{r['type']}] {r['q']}**")
            add(f"  - 期望：{'、'.join(r['relevant_titles'])}")
            add(f"  - 实际 top3：{'、'.join(r['top3_titles'])}（top1 余弦 {r['top1_cos']}）")

    report = "\n".join(lines)
    with io.open(os.path.join(RESULT_DIR, f"report_{TAG}.md"), "w", encoding="utf-8") as f:
        f.write(report)
    print(report)


def save_json(per_strategy: Dict[str, Dict[str, Any]]) -> None:
    os.makedirs(RESULT_DIR, exist_ok=True)
    with io.open(os.path.join(RESULT_DIR, f"raw_{TAG}.json"), "w", encoding="utf-8") as f:
        json.dump(per_strategy, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
