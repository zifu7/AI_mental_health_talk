from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.core.database import get_db          # 需确保 get_db 返回 AsyncSession
from app.core.dependencies import get_current_user
from app.models.users import User
from app.schemas.common import ResponseModel
from app.schemas.article import ArticleCreate, ArticleUpdate, ArticleResponse
from app.schemas.category import CategoryTreeItem
from app.services import category_service, article_service
from app.utils.file_upload import save_upload_file
import os

router = APIRouter(prefix="/knowledge", tags=["知识文章"])

# ---------- 分类 ----------
@router.get("/category/tree", response_model=ResponseModel)
async def get_category_tree(db: AsyncSession = Depends(get_db)):
    tree = await category_service.get_category_tree(db)   # 异步调用
    return ResponseModel(data=tree)


# ---------- 文章 ----------
@router.get("/article/page", response_model=ResponseModel)
async def get_article_page(
    title: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    status: Optional[int] = Query(None),
    currentPage: int = Query(1, alias="currentPage"),
    size: int = Query(10),
    sortField: str = Query("created_at", alias="sortField"),
    sortDirection: str = Query("desc", alias="sortDirection"),
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user)   # 若需要权限可放开
):
    try:
        total, articles = await article_service.get_articles(
            db, title, category_id, status, currentPage, size, sortField, sortDirection
        )
        result = []
        if articles:
            for art in articles:
                # 注意：由于使用了 selectinload，关联对象已加载，可以直接访问
                art_dict = ArticleResponse.model_validate(art).model_dump(by_alias=True)
                art_dict["tagArray"] = art.tags.split(",") if art.tags else []
                art_dict["category_name"] = art.category.category_name if art.category else None
                art_dict["author_name"] = art.author.nickname if art.author else None
                result.append(art_dict)
        return ResponseModel(data={
            "records": result,
            "total": total,
            "current": currentPage,
            "size": size
        })
    except Exception as e:
        # 生产环境建议记录日志，不要直接暴露异常
        import traceback
        traceback.print_exc()
        return ResponseModel(code="500", message=str(e), data=None)


@router.get("/article/{id}", response_model=ResponseModel)
async def get_article_detail(
    id: int,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user)   # 可选
):
    article = await article_service.get_article_by_id(db, id)
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    # 增加阅读量（使用异步提交）
    article.read_count += 1
    await db.commit()   # 异步提交
    await db.refresh(article)
    art_dict = ArticleResponse.model_validate(article).model_dump()
    art_dict["tagArray"] = article.tags.split(",") if article.tags else []
    art_dict["category_name"] = article.category.category_name if article.category else None
    art_dict["author_name"] = article.author.nickname if article.author else None
    return ResponseModel(data=art_dict)


@router.post("/article", response_model=ResponseModel)
async def create_article(
    article_data: ArticleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    #这里可以不写吧？前端已经做了权限控制
    # if current_user.user_type != 2:
    #     raise HTTPException(status_code=403, detail="权限不足")
    new_article = await article_service.create_article(db, article_data, current_user.id)
    return ResponseModel(data={"id": new_article.id})


@router.put("/article/{id}", response_model=ResponseModel)
async def update_article(
    id: int,
    article_data: ArticleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.user_type != 2:
        raise HTTPException(status_code=403, detail="权限不足")
    updated = await article_service.update_article(db, id, article_data)
    if not updated:
        raise HTTPException(status_code=404, detail="文章不存在")
    return ResponseModel(data={"id": updated.id})


@router.put("/article/{id}/status", response_model=ResponseModel)
async def change_article_status(
    id: int,
    status: int = Query(..., description="0草稿,1发布,2下线"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.user_type != 2:
        raise HTTPException(status_code=403, detail="权限不足")
    updated = await article_service.change_article_status(db, id, status)
    if not updated:
        raise HTTPException(status_code=404, detail="文章不存在")
    return ResponseModel(data={"id": updated.id, "status": updated.status})


@router.delete("/article/{id}", response_model=ResponseModel)
async def delete_article(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.user_type != 2:
        raise HTTPException(status_code=403, detail="权限不足")
    deleted = await article_service.delete_article(db, id)
    if not deleted:
        raise HTTPException(status_code=404, detail="文章不存在")
    return ResponseModel(data=None)


# ---------- 文件上传 ----------
@router.post("/file/upload", response_model=ResponseModel)
async def upload_file(
    file: UploadFile = File(...),
    business_type: str = Query(...),
    business_id: str = Query(...),
    business_field: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.user_type != 2:
        raise HTTPException(status_code=403, detail="权限不足")
    # save_upload_file 已经是异步函数
    file_path = await save_upload_file(file, business_type, business_id, business_field)
    return ResponseModel(data={"filePath": file_path})