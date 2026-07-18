from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.category import Category

async def get_category_tree(db: AsyncSession):
    """异步获取分类树（仅一级分类，children 为空）"""
    # 查询 parent_id 为 NULL 的一级分类
    stmt = select(Category).where(Category.parent_id.is_(None))
    result = await db.execute(stmt)
    root_cats = result.scalars().all()

    tree = []
    for cat in root_cats:
        tree.append({
            "value": cat.id,
            "label": cat.category_name,
            "children": []   # 原逻辑中未递归加载子分类
        })
    return tree