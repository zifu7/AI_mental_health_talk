from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    nickname: str = Field(..., min_length=1, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    password: str = Field(..., min_length=6, max_length=100)
    gender: Optional[int] = 0
    user_type: Optional[int] =  Field(1, alias="userType")
    class Config:
       populate_by_name = True  
   
class UserLogin(BaseModel):
    username: str
    password: str

class UserInfo(BaseModel):
    id: int
    username: str
    email: str
    nickname: str
    phone: Optional[str]
    gender: int
    user_type: int

class LoginResponse(BaseModel):
    token: str
    userInfo: UserInfo