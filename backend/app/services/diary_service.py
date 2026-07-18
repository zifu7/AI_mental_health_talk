from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from typing import Optional, List, Tuple
from datetime import date
from app.models.emotion_diary import EmotionDiary
from app.models.users import User
from app.schemas.emotion_diary import DiaryCreateRequest
import json

async def create_diary(db: AsyncSession, user_id: int, data: DiaryCreateRequest) -> EmotionDiary:
    """创建情绪日记"""
    diary = EmotionDiary(
        user_id=user_id,
        diary_date=data.diary_date,
        mood_score=data.mood_score,
        dominant_emotion=data.dominant_emotion,
        emotion_triggers=data.emotion_triggers,
        diary_content=data.diary_content,
        sleep_quality=data.sleep_quality,
        stress_level=data.stress_level
    )
    db.add(diary)
    await db.commit()
    await db.refresh(diary)
    return diary

async def get_diaries(
    db: AsyncSession,
    user_id: Optional[int] = None,
    mood_score_range: Optional[str] = None,
    page: int = 1,
    size: int = 10
) -> Tuple[int, List[EmotionDiary]]:
    """获取情绪日记列表（后台管理用）"""
    # 基础查询
    stmt = select(EmotionDiary)
    filters = []

    if user_id is not None:
        filters.append(EmotionDiary.user_id == user_id)

    if mood_score_range:
        # 解析范围如 "1-3" -> 1 <= mood_score <= 3
        parts = mood_score_range.split("-")
        if len(parts) == 2:
            try:
                low, high = int(parts[0]), int(parts[1])
                filters.append(EmotionDiary.mood_score.between(low, high))
            except ValueError:
                pass

    if filters:
        stmt = stmt.where(and_(*filters))

    # 排序（按创建时间倒序）
    stmt = stmt.order_by(desc(EmotionDiary.created_at))

    # 统计总数
    count_stmt = select(func.count()).select_from(EmotionDiary)
    if filters:
        count_stmt = count_stmt.where(and_(*filters))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # 分页
    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return total, items

async def delete_diary(db: AsyncSession, diary_id: int) -> bool:
    """删除情绪日记"""
    stmt = select(EmotionDiary).where(EmotionDiary.id == diary_id)
    result = await db.execute(stmt)
    diary = result.scalar_one_or_none()
    if not diary:
        return False
    await db.delete(diary)
    await db.commit()
    return True

async def update_ai_analysis(db: AsyncSession, diary_id: int, analysis: dict) -> bool:
    """更新日记的AI分析结果"""
    stmt = select(EmotionDiary).where(EmotionDiary.id == diary_id)
    result = await db.execute(stmt)
    diary = result.scalar_one_or_none()
    if not diary:
        return False
    diary.ai_emotion_analysis = analysis
    await db.commit()
    await db.refresh(diary)
    return True