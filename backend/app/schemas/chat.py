from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# 创建会话请求
class SessionStartRequest(BaseModel):
    initial_message: str = Field(..., alias="initialMessage")
    session_title: Optional[str] = Field(None, alias="sessionTitle")

    class Config:
        populate_by_name = True

# 创建会话响应
class SessionStartResponse(BaseModel):
    session_id: str = Field(..., alias="sessionId")
    status: str

    class Config:
        populate_by_name = True

# 会话列表项（响应）
class SessionItem(BaseModel):
    id: int
    session_title: str = Field(..., alias="sessionTitle")
    started_at: datetime = Field(..., alias="startedAt")
    last_message_content: Optional[str] = Field(None, alias="lastMessageContent")
    message_count: int = Field(..., alias="messageCount")
    duration_minutes: int = Field(..., alias="durationMinutes")

    class Config:
        populate_by_name = True

# 会话列表响应（分页）
class SessionListResponse(BaseModel):
    records: List[SessionItem]
    total: int

# 消息项
class MessageItem(BaseModel):
    id: int
    sender_type: int = Field(..., alias="senderType")
    content: str
    created_at: datetime = Field(..., alias="createdAt")

    class Config:
        populate_by_name = True

# 情绪分析响应
class EmotionAnalysisResponse(BaseModel):
    primary_emotion: str = Field(..., alias="primaryEmotion")
    emotion_score: int = Field(..., alias="emotionScore")
    is_negative: bool = Field(..., alias="isNegative")
    risk_level: int = Field(..., alias="riskLevel")
    suggestion: str
    improvement_suggestions: List[str] = Field(..., alias="improvementSuggestions")
    risk_description: str = Field(..., alias="riskDescription")

    class Config:
        populate_by_name = True

# 流式对话请求
class StreamRequest(BaseModel):
    session_id: str = Field(..., alias="sessionId")
    user_message_text: str = Field(..., alias="userMessageText")

    class Config:
        populate_by_name = True