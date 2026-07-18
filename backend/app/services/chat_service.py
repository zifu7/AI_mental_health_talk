from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional, List, Tuple
from datetime import datetime
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from sqlalchemy import delete  

# === 会话相关 ===
async def create_session(db: AsyncSession, user_id: int,  session_title: Optional[str] = None) -> ChatSession:
    if not session_title:
        session_title = f"会话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    session = ChatSession(
        user_id=user_id,
        session_title=session_title,
        status="ACTIVE"
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    # 不再保存初始消息，由流式接口负责保存
    return session

async def get_session(db: AsyncSession, session_id: int, user_id: int) -> Optional[ChatSession]:
    """获取单个会话（带用户权限校验）"""
    result =await db.execute(select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)) 
    return result.scalar_one_or_none()

async def get_sessions(
    db: AsyncSession,
    user_id: Optional[int] = None,
    page: int = 1,
    size: int = 10
) -> Tuple[int, List[ChatSession]]:
    stmt = select(ChatSession)
    if user_id is not None:
        stmt = stmt.where(ChatSession.user_id == user_id)
    stmt = stmt.order_by(desc(ChatSession.started_at))
    total_stmt = select(func.count()).where(ChatSession.user_id == user_id)
    total_result = await db.execute(total_stmt)
    total = total_result.scalar()
    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    return total, sessions


async def delete_session(db: AsyncSession, session_id: int, user_id: int) -> bool:
    # 1. 先查出这个会话，确保它属于当前用户
    stmt = select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        return False

    # 2. 手动删除该会话下的所有消息 (先删子表)
    await db.execute(
        delete(ChatMessage).where(ChatMessage.session_id == session_id)
    )

    # 3. 再删除会话本身 (再删父表)
    await db.delete(session)
    
    await db.commit()
    return True

# === 消息相关 ===
async def add_message(db: AsyncSession, session_id: int, sender_type: int, content: str) -> ChatMessage:
    """添加消息并更新会话消息数"""
    msg = ChatMessage(
        session_id=session_id,
        sender_type=sender_type,
        content=content
    )
    db.add(msg)
    # 更新会话消息数
    stmt = select(ChatSession).where(ChatSession.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one()
    session.message_count = session.message_count + 1
    session.last_message_at = datetime.now()
    await db.commit()
    await db.refresh(msg)  # 刷新消息
    await db.refresh(session)  # 刷新会话，确保 message_count 最新
    return msg

async def get_messages(db: AsyncSession, session_id: int, user_id: Optional[int] = None) -> List[ChatMessage]:
    stmt = select(ChatMessage).join(ChatSession).where(ChatMessage.session_id == session_id)
    if user_id is not None:
        stmt = stmt.where(ChatSession.user_id == user_id)
    stmt = stmt.order_by(ChatMessage.created_at)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_last_message(db: AsyncSession, session_id: int) -> Optional[ChatMessage]:
    """获取会话的最后一条消息（用于列表预览）"""
    stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(desc(ChatMessage.created_at)).limit(1)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

# === 情绪分析 ===
async def get_messages_by_session(db: AsyncSession, session_id: int) -> List[ChatMessage]:
    """获取会话所有消息（内部用，不校验用户归属）"""
    stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
    result = await db.execute(stmt)
    return result.scalars().all()

async def update_session_emotion(db: AsyncSession, session_id: int, analysis: dict) -> bool:
    """更新会话的情绪分析结果"""
    stmt = select(ChatSession).where(ChatSession.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        return False
    session.emotion_analysis = analysis
    await db.commit()
    await db.refresh(session)
    return True