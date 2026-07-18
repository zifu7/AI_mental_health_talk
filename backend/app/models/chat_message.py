from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, SmallInteger
from sqlalchemy.sql import func
from app.core.database import Base

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    sender_type = Column(SmallInteger, nullable=False)  # 1=用户, 2=AI
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())