"""Auth Domain Repository - 数据访问层"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from chatbi.domain.auth.entities import UserEntity, UserSessionEntity
from chatbi.domain.auth.models import User, UserSession


class UserRepository:
    """用户仓储（同步）"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, user: User) -> User:
        """创建用户"""
        entity = UserEntity.from_domain(user)
        self.session.add(entity)
        self.session.flush()
        return entity.to_domain()

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """根据 ID 获取用户"""
        entity = self.session.get(UserEntity, user_id)
        return entity.to_domain() if entity else None

    def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        stmt = select(UserEntity).where(UserEntity.username == username)
        entity = self.session.execute(stmt).scalar_one_or_none()
        return entity.to_domain() if entity else None

    def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        stmt = select(UserEntity).where(UserEntity.email == email)
        entity = self.session.execute(stmt).scalar_one_or_none()
        return entity.to_domain() if entity else None

    def update(self, user: User) -> User:
        """更新用户"""
        entity = self.session.get(UserEntity, user.user_id)
        if not entity:
            raise ValueError(f"User {user.user_id} not found")

        entity.username = user.username
        entity.email = user.email
        entity.password_hash = user.password_hash
        entity.is_active = user.is_active
        entity.is_admin = user.is_admin
        entity.updated_at = datetime.now()

        self.session.flush()
        return entity.to_domain()

    def delete(self, user_id: UUID) -> bool:
        """删除用户"""
        entity = self.session.get(UserEntity, user_id)
        if entity:
            self.session.delete(entity)
            return True
        return False


class AsyncUserRepository:
    """用户仓储（异步）"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user: User) -> User:
        """创建用户"""
        entity = UserEntity.from_domain(user)
        self.session.add(entity)
        await self.session.flush()
        return entity.to_domain()

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """根据 ID 获取用户"""
        entity = await self.session.get(UserEntity, user_id)
        return entity.to_domain() if entity else None

    async def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        stmt = select(UserEntity).where(UserEntity.username == username)
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        return entity.to_domain() if entity else None

    async def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        stmt = select(UserEntity).where(UserEntity.email == email)
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        return entity.to_domain() if entity else None

    async def update(self, user: User) -> User:
        """更新用户"""
        entity = await self.session.get(UserEntity, user.user_id)
        if not entity:
            raise ValueError(f"User {user.user_id} not found")

        entity.username = user.username
        entity.email = user.email
        entity.password_hash = user.password_hash
        entity.is_active = user.is_active
        entity.is_admin = user.is_admin
        entity.updated_at = datetime.now()

        await self.session.flush()
        return entity.to_domain()

    async def delete(self, user_id: UUID) -> bool:
        """删除用户"""
        entity = await self.session.get(UserEntity, user_id)
        if entity:
            await self.session.delete(entity)
            return True
        return False


class UserSessionRepository:
    """用户会话仓储（同步）"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, user_session: UserSession) -> UserSession:
        """创建会话"""
        entity = UserSessionEntity.from_domain(user_session)
        self.session.add(entity)
        self.session.flush()
        return entity.to_domain()

    def get_by_token(self, refresh_token: str) -> Optional[UserSession]:
        """根据 Refresh Token 获取会话"""
        stmt = select(UserSessionEntity).where(
            UserSessionEntity.refresh_token == refresh_token
        )
        entity = self.session.execute(stmt).scalar_one_or_none()
        return entity.to_domain() if entity else None

    def delete_by_token(self, refresh_token: str) -> bool:
        """删除会话"""
        stmt = select(UserSessionEntity).where(
            UserSessionEntity.refresh_token == refresh_token
        )
        entity = self.session.execute(stmt).scalar_one_or_none()
        if entity:
            self.session.delete(entity)
            return True
        return False

    def delete_expired(self) -> int:
        """删除过期会话"""
        stmt = select(UserSessionEntity).where(
            UserSessionEntity.expires_at < datetime.now()
        )
        entities = self.session.execute(stmt).scalars().all()
        count = len(entities)
        for entity in entities:
            self.session.delete(entity)
        return count


class AsyncUserSessionRepository:
    """用户会话仓储（异步）"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_session: UserSession) -> UserSession:
        """创建会话"""
        entity = UserSessionEntity.from_domain(user_session)
        self.session.add(entity)
        await self.session.flush()
        return entity.to_domain()

    async def get_by_token(self, refresh_token: str) -> Optional[UserSession]:
        """根据 Refresh Token 获取会话"""
        stmt = select(UserSessionEntity).where(
            UserSessionEntity.refresh_token == refresh_token
        )
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        return entity.to_domain() if entity else None

    async def delete_by_token(self, refresh_token: str) -> bool:
        """删除会话"""
        stmt = select(UserSessionEntity).where(
            UserSessionEntity.refresh_token == refresh_token
        )
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity:
            await self.session.delete(entity)
            return True
        return False

    async def delete_expired(self) -> int:
        """删除过期会话"""
        stmt = select(UserSessionEntity).where(
            UserSessionEntity.expires_at < datetime.now()
        )
        result = await self.session.execute(stmt)
        entities = result.scalars().all()
        count = len(entities)
        for entity in entities:
            await self.session.delete(entity)
        return count
