"""RAG 冒烟测试：跑通「文章 → 切分 → 向量化 → 检索」整条链路

运行方式（在 backend 目录下）：
    venv/Scripts/python test_rag.py

如果还没写 chunk_text()，build_index 会报错——先去写它。
"""
import asyncio
import logging

from app.core.database import AsyncSessionLocal, engine, Base
from app.services import rag

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")


async def main():
    # 建表：表只在应用启动时自动创建，脚本直接连库需要手动建一次
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # 1. 重建索引
        total = await rag.build_index(db)
        print(f"✅ 索引构建完成，共 {total} 个分块")

        # 2. 测试检索
        # TODO【你来写】换成你知识库真实相关的问题
        questions = [
            "失眠怎么办",
            "如何缓解考试焦虑",
            "什么是抑郁症",
        ]
        for q in questions:
            results = await rag.search(db, q, top_k=2)
            print(f"\n❓ {q}")
            for r in results:
                print(f"   [{r['score']}] {r['content'][:60]}...")

        # 3. 看拼好的提示词（build_prompt 的输出长什么样）
        prompt = rag.build_prompt(questions[0], await rag.search(db, questions[0], top_k=2))
        print(f"\n========== 拼好的提示词 ==========\n{prompt}")


if __name__ == "__main__":
    asyncio.run(main())
