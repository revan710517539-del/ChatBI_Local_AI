"""
Database entity models for chat persistence.

This module contains SQLAlchemy ORM models for persisting chat information
along with domain entity classes that represent the core business objects.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from chatbi.domain.common import EntityMixin, UUIDModel


class ChatSession(UUIDModel):
    """
    Chat session entity representing a conversation thread.
    """

    __tablename__ = "chat_sessions"

    title = Column(String(255), nullable=True)
    user_id = Column(String(100), nullable=False)
    datasource_id = Column(String(36), ForeignKey("datasources.id"), nullable=True)
    context = Column(JSON, nullable=True)  # Session context data
    status = Column(String(20), nullable=False, default="active")  # active, archived
    last_active = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    messages = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )
    datasource = relationship("Datasource", back_populates="chat_sessions")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, title='{self.title}', user_id='{self.user_id}')>"

    def to_domain_model(self) -> "ChatSessionEntity":
        """Convert ORM entity to domain entity."""
        # Create domain model
        return ChatSessionEntity(
            session_id=self.id,
            title=self.title,
            user_id=self.user_id,
            datasource_id=self.datasource_id,
            context=self.context,
            status=self.status,
            last_active=self.last_active,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class ChatMessage(UUIDModel):
    """
    Individual message within a chat session.
    """

    __tablename__ = "chat_messages"

    session_id = Column(
        String(36), ForeignKey("chat_sessions.id"), nullable=False, index=True
    )
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    table_metadata = Column(JSON, nullable=True)  # Additional message metadata

    # For assistant messages
    query_sql = Column(Text, nullable=True)  # Generated SQL
    execution_time = Column(Integer, nullable=True)  # Query execution time in ms

    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    visualizations = relationship(
        "Visualization", back_populates="message", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role='{self.role}', session_id='{self.session_id}')>"

    def to_domain_model(self) -> "ChatMessageEntity":
        """Convert ORM entity to domain entity."""
        return ChatMessageEntity(
            message_id=self.id,
            session_id=self.session_id,
            role=self.role,
            content=self.content,
            timestamp=self.timestamp,
            table_metadata=self.table_metadata,
            query_sql=self.query_sql,
            execution_time=self.execution_time,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class Visualization(UUIDModel):
    """
    Data visualization generated from query results.
    """

    __tablename__ = "visualizations"

    message_id = Column(String(36), ForeignKey("chat_messages.id"), nullable=False)
    chart_type = Column(String(50), nullable=False)  # bar, line, pie, etc.
    chart_config = Column(JSON, nullable=False)  # Chart configuration
    data = Column(JSON, nullable=True)  # Cached chart data
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    # Relationships
    message = relationship("ChatMessage", back_populates="visualizations")

    def __repr__(self):
        return f"<Visualization(id={self.id}, chart_type='{self.chart_type}', message_id='{self.message_id}')>"


class SavedQuery(UUIDModel):
    """
    Saved queries for reuse.
    """

    __tablename__ = "saved_queries"

    user_id = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    question = Column(Text, nullable=False)
    generated_sql = Column(Text, nullable=False)
    visualization_config = Column(JSON, nullable=True)

    def __repr__(self):
        return (
            f"<SavedQuery(id={self.id}, name='{self.name}', user_id='{self.user_id}')>"
        )


class ChatHistory(UUIDModel):
    """
    History of chat interactions and operations for analytics and audit.

    This entity consolidates the functionality from the previous Conversation entity
    and provides a unified history tracking system.
    """

    __tablename__ = "chat_history"

    conversation_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(100), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    question = Column(Text, nullable=True)
    sql = Column(Text, nullable=True)
    row_count = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    model = Column(String(50), nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    usage = Column(JSON, nullable=True)  # Token usage stats
    field_metadata = Column(JSON, nullable=True)  # Additional context info

    def __repr__(self):
        return f"<ChatHistory(id={self.id}, conversation_id='{self.conversation_id}', success={self.success})>"


# Domain entities (pure business objects not tied to ORM)


class ChatSessionEntity(EntityMixin):
    """
    Domain entity representing a chat session.

    This is a pure domain entity that's not tied to the ORM,
    but can be converted to and from the ORM model.
    """

    def __init__(
        self,
        session_id: str,
        user_id: str,
        title: Optional[str] = None,
        datasource_id: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
        status: str = "active",
        last_active: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.session_id = session_id
        self.title = title
        self.user_id = user_id
        self.datasource_id = datasource_id
        self.context = context or {}
        self.status = status
        self.last_active = last_active or datetime.utcnow()
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or self.created_at

    def to_orm_entity(self) -> ChatSession:
        """Convert domain entity to ORM entity."""
        return ChatSession(
            id=self.session_id,
            title=self.title,
            user_id=self.user_id,
            datasource_id=self.datasource_id,
            context=self.context,
            status=self.status,
            last_active=self.last_active,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class ChatMessageEntity(EntityMixin):
    """
    Domain entity representing a chat message.

    This is a pure domain entity that's not tied to the ORM,
    but can be converted to and from the ORM model.
    """

    def __init__(
        self,
        message_id: str,
        session_id: str,
        role: str,
        content: str,
        timestamp: Optional[datetime] = None,
        table_metadata: Optional[dict[str, Any]] = None,
        query_sql: Optional[str] = None,
        execution_time: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.message_id = message_id
        self.session_id = session_id
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.utcnow()
        self.table_metadata = table_metadata or {}
        self.query_sql = query_sql
        self.execution_time = execution_time
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or self.created_at

    def to_orm_entity(self) -> ChatMessage:
        """Convert domain entity to ORM entity."""
        return ChatMessage(
            id=self.message_id,
            session_id=self.session_id,
            role=self.role,
            content=self.content,
            timestamp=self.timestamp,
            table_metadata=self.table_metadata,
            query_sql=self.query_sql,
            execution_time=self.execution_time,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
