"""
Database entity models for datasource persistence.

This module contains SQLAlchemy ORM models for persisting datasource information
along with domain entity classes that represent the core business objects.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from chatbi.domain.common import EntityMixin, UUIDModel


class Datasource(UUIDModel):
    """
    Database model for storing datasource connection information.

    Represents a data source configuration that users can connect to for queries.
    """

    __tablename__ = "datasources"

    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(String(500), nullable=True)
    type = Column(String(50), nullable=False, index=True)
    connection_info = Column(JSON, nullable=False)
    status = Column(
        String(20), nullable=False, default="active", server_default=text("'active'")
    )
    is_default = Column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )

    # Metadata
    created_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, server_default=func.now()
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
        onupdate=func.now(),
    )
    last_used_at = Column(DateTime, nullable=True)

    # Relationships
    queries = relationship(
        "QueryHistory", back_populates="datasource", cascade="all, delete-orphan"
    )
    chat_sessions = relationship("ChatSession", back_populates="datasource")

    def __repr__(self) -> str:
        return f"<Datasource(id={self.id}, name='{self.name}', type='{self.type}')>"

    def to_domain_model(self) -> "DataSourceEntity":
        """Convert ORM entity to domain entity."""
        from chatbi.domain.datasource.models import (
            ConnectionDetails,
            DatabaseSchema,
            DataSource,
        )

        # Create domain model
        return DataSourceEntity(
            datasource_id=self.id,
            name=self.name,
            description=self.description,
            type=self.type,
            connection_info=self.connection_info,
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at,
            last_used_at=self.last_used_at,
        )


class QueryHistory(UUIDModel):
    """
    Database model for storing query execution history.

    Keeps track of queries executed against datasources.
    """

    __tablename__ = "query_history"

    datasource_id = Column(String(36), ForeignKey("datasources.id"), nullable=False)
    user_id = Column(String(100), nullable=True)  # Optional: If tracking per user
    sql = Column(String, nullable=False)
    execution_time_ms = Column(Integer, nullable=False)
    row_count = Column(Integer, nullable=False)
    error = Column(String, nullable=True)
    status = Column(
        String(20), nullable=False, default="success", server_default=text("'success'")
    )

    # Execution metadata
    executed_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, server_default=func.now()
    )

    # Relationships
    datasource = relationship("Datasource", back_populates="queries")

    def __repr__(self) -> str:
        return f"<QueryHistory(id={self.id}, datasource_id='{self.datasource_id}')>"


class DataSourceEntity(EntityMixin):
    """
    Domain entity representing a data source configuration.

    This is a pure domain entity that's not tied to the ORM,
    but can be converted to and from the ORM model.
    """

    def __init__(
        self,
        datasource_id: str,
        name: str,
        type: str,
        connection_info: dict[str, Any],
        status: str = "active",
        description: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        last_used_at: Optional[datetime] = None,
    ):
        self.datasource_id = datasource_id
        self.name = name
        self.description = description
        self.type = type
        self.connection_info = connection_info
        self.status = status
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or self.created_at
        self.last_used_at = last_used_at

    def to_orm_entity(self) -> Datasource:
        """Convert domain entity to ORM entity."""
        return Datasource(
            id=self.datasource_id,
            name=self.name,
            description=self.description,
            type=self.type,
            connection_info=self.connection_info,
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at,
            last_used_at=self.last_used_at,
        )
