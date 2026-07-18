from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# 注意：连接串前缀改为 mysql+asyncmy://    创建异步引擎 固定写法
DATABASE_URL = settings.DATABASE_URL.replace("mysql+pymysql", "mysql+asyncmy")

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)
#创建会话工厂，用来操作数据库  固定写法
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

# 异步依赖注入  关键的固定写法  前端一请求就会调用
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session