from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.users import User
from app.schemas.common import ResponseModel
from app.schemas.chat import (
    SessionStartRequest,
    SessionStartResponse,
    SessionItem,
    MessageItem,
    EmotionAnalysisResponse,
    StreamRequest
)
from app.services import chat_service
from app.utils.ai_client import stream_deepseek
import json
from sqlalchemy import select

router = APIRouter(prefix="/psychological-chat", tags=["心理咨询"])


# ---------- 创建会话 ----------
@router.post("/session/start", response_model=ResponseModel)
async def start_session(
    req: SessionStartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新会话并保存初始用户消息
    - 前端传参：{ initialMessage: string, sessionTitle?: string }
    - 返回：{ sessionId: string, status: string }
    """
    session = await chat_service.create_session(
        db,
        user_id=current_user.id,
        session_title=req.session_title
    )
    # 前端期望 sessionId 为字符串
    return ResponseModel(data={
        "sessionId": str(session.id),
        "status": session.status
    })


# ---------- 会话列表 ----------
@router.get("/sessions", response_model=ResponseModel)
async def get_session_list(
    pageNum: int = Query(1, alias="pageNum", ge=1),
    pageSize: int = Query(10, alias="pageSize", ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 管理员：查所有用户；普通用户：只查自己的
    user_id = None if current_user.user_type == 2 else current_user.id
    total, sessions = await chat_service.get_sessions(db, user_id, pageNum, pageSize)
    from app.models.users import User   # 如果顶部没有，加上

    records = []
    for s in sessions:
        # 查用户昵称
        user_stmt = select(User).where(User.id == s.user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        last_msg = await chat_service.get_last_message(db, s.id)
        records.append({
            "id": s.id,
            "userNickname": user.nickname if user else "未知用户",
            "sessionTitle": s.session_title,
            "startedAt": s.started_at.isoformat(),
            "lastMessageContent": last_msg.content if last_msg else "",
            "lastMessageTime": s.last_message_at.isoformat() if s.last_message_at else "",
            "messageCount": s.message_count,
            "durationMinutes": 0
        })
    return ResponseModel(data={
        "records": records,
        "total": total
    })


# ---------- 删除会话 ----------
@router.delete("/sessions/{sessionId}", response_model=ResponseModel)
async def delete_session(
    sessionId: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除指定会话（需验证归属）
    - 路径参数：sessionId (int)
    - 返回：成功状态
    """
    deleted = await chat_service.delete_session(db, sessionId, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="会话不存在或无权删除")
    return ResponseModel(data=None)


# ---------- 获取会话历史消息 ----------
@router.get("/sessions/{sessionId}/messages", response_model=ResponseModel)
async def get_session_messages(
    sessionId: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定会话的所有消息
    """
    # 管理员查看所有用户消息，普通用户只能看自己的
    user_id = None if current_user.user_type == 2 else current_user.id
    messages = await chat_service.get_messages(db, sessionId, user_id)
    result = [
        {
            "id": m.id,
            "senderType": m.sender_type,
            "content": m.content,
            "createdAt": m.created_at.isoformat()
        }
        for m in messages
    ]
    return ResponseModel(data=result)
# ---------- 情绪分析 ----------
@router.get("/session/{sessionId}/emotion", response_model=ResponseModel)
async def get_emotion_analysis(
    sessionId: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = await chat_service.get_session(db, sessionId, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 如果有分析结果，直接返回
    if session.emotion_analysis:
        return ResponseModel(data=session.emotion_analysis)
    
    # 无结果则返回默认
    return ResponseModel(data={
        "primaryEmotion": "中性",
        "emotionScore": 50,
        "isNegative": False,
        "riskLevel": 1,
        "suggestion": "暂无分析结果",
        "improvementSuggestions": [],
        "riskDescription": ""
    })

# ---------- 流式对话 (SSE) ----------
@router.post("/stream")
async def stream_chat(
    req: StreamRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    流式AI对话（Server-Sent Events）
    - 请求体：{ sessionId: int, userMessageText: string }
    - 响应：text/event-stream
    """
    # 验证会话是否存在且属于当前用户
    session = await chat_service.get_session(db, req.session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 保存用户消息
    await chat_service.add_message(db, session.id, sender_type=1, content=req.user_message_text)

    # 返回流式响应
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        stream_deepseek(session.id, req.user_message_text, db),
        media_type="text/event-stream"
    )