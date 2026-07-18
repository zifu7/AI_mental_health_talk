from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime

# 创建日记请求（前端字段名：驼峰）
class DiaryCreateRequest(BaseModel):
    diary_date: date = Field(..., alias="diaryDate")
    mood_score: int = Field(..., alias="moodScore", ge=1, le=10)
    dominant_emotion: Optional[str] = Field(None, alias="dominantEmotion")
    emotion_triggers: Optional[str] = Field(None, alias="emotionTriggers")
    diary_content: Optional[str] = Field(None, alias="diaryContent")
    sleep_quality: Optional[int] = Field(None, alias="sleepQuality", ge=1, le=5)
    stress_level: Optional[int] = Field(None, alias="stressLevel", ge=1, le=5)

    class Config:
        populate_by_name = True

# 列表查询参数（前端传的是 params，字段名是驼峰，但 FastAPI Query 自动映射）
class DiaryQueryParams(BaseModel):
    user_id: Optional[int] = Field(None, alias="userId")
    mood_score_range: Optional[str] = Field(None, alias="moodScoreRange")
    page_num: int = Field(1, alias="pageNum", ge=1)
    page_size: int = Field(10, alias="pageSize", ge=1, le=100)

    class Config:
        populate_by_name = True

# 列表响应项（前端页面使用的字段名）
class DiaryListItem(BaseModel):
    id: int
    user_id: int = Field(..., alias="userId")
    nickname: Optional[str] = Field(None, alias="nickname")
    diary_date: date = Field(..., alias="diaryDate")
    mood_score: int = Field(..., alias="moodScore")
    dominant_emotion: Optional[str] = Field(None, alias="dominantEmotion")
    emotion_triggers: Optional[str] = Field(None, alias="emotionTriggers")
    diary_content: Optional[str] = Field(None, alias="diaryContent")
    sleep_quality: Optional[int] = Field(None, alias="sleepQuality")
    stress_level: Optional[int] = Field(None, alias="stressLevel")
    ai_emotion_analysis: Optional[str] = Field(None, alias="aiEmotionAnalysis")  # JSON 字符串
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    class Config:
        populate_by_name = True

# 列表响应
class DiaryListResponse(BaseModel):
    records: List[DiaryListItem]
    total: int