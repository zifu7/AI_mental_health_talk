from sqlalchemy import Column, Integer, Text, ForeignKey, JSON
from app.core.database import Base


class ArticleChunk(Base):
    """文章分块表：一篇文章切成 N 段，每段一行，embedding 直接存 JSON 列

    数据量小（几百个分块），全量加载算余弦相似度就够了，不需要专门的向量数据库。
    等数据量到百万级再考虑 Milvus 之类——面试能讲出这个决策就是加分点。
    """
    __tablename__ = "article_chunks"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("knowledge_articles.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)  # 在文章里的第几段
    content = Column(Text, nullable=False)         # 分块内容
    embedding = Column(JSON, nullable=False)       # 向量（几百个浮点数）
