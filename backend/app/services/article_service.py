from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from typing import Optional, Tuple, List
from datetime import datetime
from app.models.article import Article
from app.models.users import User
from app.models.category import Category
from app.schemas.article import ArticleCreate, ArticleUpdate
from app.services import rag
from app.services.retrieval import invalidate_index_cache

# 会进入检索索引的字段：标题以【】前缀形式参与检索，正文切分成块。
# 改这两个之外的字段（封面、摘要、分类、标签）不影响切分结果，不必重建索引。
INDEXED_FIELDS = {"title", "content"}


async def get_articles(
    db: AsyncSession,
    title: Optional[str] = None,
    category_id: Optional[int] = None,
    status: Optional[int] = None,
    page: int = 1,
    size: int = 10,
    sort_field: str = "created_at",
    sort_direction: str = "desc"
) -> Tuple[int, List[Article]]:
    """异步获取文章列表（使用 selectinload 加载关联）"""
    stmt = select(Article).options(
        selectinload(Article.author),
        selectinload(Article.category)
    )

    # 过滤条件
    filters = []
    if title:
        filters.append(Article.title.contains(title))
    if category_id is not None:
        filters.append(Article.category_id == category_id)
    if status is not None:
        filters.append(Article.status == status)
    if filters:
        stmt = stmt.where(and_(*filters))

    # 排序
    if hasattr(Article, sort_field):
        order_column = getattr(Article, sort_field)
    else:
        order_column = Article.created_at
    if sort_direction.lower() == "asc":
        stmt = stmt.order_by(order_column.asc())
    else:
        stmt = stmt.order_by(order_column.desc())

    # 统计总数
    count_stmt = select(func.count()).select_from(Article)
    if filters:
        count_stmt = count_stmt.where(and_(*filters))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # 分页
    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return total, items


async def get_article_by_id(db: AsyncSession, article_id: int):
    stmt = select(Article).where(Article.id == article_id).options(
        selectinload(Article.author),
        selectinload(Article.category)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_article(
    db: AsyncSession,
    article_data: ArticleCreate,
    author_id: int
) -> Article:
    """异步创建文章（默认状态为草稿）"""
    db_article = Article(
        title=article_data.title,
        content=article_data.content,
        cover_image=article_data.cover_image,
        summary=article_data.summary,
        category_id=article_data.category_id,
        author_id=author_id,
        tags=article_data.tags,
        status=0  # 草稿
    )
    db.add(db_article)
    await db.commit()
    await db.refresh(db_article)
    # 刷新后重新加载关联（可选，但后续返回时可能不需要，也可以再查询一次）
    return db_article


async def update_article(
    db: AsyncSession,
    article_id: int,
    article_data: ArticleUpdate
) -> Optional[Article]:
    """异步更新文章（只更新传入的字段）"""
    stmt = select(Article).where(Article.id == article_id)
    result = await db.execute(stmt)
    db_article = result.scalar_one_or_none()
    if not db_article:
        return None

    update_data = article_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_article, key, value)

    await db.commit()
    await db.refresh(db_article)

    # 改了标题或正文才重建索引：否则改个封面也要重跑一遍向量化，白花 embedding 额度
    if INDEXED_FIELDS & update_data.keys():
        await rag.index_article(db, db_article)
        invalidate_index_cache()
    return db_article


async def change_article_status(
    db: AsyncSession,
    article_id: int,
    status: int
) -> Optional[Article]:
    """异步更改文章状态（0草稿,1发布,2下线）"""
    stmt = select(Article).where(Article.id == article_id)
    result = await db.execute(stmt)
    db_article = result.scalar_one_or_none()
    if not db_article:
        return None

    db_article.status = status
    if status == 1:  # 发布时记录发布时间
        db_article.published_at = datetime.now()
    await db.commit()
    await db.refresh(db_article)

    # 发布 → 建索引；下线/退回草稿 → 清掉分块。
    # 下线必须真的清干净：否则"已下线"的文章还会被检索到并作为引用发给模型。
    await rag.index_article(db, db_article)
    invalidate_index_cache()
    return db_article


async def delete_article(db: AsyncSession, article_id: int) -> bool:
    """异步删除文章"""
    stmt = select(Article).where(Article.id == article_id)
    result = await db.execute(stmt)
    db_article = result.scalar_one_or_none()
    if not db_article:
        return False
    # 顺序有讲究：必须先删分块再删文章。article_chunks.article_id 有外键指向文章
    # 且未配级联删除，反过来做会被外键约束拦下。
    await rag.clear_chunks(db, article_id)
    await db.delete(db_article)
    await db.commit()
    invalidate_index_cache()
    return True