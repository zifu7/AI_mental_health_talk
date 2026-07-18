from sqlalchemy import Column, Integer, String, SmallInteger, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

#用户表的定义
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    nickname = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    gender = Column(SmallInteger, default=0)  # 0:未知, 1:男, 2:女
    user_type = Column(SmallInteger, default=1)  # 1:普通用户, 2:管理员
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())