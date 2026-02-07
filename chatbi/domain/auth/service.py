"""Auth Domain Service - 业务逻辑编排"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt
from loguru import logger

from chatbi.config import config
from chatbi.domain.auth.dtos import CreateUserDTO, UpdateUserDTO
from chatbi.domain.auth.models import TokenPair, User, UserSession
from chatbi.domain.auth.repository import (
    AsyncUserRepository,
    AsyncUserSessionRepository,
)
from chatbi.exceptions import UnauthorizedError, ValidationError


class AuthService:
    """认证服务"""

    def __init__(
        self,
        user_repo: AsyncUserRepository,
        session_repo: AsyncUserSessionRepository,
    ):
        self.user_repo = user_repo
        self.session_repo = session_repo
        self.secret_key = config.jwt.secret_key
        self.algorithm = config.jwt.algorithm
        self.access_token_expire_minutes = config.jwt.access_token_expire_minutes
        self.refresh_token_expire_days = config.jwt.refresh_token_expire_days

    async def login(self, username: str, password: str) -> TokenPair:
        """用户登录"""
        # 1. 查找用户
        user = await self.user_repo.get_by_username(username)
        if not user:
            raise UnauthorizedError("Invalid username or password")

        # 2. 验证密码
        if not user.verify_password(password):
            raise UnauthorizedError("Invalid username or password")

        # 3. 检查用户状态
        if not user.is_active:
            raise UnauthorizedError("User account is disabled")

        # 4. 生成 Token
        token_pair = await self._create_token_pair(user)
        logger.info(f"User {username} logged in successfully")
        return token_pair

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        """刷新 Access Token"""
        # 1. 验证 Refresh Token
        try:
            payload = jwt.decode(
                refresh_token, self.secret_key, algorithms=[self.algorithm]
            )
            user_id_str: str = payload.get("sub")
            if user_id_str is None:
                raise UnauthorizedError("Invalid refresh token")
            user_id = UUID(user_id_str)
        except JWTError as e:
            raise UnauthorizedError(f"Invalid refresh token: {e}")

        # 2. 检查会话是否存在
        session = await self.session_repo.get_by_token(refresh_token)
        if not session:
            raise UnauthorizedError("Refresh token not found")

        # 3. 检查是否过期
        if session.is_expired():
            await self.session_repo.delete_by_token(refresh_token)
            raise UnauthorizedError("Refresh token expired")

        # 4. 获取用户
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")

        # 5. 生成新 Token 对
        new_token_pair = await self._create_token_pair(user)

        # 6. 删除旧 Refresh Token
        await self.session_repo.delete_by_token(refresh_token)

        logger.info(f"User {user.username} refreshed token")
        return new_token_pair

    async def logout(self, refresh_token: str):
        """登出（删除 Refresh Token）"""
        await self.session_repo.delete_by_token(refresh_token)

    async def get_current_user(self, access_token: str) -> User:
        """从 Access Token 获取当前用户"""
        try:
            payload = jwt.decode(
                access_token, self.secret_key, algorithms=[self.algorithm]
            )
            user_id_str: str = payload.get("sub")
            if user_id_str is None:
                raise UnauthorizedError("Invalid access token")
            user_id = UUID(user_id_str)
        except JWTError as e:
            raise UnauthorizedError(f"Invalid access token: {e}")

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")

        return user

    async def create_user(self, dto: CreateUserDTO) -> User:
        """创建用户（仅管理员）"""
        # 1. 检查用户名是否已存在
        existing = await self.user_repo.get_by_username(dto.username)
        if existing:
            raise ValidationError(f"Username {dto.username} already exists")

        # 2. 检查邮箱是否已存在
        existing = await self.user_repo.get_by_email(dto.email)
        if existing:
            raise ValidationError(f"Email {dto.email} already exists")

        # 3. 创建用户
        user = User(
            username=dto.username,
            email=dto.email,
            password_hash=User.hash_password(dto.password),
            is_admin=dto.is_admin,
        )
        created = await self.user_repo.create(user)
        logger.info(f"User {dto.username} created")
        return created

    async def update_user(self, user_id: UUID, dto: UpdateUserDTO) -> User:
        """更新用户（仅管理员或本人）"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValidationError(f"User {user_id} not found")

        # 更新字段
        if dto.email is not None:
            # 检查邮箱是否被占用
            existing = await self.user_repo.get_by_email(dto.email)
            if existing and existing.user_id != user_id:
                raise ValidationError(f"Email {dto.email} already exists")
            user.email = dto.email

        if dto.password is not None:
            user.password_hash = User.hash_password(dto.password)

        if dto.is_active is not None:
            user.is_active = dto.is_active

        if dto.is_admin is not None:
            user.is_admin = dto.is_admin

        updated = await self.user_repo.update(user)
        logger.info(f"User {user.username} updated")
        return updated

    async def delete_user(self, user_id: UUID) -> bool:
        """删除用户（仅管理员）"""
        success = await self.user_repo.delete(user_id)
        if success:
            logger.info(f"User {user_id} deleted")
        return success

    async def _create_token_pair(self, user: User) -> TokenPair:
        """生成 Token 对"""
        # 1. 生成 Access Token
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        access_token = self._create_access_token(
            data={"sub": str(user.user_id), "username": user.username},
            expires_delta=access_token_expires,
        )

        # 2. 生成 Refresh Token
        refresh_token_expires = timedelta(days=self.refresh_token_expire_days)
        refresh_token = self._create_refresh_token(
            data={"sub": str(user.user_id)}, expires_delta=refresh_token_expires
        )

        # 3. 存储 Refresh Token
        session = UserSession(
            user_id=user.user_id,
            refresh_token=refresh_token,
            expires_at=datetime.now() + refresh_token_expires,
        )
        await self.session_repo.create(session)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(access_token_expires.total_seconds()),
        )

    def _create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """生成 Access Token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now() + expires_delta
        else:
            expire = datetime.now() + timedelta(minutes=15)

        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def _create_refresh_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """生成 Refresh Token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now() + expires_delta
        else:
            expire = datetime.now() + timedelta(days=7)

        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
