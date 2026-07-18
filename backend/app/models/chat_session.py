from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_title = Column(String(100), nullable=True)
    status = Column(String(20), default="ACTIVE")  # ACTIVE, ENDED
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_message_at = Column(DateTime(timezone=True), onupdate=func.now())
    message_count = Column(Integer, default=0)
    duration_minutes = Column(Integer, default=0)  # 可以计算，也可以留空
    emotion_analysis = Column(JSON, nullable=True)