"""两轮评测报告对照：v1（标题不入块）vs v2（标题入块）

运行：
    venv/Scripts/python -m eval.compare report_v1_tuned report_v2_title

看三件事：
  1. 总表 delta —— 改动的净效果（Hit@3 / Recall@5 / MRR 各涨跌多少）
  2. 全员失败题 —— 所有策略都没命中的查询，才是"真难题"（不是策略问题，是语料/标注问题）
  3. 单策略差异 —— 哪些查询被改动"救回来"了，哪些被"搞坏了"（有得有失才是真实结论）
"""
import io
import json
import os
import sys
from typing import Any, Dict, List

RESULT_DIR = os.path.join(os.path.dirname(__file__), "results")
KS = (1, 3, 5)
MAX_RANK = 10


def load(tag: str) -> Dict[str, Any]:
    with io.open(os.path.join(RESULT_DIR, f"raw_{tag}.json"), encoding="utf-8") as f:
        return json.load(f)


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def overall(queries: List[Dict]) -> Dict[str, float]:
    return {
        "hit@1": mean([r["hit@1"] for r in queries]),
        "hit@3": mean([r["hit@3"] for r in queries]),
        "hit@5": mean([r["hit@5"] for r in queries]),
        "recall@3": mean([r["recall@3"] for r in queries]),
        "recall@5": mean([r["recall@5"] for r in queries]),
        "mrr": mean([r[f"mrr@{MAX_RANK}"] for r in queries]),
    }


def main() -> None:
    tag_old, tag_new = sys.argv[1], sys.argv[2]
    old, new = load(tag_old), load(tag_new)
    print(f"对照：{tag_old}  →  {tag_new}\n")

    # ---- 1. 总表 delta ----
    print("| 策略 | Hit@3 旧→新 | Recall@5 旧→新 | MRR 旧→新 |")
    print("|---|---|---|---|")
    for name in new:
        o, n = overall(old[name]["queries"]), overall(new[name]["queries"])
        print(
            f"| {name} "
            f"| {o['hit@3']:.3f} → **{n['hit@3']:.3f}** ({n['hit@3'] - o['hit@3']:+.3f}) "
            f"| {o['recall@5']:.3f} → {n['recall@5']:.3f} ({n['recall@5'] - o['recall@5']:+.3f}) "
            f"| {o['mrr']:.3f} → {n['mrr']:.3f} ({n['mrr'] - o['mrr']:+.3f}) |"
        )

    # ---- 2. 全员失败题 ----
    qs = [r["q"] for r in new[next(iter(new))]["queries"]]
    print("\n## 所有策略都没命中的查询（真难题）\n")
    any_miss = False
    for q in qs:
        hits = {}
        for name, data in new.items():
            row = next(r for r in data["queries"] if r["q"] == q)
            if row["type"] == "no_answer":
                continue
            hits[name] = row["hit@3"]
        if hits and all(v == 0 for v in hits.values()):
            any_miss = True
            row = next(r for r in new[next(iter(new))]["queries"] if r["q"] == q)
            print(f"- **[{row['type']}] {q}**")
            print(f"  - 期望：{'、'.join(row['relevant_titles'])}")
            print(f"  - 实际（vector）：{'、'.join(row['top3_titles'])}")
    if not any_miss:
        print("（无：每条查询至少有一个策略命中）")

    # ---- 3. 单策略得失 ----
    print("\n## 生产候选策略的得失（旧 vs 新）\n")
    for name in new:
        gained, lost = [], []
        for o_row, n_row in zip(old[name]["queries"], new[name]["queries"]):
            if o_row["type"] == "no_answer":
                continue
            if o_row["hit@3"] == 0 and n_row["hit@3"] == 1:
                gained.append(n_row["q"])
            if o_row["hit@3"] == 1 and n_row["hit@3"] == 0:
                lost.append(n_row["q"])
        print(f"### {name}")
        print(f"- 救回来 {len(gained)} 条：{'；'.join(gained) if gained else '无'}")
        print(f"- 搞坏了 {len(lost)} 条：{'；'.join(lost) if lost else '无'}\n")

    # ---- 4. 有答案组 top1 余弦分位数（阈值该定在哪） ----
    print("## 有答案组 top1 余弦分位数（看「低分长尾」有多长）\n")
    name = "hybrid_cut_dedup" if "hybrid_cut_dedup" in new else next(iter(new))
    cos = sorted(r["top1_cos"] for r in new[name]["queries"] if r["type"] != "no_answer")
    noa = sorted(r["top1_cos"] for r in new[name]["queries"] if r["type"] == "no_answer")
    for p in (0, 10, 25, 50):
        idx = min(len(cos) - 1, int(len(cos) * p / 100))
        print(f"- 有答案组 P{p}：{cos[idx]:.3f}")
    print(f"- 库外组    最大：{noa[-1]:.3f}  中位：{noa[len(noa) // 2]:.3f}")
    print("\n低分长尾里的查询（余弦 < 0.5 的有答案问题）：")
    for r in new[name]["queries"]:
        if r["type"] != "no_answer" and r["top1_cos"] < 0.5:
            print(f"- [{r['type']}] {r['q']}（top1 余弦 {r['top1_cos']}）")


if __name__ == "__main__":
    main()
