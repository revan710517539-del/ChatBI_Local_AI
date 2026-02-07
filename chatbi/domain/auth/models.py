"""Auth Domain Models - 纯业务逻辑"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    """用户领域模型"""

    user_id: UUID = Field(default_factory=uuid4)
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password_hash: str  # bcrypt hash
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def verify_password(self, plain_password: str) -> bool:
        """验证密码"""
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(plain_password, self.password_hash)

    @staticmethod
    def hash_password(plain_password: str) -> str:
        """生成密码哈希"""
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(plain_password)


class UserSession(BaseModel):
    """用户会话领域模型（Refresh Token）"""

    session_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    refresh_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.now)

    def is_expired(self) -> bool:
        """检查 Token 是否过期"""
        return datetime.now() > self.expires_at


class TokenPair(BaseModel):
    """Token 对（Access + Refresh）"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(
        default=1800, description="Access Token 有效期（秒）"
    )  # 30分钟
