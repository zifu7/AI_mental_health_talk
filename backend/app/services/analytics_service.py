from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import datetime, timedelta, date
from typing import List, Dict, Any
from app.models.users import User
from app.models.emotion_diary import EmotionDiary
from app.models.chat_session import ChatSession

async def get_overview(db: AsyncSession) -> Dict[str, Any]:
    """获取仪表盘总览数据"""
    # 1. 系统总览
    total_users = await db.execute(select(func.count()).select_from(User))
    total_users = total_users.scalar()

    # 活跃用户：今天有活动的用户（有日记或会话）
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    active_users_stmt = (
        select(func.count(func.distinct(EmotionDiary.user_id)))
        .select_from(EmotionDiary)
        .where(EmotionDiary.created_at.between(today_start, today_end))
    )
    active_diary_users = await db.execute(active_users_stmt)
    active_diary_users = active_diary_users.scalar()

    # 会话活跃用户
    active_session_users_stmt = (
        select(func.count(func.distinct(ChatSession.user_id)))
        .select_from(ChatSession)
        .where(ChatSession.started_at.between(today_start, today_end))
    )
    active_session_users = await db.execute(active_session_users_stmt)
    active_session_users = active_session_users.scalar()

    # 总日记数
    total_diaries = await db.execute(select(func.count()).select_from(EmotionDiary))
    total_diaries = total_diaries.scalar()

    # 今日新增日记
    new_diaries_stmt = select(func.count()).where(EmotionDiary.created_at.between(today_start, today_end))
    new_diaries = await db.execute(new_diaries_stmt)
    new_diaries = new_diaries.scalar()

    # 总会话数
    total_sessions = await db.execute(select(func.count()).select_from(ChatSession))
    total_sessions = total_sessions.scalar()

    # 今日新增会话
    new_sessions_stmt = select(func.count()).where(ChatSession.started_at.between(today_start, today_end))
    new_sessions = await db.execute(new_sessions_stmt)
    new_sessions = new_sessions.scalar()

    # 平均情绪得分（所有日记的平均）
    avg_mood = await db.execute(select(func.avg(EmotionDiary.mood_score)))
    avg_mood = avg_mood.scalar() or 0

    overview = {
        "totalUsers": total_users,
        "activeUsers": max(active_diary_users, active_session_users),
        "totalDiaries": total_diaries,
        "totalNewDiaries": new_diaries,
        "totalSessions": total_sessions,
        "totalNewSessions": new_sessions,
        "avgMoodScore": round(avg_mood, 1)
    }

    # 2. 情绪趋势（最近7天）
    emotion_trend = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        avg = await db.execute(
            select(func.avg(EmotionDiary.mood_score))
            .where(EmotionDiary.created_at.between(day_start, day_end))
        )
        avg_score = avg.scalar() or 0
        count = await db.execute(
            select(func.count())
            .where(EmotionDiary.created_at.between(day_start, day_end))
        )
        record_count = count.scalar()
        emotion_trend.append({
            "date": day.isoformat(),
            "avgMoodScore": round(avg_score, 1),
            "recordCount": record_count
        })

    # 3. 咨询会话统计
    total_sessions = await db.execute(select(func.count()).select_from(ChatSession))
    total_sessions = total_sessions.scalar()
    # 平均时长（简化，暂时不计算）
    avg_duration = 0

    # 每日趋势（最近7天）
    daily_trend = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        session_count = await db.execute(
            select(func.count())
            .where(ChatSession.started_at.between(day_start, day_end))
        )
        session_count = session_count.scalar()
        user_count = await db.execute(
            select(func.count(func.distinct(ChatSession.user_id)))
            .where(ChatSession.started_at.between(day_start, day_end))
        )
        user_count = user_count.scalar()
        daily_trend.append({
            "date": day.isoformat(),
            "sessionCount": session_count,
            "userCount": user_count
        })

    consultation_stats = {
        "totalSessions": total_sessions,
        "avgDurationMinutes": avg_duration,
        "dailyTrend": daily_trend
    }

    # 4. 用户活跃趋势（最近7天）
    user_activity = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())

        # 活跃用户（有日记或会话）
        diary_users = await db.execute(
            select(func.count(func.distinct(EmotionDiary.user_id)))
            .where(EmotionDiary.created_at.between(day_start, day_end))
        )
        diary_users = diary_users.scalar()
        session_users = await db.execute(
            select(func.count(func.distinct(ChatSession.user_id)))
            .where(ChatSession.started_at.between(day_start, day_end))
        )
        session_users = session_users.scalar()
        active_users = max(diary_users, session_users)

        # 新增用户（注册日期为当天）
        new_users = await db.execute(
            select(func.count())
            .where(User.created_at.between(day_start, day_end))
        )
        new_users = new_users.scalar()

        user_activity.append({
            "date": day.isoformat(),
            "activeUsers": active_users,
            "newUsers": new_users,
            "diaryUsers": diary_users,
            "consultationUsers": session_users
        })

    return {
        "systemOverview": overview,
        "emotionTrend": emotion_trend,
        "consultationStats": consultation_stats,
        "userActivity": user_activity
    }