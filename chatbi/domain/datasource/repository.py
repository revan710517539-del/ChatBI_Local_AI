"""
Repository for datasource operations.

This module provides a repository implementation for datasource operations,
abstracting database access for datasource management.
"""

from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
from datetime import datetime

from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, select

from chatbi.domain.datasource.entities import Datasource, QueryHistory
from chatbi.domain.common.repository import AsyncBaseRepository, BaseRepository
from chatbi.exceptions import BadRequestError, DatabaseError, NotFoundError


class DatasourceRepository(BaseRepository[Datasource]):
    """Repository for datasource operations."""

    model_class = Datasource

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        type_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> list[Datasource]:
        """
        Get all datasources with filtering and pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            type_filter: Optional filter by datasource type
            status_filter: Optional filter by datasource status

        Returns:
            List of datasources that match the filters
        """
        # Use appropriate query method based on session type
        if self.is_async:
            # Build async query with filters
            query = select(self.model_class)
            if type_filter:
                query = query.where(self.model_class.type == type_filter)
            if status_filter:
                query = query.where(self.model_class.status == status_filter)

            # Apply pagination
            query = query.offset(skip).limit(limit)

            # Execute query and get results
            result = await self.db.execute(query)
            return list(result.scalars().all())
        else:
            # Build sync query with filters using SQLAlchemy 1.0 style
            query = self.db.query(self.model_class)
            if type_filter:
                query = query.filter(self.model_class.type == type_filter)
            if status_filter:
                query = query.filter(self.model_class.status == status_filter)

            # Apply pagination and return results
            return query.offset(skip).limit(limit).all()

    async def count(
        self, type_filter: Optional[str] = None, status_filter: Optional[str] = None
    ) -> int:
        """
        Count total number of datasources with optional filtering.

        Args:
            type_filter: Optional filter by datasource type
            status_filter: Optional filter by datasource status

        Returns:
            Total count of matching datasources
        """
        if self.is_async:
            # Build async query with filters
            query = select(func.count()).select_from(self.model_class)
            if type_filter:
                query = query.where(self.model_class.type == type_filter)
            if status_filter:
                query = query.where(self.model_class.status == status_filter)

            # Execute query and get count
            result = await self.db.execute(query)
            return result.scalar() or 0
        else:
            # Build sync query with filters
            query = self.db.query(func.count(self.model_class.id))
            if type_filter:
                query = query.filter(self.model_class.type == type_filter)
            if status_filter:
                query = query.filter(self.model_class.status == status_filter)

            return query.scalar() or 0

    async def get_by_name(self, name: str) -> Optional[Datasource]:
        """
        Get a datasource by name.

        Args:
            name: Name of the datasource

        Returns:
            Datasource if found, None otherwise
        """
        if self.is_async:
            query = select(self.model_class).where(self.model_class.name == name)
            result = await self.db.execute(query)
            return result.scalars().first()
        else:
            return self.db.query(self.model_class).filter(self.model_class.name == name).first()

    async def update_datasource_last_used(self, datasource_id: str) -> bool:
        """
        Update the last_used_at timestamp for a datasource.

        Args:
            datasource_id: ID of the datasource to update

        Returns:
            True if successful, False if datasource not found
        """
        datasource = await self.get_by_id(datasource_id)
        if not datasource:
            return False

        datasource.last_used_at = datetime.utcnow()
        if self.is_async:
            await self.db.flush()
        else:
            self.db.flush()
        return True

    async def create_query_history(self, query_data: dict[str, Any]) -> QueryHistory:
        """
        Create a new query history record.

        Args:
            query_data: Query history data dictionary

        Returns:
            New QueryHistory entity
        """
        try:
            query_history = QueryHistory(**query_data)
            self.db.add(query_history)

            if self.is_async:
                await self.db.flush()
            else:
                self.db.flush()

            return query_history
        except SQLAlchemyError as e:
            logger.error(f"Error creating query history: {e}")
            if self.is_async:
                await self.db.rollback()
            else:
                self.db.rollback()
            raise DatabaseError(f"Failed to create query history: {e}")

    # The methods below are kept for backwards compatibility

    def get_all_datasources(self) -> list[Datasource]:
        """
        Get all datasources.

        Returns:
            List of all datasources
        """
        if self.is_async:
            raise ValueError("Cannot use sync method with async session")
        return self.db.query(self.model_class).all()

    def get_datasource_by_id(self, datasource_id: str) -> Optional[Datasource]:
        """
        Get datasource by ID.

        Args:
            datasource_id: Datasource ID

        Returns:
            Datasource or None if not found
        """
        if self.is_async:
            raise ValueError("Cannot use sync method with async session")
        return (
            self.db.query(self.model_class)
            .filter(self.model_class.id == datasource_id)
            .first()
        )

    async def create_datasource(self, datasource_data: dict[str, Any]) -> Datasource:
        """
        Create a new datasource.

        Args:
            datasource_data: Datasource data dictionary

        Returns:
            New datasource

        Raises:
            SQLAlchemyError: If creation fails
        """
        try:
            # Generate ID if not provided
            if "id" not in datasource_data:
                datasource_data["id"] = str(uuid4())

            # Create new datasource entity
            datasource = self.model_class(**datasource_data)
            
            # Use BaseRepository's create method which handles sync/async
            return await self.create(datasource)
        except SQLAlchemyError as e:
            logger.error(f"Error creating datasource: {e}")
            raise

    def update_datasource(
        self, datasource_id: str, datasource_data: dict[str, Any]
    ) -> Optional[Datasource]:
        """
        Update an existing datasource.

        Args:
            datasource_id: Datasource ID
            datasource_data: Updated datasource data

        Returns:
            Updated datasource or None if not found
        """
        datasource = self.get_datasource_by_id(datasource_id)
        if not datasource:
            return None

        # Update fields
        for key, value in datasource_data.items():
            if hasattr(datasource, key):
                setattr(datasource, key, value)

        self.db.flush()
        return datasource

    def delete_datasource(self, datasource_id: str) -> bool:
        """
        Delete a datasource.

        Args:
            datasource_id: Datasource ID

        Returns:
            True if successful, False if not found
        """
        datasource = self.get_datasource_by_id(datasource_id)
        if not datasource:
            return False

        self.db.delete(datasource)
        self.db.flush()
        return True

    def test_connection(self, connection_params: dict[str, Any]) -> bool:
        """
        Test database connection.

        Args:
            connection_params: Connection parameters

        Returns:
            True if connection successful
        """
        # This is a placeholder. In a real implementation,
        # we would use a connection manager to test the connection.
        from chatbi.database.connection_manager import ConnectionManager

        return ConnectionManager.test_connection(**connection_params)
