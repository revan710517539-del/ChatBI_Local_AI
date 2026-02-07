"""
DataSource models and connection management.

This module provides database models for datasource management
and interfaces with the optimized connection system.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from loguru import logger
from pydantic import BaseModel
from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, Relationship, SQLModel

from chatbi.database.drivers.factory import ConnectionPool
from chatbi.domain.datasource import ConnectionInfo, DatabaseType, DataSourceStatus
from chatbi.exceptions import DatabaseError


class DataSource(SQLModel, table=True):
    """
    Database model for datasources
    """

    __tablename__ = "datasources"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    type: DatabaseType = Field(sa_column=Column(Text, nullable=False))
    config: dict[str, Any] = Field(sa_column=Column(JSON), default={})
    status: DataSourceStatus = Field(default=DataSourceStatus.INACTIVE)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(datetime.timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(datetime.timezone.utc)
    )
    last_used_at: Optional[datetime] = Field(default=None)

    # Relationships - a datasource has many queries
    queries: list["QueryHistory"] = Relationship(
        back_populates="datasource",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "lazy": "selectin",
        },
    )

    def get_connection_info(self) -> ConnectionInfo:
        """
        Convert datasource config to ConnectionInfo object.

        Returns:
            ConnectionInfo: Connection parameters
        """
        # Create a ConnectionInfo object from the datasource config
        # This assumes config contains all necessary connection parameters
        connection_info = ConnectionInfo(**self.config)
        return connection_info


class QueryHistory(SQLModel, table=True):
    """
    Database model for query history
    """

    __tablename__ = "query_history"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    datasource_id: UUID = Field(foreign_key="datasources.id", index=True)
    sql: str = Field(sa_column=Column(Text, nullable=False))
    status: str = Field(default="success")  # success, error
    error: Optional[str] = Field(default=None, sa_column=Column(Text))
    duration_ms: int = Field(default=0)
    row_count: int = Field(default=0)
    executed_at: datetime = Field(
        default_factory=lambda: datetime.now(datetime.timezone.utc)
    )
    user_id: Optional[str] = Field(default=None)  # For future user tracking

    # Relationship back to datasource
    datasource: Optional[DataSource] = Relationship(back_populates="queries")


class DataSourceMetrics(BaseModel):
    """
    Metrics for a datasource
    """

    datasource_id: UUID
    query_count: int = 0
    avg_duration_ms: float = 0
    error_rate: float = 0
    last_query_time: Optional[datetime] = None

    class Config:
        orm_mode = True


# Function to help clean up connections when app shuts down
async def cleanup_datasource_connections():
    """
    Clean up all datasource connections.
    Should be called during application shutdown.
    """
    from chatbi.database.drivers.factory import close_all_connections

    try:
        logger.info("Cleaning up all datasource connections")
        await close_all_connections()
    except Exception as e:
        logger.error(f"Error cleaning up datasource connections: {e!s}")


# Function to get connection metrics
def get_datasource_connection_metrics() -> dict[str, Any]:
    """
    Get metrics about datasource connections.

    Returns:
        Dict containing connection metrics
    """
    from chatbi.database.drivers.factory import get_adapter_status

    try:
        return get_adapter_status()
    except Exception as e:
        logger.error(f"Error getting datasource connection metrics: {e!s}")
        return {
            "error": str(e),
            "active_connections": 0,
        }
