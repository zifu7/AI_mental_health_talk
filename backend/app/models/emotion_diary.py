from sqlalchemy import Column, Integer, String, Text, SmallInteger, Date, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class EmotionDiary(Base):
    __tablename__ = "emotion_diaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    diary_date = Column(Date, nullable=False)
    mood_score = Column(SmallInteger, nullable=False)  # 1-10
    dominant_emotion = Column(String(50), nullable=True)
    emotion_triggers = Column(Text, nullable=True)
    diary_content = Column(Text, nullable=True)
    sleep_quality = Column(SmallInteger, nullable=True)  # 1-5
    stress_level = Column(SmallInteger, nullable=True)   # 1-5
    ai_emotion_analysis = Column(JSON, nullable=True)    # 存储AI分析结果
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())