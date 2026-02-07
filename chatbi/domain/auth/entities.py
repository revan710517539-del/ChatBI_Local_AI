"""Auth Domain Entities - SQLAlchemy ORM 模型"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from chatbi.domain.auth.models import User as DomainUser
from chatbi.domain.auth.models import UserSession as DomainUserSession
from chatbi.domain.common.entities import Base


class UserEntity(Base):
    """用户表"""

    __tablename__ = "app_users"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    def to_domain(self) -> DomainUser:
        """转换为领域模型"""
        return DomainUser(
            user_id=self.id,
            username=self.username,
            email=self.email,
            password_hash=self.password_hash,
            is_active=self.is_active,
            is_admin=self.is_admin,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @staticmethod
    def from_domain(user: DomainUser) -> "UserEntity":
        """从领域模型创建"""
        return UserEntity(
            id=user.user_id,
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


class UserSessionEntity(Base):
    """用户会话表（JWT Refresh Token）"""

    __tablename__ = "user_sessions"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    refresh_token: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def to_domain(self) -> DomainUserSession:
        """转换为领域模型"""
        return DomainUserSession(
            session_id=self.id,
            user_id=self.user_id,
            refresh_token=self.refresh_token,
            expires_at=self.expires_at,
            created_at=self.created_at,
        )

    @staticmethod
    def from_domain(session: DomainUserSession) -> "UserSessionEntity":
        """从领域模型创建"""
        return UserSessionEntity(
            id=session.session_id,
            user_id=session.user_id,
            refresh_token=session.refresh_token,
            expires_at=session.expires_at,
            created_at=session.created_at,
        )
