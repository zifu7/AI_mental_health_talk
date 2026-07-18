from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.user import UserRegister, UserLogin, LoginResponse
from app.schemas.common import ResponseModel
from app.services import user_service
from app.core.security import create_access_token

router = APIRouter(prefix="/user", tags=["用户认证"])

@router.post("/add", response_model=ResponseModel)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    existing_user = await user_service.get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被使用"
        )
    existing_email = await user_service.get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    new_user = await user_service.create_user(db, user_data)
    user_info = user_service.build_user_info(new_user)   # 同步方法，无需 await
    return ResponseModel(data=user_info.dict())

@router.post("/login", response_model=ResponseModel)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    try:
        user = await user_service.authenticate_user(db, login_data.username, login_data.password)
        if not user:
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        token = create_access_token(data={"sub": str(user.id), "user_type": user.user_type})
        user_info = user_service.build_user_info(user)
        login_resp = LoginResponse(token=token, userInfo=user_info)
        return ResponseModel(data=login_resp.dict())
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ResponseModel(code="500", message=str(e), data=None)
@router.post("/logout", response_model=ResponseModel)
async def logout():
    return ResponseModel(message="退出登录成功")