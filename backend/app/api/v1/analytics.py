from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.users import User
from app.schemas.common import ResponseModel
from app.services import analytics_service

router = APIRouter(prefix="/data-analytics", tags=["数据分析"])

@router.get("/overview", response_model=ResponseModel)
async def get_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取仪表盘总览数据（仅管理员）"""
    if current_user.user_type != 2:
        raise HTTPException(status_code=403, detail="权限不足")
    
    data = await analytics_service.get_overview(db)
    return ResponseModel(data=data)