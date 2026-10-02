"""把评测语料写进知识库，并重建全部向量索引

运行（backend 目录下）：
    venv/Scripts/python -m eval.seed_corpus

做的事：
  1. 按标题去重，插入 corpus.py 里的 33 篇文章（status=1 已发布）
  2. 全量重建索引（rag.build_index → chunk_text → 批量向量化 → 存 article_chunks）

可以重复执行：已存在的文章会跳过，索引每次全量重建（保证没有脏数据）。
"""
import asyncio
import sys

from sqlalchemy import select, func

from app.core.database import AsyncSessionLocal, engine, Base
from app.models.article import Article
from app.models.category import Category
from app.models.users import User
from app.services import rag
from eval.corpus import ARTICLES


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # 分类和作者：借库里已有的，没有就用 1（和 seed_test_articles.py 的约定一致）
        category_id = (await db.execute(select(func.min(Category.id)))).scalar() or 1
        author_id = (await db.execute(select(func.min(User.id)))).scalar() or 1

        existing = set(
            (await db.execute(select(Article.title))).scalars().all()
        )
        inserted = 0
        for title, category, content in ARTICLES:
            if title in existing:
                continue
            db.add(Article(
                title=title,
                content=content,
                category_id=category_id,
                author_id=author_id,
                status=1,
                published_at=func.now(),
                tags=category,
            ))
            inserted += 1
        await db.commit()
        print(f"新插入文章 {inserted} 篇（已存在跳过 {len(ARTICLES) - inserted} 篇）")

        published = (await db.execute(
            select(func.count()).select_from(Article).where(Article.status == 1)
        )).scalar()
        print(f"当前已发布文章 {published} 篇，开始重建索引……")

        total = await rag.build_index(db)
        print(f"索引重建完成，共 {total} 个分块")


if __name__ == "__main__":
    asyncio.run(main())
