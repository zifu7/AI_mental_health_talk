from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.users import User
from app.schemas.common import ResponseModel
from app.schemas.emotion_diary import DiaryCreateRequest, DiaryListItem, DiaryListResponse
from app.services import diary_service
from sqlalchemy import select
# from app.utils.ai_client import analyze_emotion  # 待实现
import json

router = APIRouter(prefix="/emotion-diary", tags=["情绪日记"])

# ---------- 用户端：创建日记 ----------
@router.post("", response_model=ResponseModel)
async def create_diary(
    data: DiaryCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建情绪日记（普通用户）"""
    diary = await diary_service.create_diary(db, current_user.id, data)
    
    # TODO: 异步调用 AI 分析，更新日记的 ai_emotion_analysis 字段
    # 可以在后台任务中执行，避免阻塞响应
    
    return ResponseModel(data={"id": diary.id})

# ---------- 管理端：查询列表 ----------
@router.get("/admin/page", response_model=ResponseModel)
async def get_diary_page(
    userId: Optional[int] = Query(None, alias="userId"),
    moodScoreRange: Optional[str] = Query(None, alias="moodScoreRange"),
    pageNum: int = Query(1, alias="pageNum", ge=1),
    pageSize: int = Query(10, alias="pageSize", ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)  # 仅管理员可访问
):
    """后台管理：分页查询情绪日志（需管理员权限）"""
    if current_user.user_type != 2:
        raise HTTPException(status_code=403, detail="权限不足")
    
    total, diaries = await diary_service.get_diaries(
        db,
        user_id=userId,
        mood_score_range=moodScoreRange,
        page=pageNum,
        size=pageSize
    )
    
    # 组装响应（需要关联用户表获取昵称）
    records = []
    for d in diaries:
        # 查询用户昵称
        stmt = select(User).where(User.id == d.user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        records.append({
            "id": d.id,
            "userId": d.user_id,
            "nickname": user.nickname if user else "",
            "diaryDate": d.diary_date.isoformat(),
            "moodScore": d.mood_score,
            "dominantEmotion": d.dominant_emotion,
            "emotionTriggers": d.emotion_triggers,
            "diaryContent": d.diary_content,
            "sleepQuality": d.sleep_quality,
            "stressLevel": d.stress_level,
            "aiEmotionAnalysis": json.dumps(d.ai_emotion_analysis) if d.ai_emotion_analysis else None,
            "createdAt": d.created_at.isoformat(),
            "updatedAt": d.updated_at.isoformat() if d.updated_at else None
        })
    
    return ResponseModel(data={
        "records": records,
        "total": total
    })

# ---------- 管理端：删除日记 ----------
@router.delete("/admin/{id}", response_model=ResponseModel)
async def delete_diary(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """后台管理：删除情绪日志（需管理员权限）"""
    if current_user.user_type != 2:
        raise HTTPException(status_code=403, detail="权限不足")
    
    deleted = await diary_service.delete_diary(db, id)
    if not deleted:
        raise HTTPException(status_code=404, detail="日记不存在")
    return ResponseModel(data=None)