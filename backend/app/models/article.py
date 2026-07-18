from sqlalchemy import Column, Integer, String, Text, SmallInteger, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Article(Base):
    __tablename__ = "knowledge_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    cover_image = Column(String(255), nullable=True)
    summary = Column(String(1000), nullable=True)
    category_id = Column(Integer, ForeignKey("knowledge_categories.id"),nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(SmallInteger, default=0)  # 0:草稿, 1:已发布, 2:已下线
    read_count = Column(Integer, default=0)
    tags = Column(String(255), nullable=True)  # 逗号分隔
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)

    # 关系（可选）
    category = relationship("Category")
    author = relationship("User")