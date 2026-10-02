import os
import logging
from dotenv import load_dotenv
from typing import Optional, List

load_dotenv()  # 加载 .env 文件

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "fallback-secret-key")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    # Embedding（RAG 用）：DeepSeek 官方没有 embedding 接口，用硅基流动的 BGE 系列（免费额度，OpenAI 兼容格式）
    EMBEDDING_API_KEY: str = os.getenv("EMBEDDING_API_KEY", "")
    EMBEDDING_BASE_URL: str = os.getenv("EMBEDDING_BASE_URL", "https://api.siliconflow.cn/v1")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    # CORS 允许的前端地址（逗号分隔）
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000"
    ).split(",")
    # 日志级别
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


def setup_logging(level: str = "INFO") -> None:
    """统一配置项目日志格式和级别"""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-7s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


settings = Settings()