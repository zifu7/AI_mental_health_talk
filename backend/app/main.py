import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.database import engine, Base
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.auth import router as auth_router   # 导入认证路由
from app.api.v1.chat import router as chat_router
from app.api.v1.diary import router as diary_router
from app.api.v1.analytics import router as analytics_router

app = FastAPI(title="心理健康AI助手后端", version="0.1.0")

# CORS 中间件（功能：允许前端跨域）  固定写法
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由（knowledge.py 内部已有 prefix="/knowledge"，不要再重复加）
app.include_router(auth_router, prefix="/api")
app.include_router(knowledge_router, prefix="/api")
app.include_router(chat_router,prefix="/api")
app.include_router(diary_router,prefix="/api")
app.include_router(analytics_router,prefix="/api")

# 挂载静态文件目录（用于访问上传的图片）
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

#固定套路，启动服务器时根据数据库模型创建表
@app.on_event("startup")
async def startup():
    await init_db()


#测试地址
@app.get("/")
async def root():
    return {"message": "心理健康AI助手后端运行中"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}