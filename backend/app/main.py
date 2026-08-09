import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.core.config import settings, setup_logging
from app.core.database import engine, Base
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.diary import router as diary_router
from app.api.v1.analytics import router as analytics_router

# ---- 日志初始化 ----
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """替代 on_event 的 lifespan 写法（FastAPI 推荐）"""
    logger.info("服务启动中...")
    await init_db()
    logger.info("数据库表初始化完成")
    yield
    logger.info("服务关闭")


app = FastAPI(title="心理健康AI助手后端", version="0.1.0", lifespan=lifespan)

# ---- CORS 中间件 ----
# 注意：allow_credentials=True 时不能使用 ["*"]，必须指定具体域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- 全局异常处理 ----
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("未捕获的异常: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"code": "500", "message": "服务器内部错误", "data": None},
    )

# ---- 路由注册 ----
app.include_router(auth_router, prefix="/api")
app.include_router(knowledge_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(diary_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")

# ---- 静态文件 ----
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# ---- 健康检查 ----
@app.get("/")
async def root():
    return {"message": "心理健康AI助手后端运行中"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}