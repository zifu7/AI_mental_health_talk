from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.users import User
from app.core.security import hash_password, verify_password
from app.schemas.user import UserRegister, UserInfo

async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user_data: UserRegister) -> User:
    hashed = hash_password(user_data.password)    # 哈希化密码
    db_user = User(        # 创建 User 对象
        username=user_data.username,
        email=user_data.email,
        nickname=user_data.nickname,
        phone=user_data.phone,
        password_hash=hashed,
        gender=user_data.gender or 0,
        user_type=user_data.user_type or 1
    )
    db.add(db_user)    #添加到数据库   固定写法
    await db.commit()    # 异步提交    固定写法
    await db.refresh(db_user)    # 刷新数据    固定写法
    return db_user    

async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def build_user_info(user: User) -> UserInfo:
    return UserInfo(
        id=user.id,
        username=user.username,
        email=user.email,
        nickname=user.nickname,
        phone=user.phone,
        gender=user.gender,
        user_type=user.user_type
    )