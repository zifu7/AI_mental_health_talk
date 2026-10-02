"""Agent 引擎冒烟测试（课 2 作业验收）

运行（backend 目录下，需 MySQL 已启动）：
    venv/Scripts/python test_agent.py

三个场景（对照讲义看输出）：
  场景 A  情绪日记工具：问"最近心情"→ 触发 get_mood_summary，回答里有真实统计数字
  场景 B  跨轮记忆：第二轮问"刚才那段时间睡眠差/压力大的天数"→ 小暖记得上一轮在聊什么
  场景 C  知识库工具（做完作业后）：问失眠方法 → 触发 search_knowledge，引用资料内容

脚本会自动：建测试用户（如果库里没人）+ 播种 5 条测试日记（不想要可删 emotion_diaries 表对应行）。
"""
import asyncio
import random
import uuid
from datetime import date, timedelta

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, engine, Base
from app.models.users import User
from app.models.emotion_diary import EmotionDiary
from app.services import chat_service
from app.services.agent import make_agent

EMOTIONS = ["平静", "开心", "焦虑", "低落", "疲惫"]


async def seed(db) -> int:
    """保证有一个测试用户和若干条近几天的心情日记"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    user = (await db.execute(select(User).order_by(User.id).limit(1))).scalar_one_or_none()
    if user is None:
        user = User(
            username=f"agent_test_{uuid.uuid4().hex[:6]}",
            email="agent_test@test.com",
            nickname="测试小号",
            password_hash="test-only",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print(f"[seed] 创建了测试用户 id={user.id}（只能测工具，不能真实登录）")

    recent = (
        await db.execute(
            select(EmotionDiary).where(
                EmotionDiary.user_id == user.id,
                EmotionDiary.diary_date >= date.today() - timedelta(days=10),
            )
        )
    ).scalars().all()
    if len(recent) < 3:
        for i in range(5):
            d = date.today() - timedelta(days=i + 1)
            exists = (
                await db.execute(
                    select(EmotionDiary).where(EmotionDiary.user_id == user.id,
                                               EmotionDiary.diary_date == d)
                )
            ).scalar_one_or_none()
            if exists:
                continue
            db.add(EmotionDiary(
                user_id=user.id,
                diary_date=d,
                mood_score=random.randint(4, 9),
                dominant_emotion=random.choice(EMOTIONS),
                diary_content="测试日记（可删）",
                sleep_quality=random.randint(2, 5),
                stress_level=random.randint(1, 5),
            ))
        await db.commit()
        print("[seed] 播种了 5 条最近的心情日记")
    return user.id


async def turn(db, session_id, agent_chat, text: str, label: str):
    print(f"\n{'='*24}\n{label}｜用户：{text}")
    await chat_service.add_message(db, session_id, 1, text)
    answer = await agent_chat(session_id, text)
    print("[最终回答]", answer[:400])
    await chat_service.add_message(db, session_id, 2, answer)


async def main():
    async with AsyncSessionLocal() as db:
        user_id = await seed(db)
        agent_chat = make_agent(db, user_id)

        # 同一会话连聊两轮：场景 B 依赖第一轮的记录还在库里
        session = await chat_service.create_session(db, user_id, session_title="课2验收-1")
        await turn(db, session.id, agent_chat,
                   "我最近一周的心情怎么样？有什么规律吗？", "场景 A｜日记工具")
        await turn(db, session.id, agent_chat,
                   "那我刚才问的那段时间里，睡眠差和压力大的日子各有几天？", "场景 B｜跨轮记忆")

        # 新会话问知识类问题：注册 search_knowledge 后应触发
        session2 = await chat_service.create_session(db, user_id, session_title="课2验收-2")
        await turn(db, session2.id, agent_chat,
                   "考试前总是失眠怎么办？有什么科学建议？", "场景 C｜知识库（作业）")


if __name__ == "__main__":
    logging_fmt = "%(levelname)s | %(message)s"
    import logging
    logging.basicConfig(level=logging.INFO, format=logging_fmt)
    asyncio.run(main())
