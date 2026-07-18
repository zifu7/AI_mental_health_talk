from pydantic import BaseModel,Field
from typing import Optional, List
from datetime import datetime

class ArticleCreate(BaseModel):
    title: str
    content: str
    cover_image: Optional[str] = Field(None, alias="coverImage")  # ← 加 alias
    summary: Optional[str] = None
    category_id: int = Field(alias="categoryId")
    tags: Optional[str] = None
    class Config:
        populate_by_name = True   # ← 加上这行
class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    cover_image: Optional[str] = Field(None, alias="coverImage")  # ← 加上
    summary: Optional[str] = None
    category_id: Optional[int] = Field(None, alias="categoryId")  # ← 加上
    tags: Optional[str] = None

    class Config:
        populate_by_name = True   # ← 加上

class ArticleResponse(BaseModel):
    id: int
    title: str
    content: str
    cover_image: Optional[str] = Field(None, alias="coverImage")          # ← 添加 alias
    summary: Optional[str] = None
    category_id: int
    category_name: Optional[str] = Field(None, alias="categoryName")      # ← 添加 alias
    author_name: Optional[str] = Field(None, alias="authorName")          # ← 添加 alias
    status: int
    read_count: int
    tags: str
    tagArray: Optional[List[str]] = None
    created_at: Optional[datetime] = Field(None, alias="createdAt")       # ← 添加 alias
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")       # ← 添加 alias
    published_at: Optional[datetime] = Field(None, alias="publishedAt")   # ← 添加 alias

    class Config:
        from_attributes = True
        populate_by_name = True   # ← 允许使用原字段名或别名