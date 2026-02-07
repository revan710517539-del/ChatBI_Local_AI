"""Auth Domain DTOs - API Request/Response 数据传输对象"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginDTO(BaseModel):
    """登录请求"""

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)


class TokenResponse(BaseModel):
    """Token 响应"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(default=1800, description="Access Token 有效期（秒）")


class UserDTO(BaseModel):
    """用户信息响应"""

    user_id: UUID
    username: str
    email: EmailStr
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime


class CreateUserDTO(BaseModel):
    """创建用户请求"""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    is_admin: bool = False


class UpdateUserDTO(BaseModel):
    """更新用户请求"""

    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6, max_length=100)
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
