"""
Base repository pattern implementation for database access.

This module provides a unified repository pattern implementation that supports
both synchronous and asynchronous database operations through a single interface.
"""

import uuid
from abc import ABC
from typing import Any, Generic, List, Optional, Type, TypeVar, Union, cast

from loguru import logger
from sqlalchemy import delete, func, select, update, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from chatbi.exceptions import DatabaseError, NotFoundError

# Generic type for database models
T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """
    Unified base repository for database operations.

    Supports both synchronous and asynchronous operations depending on the
    session type provided during initialization.
    """

    def __init__(self, db: Union[Session, AsyncSession]):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy session (sync or async)
        """
        self.db = db
        self.is_async = isinstance(db, AsyncSession)

        # Get the model class from generic type
        # This requires the specific repository to set model_class
        if not hasattr(self, "model_class"):
            raise TypeError("Repository must define 'model_class' attribute")

    async def _async_get_by_id(self, id_value: Any) -> Optional[T]:
        """Get entity by ID asynchronously."""
        # Handle UUIDs by checking both string format (with hyphens) and hex format
        if isinstance(id_value, uuid.UUID):
            query = select(self.model_class).filter(
                or_(
                    self.model_class.id == str(id_value),
                    self.model_class.id == id_value.hex
                )
            )
        else:
            query = select(self.model_class).filter(self.model_class.id == id_value)
        
        result = await self.db.execute(query)
        return result.scalars().first()

    def _sync_get_by_id(self, id_value: Any) -> Optional[T]:
        """Get entity by ID synchronously."""
        # Handle UUIDs by checking both string format (with hyphens) and hex format
        if isinstance(id_value, uuid.UUID):
            return self.db.query(self.model_class).filter(
                or_(
                    self.model_class.id == str(id_value),
                    self.model_class.id == id_value.hex
                )
            ).first()
        
        return self.db.query(self.model_class).get(id_value)

    async def _async_get_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        """Get all entities with pagination asynchronously."""
        result = await self.db.execute(
            select(self.model_class).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    def _sync_get_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        """Get all entities with pagination synchronously."""
        return self.db.query(self.model_class).offset(skip).limit(limit).all()

    async def _async_count(self) -> int:
        """Count total number of entities asynchronously."""
        result = await self.db.execute(
            select(func.count()).select_from(self.model_class)
        )
        return result.scalar() or 0

    def _sync_count(self) -> int:
        """Count total number of entities synchronously."""
        return self.db.query(func.count(self.model_class.id)).scalar() or 0

    async def _async_create(self, entity: T) -> T:
        """Create new entity asynchronously."""
        try:
            self.db.add(entity)
            await self.db.flush()
            await self.db.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error creating {self.model_class.__name__}: {e}")
            raise DatabaseError(f"Failed to create {self.model_class.__name__}: {e}")

    def _sync_create(self, entity: T) -> T:
        """Create new entity synchronously."""
        try:
            self.db.add(entity)
            self.db.flush()
            self.db.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating {self.model_class.__name__}: {e}")
            raise DatabaseError(f"Failed to create {self.model_class.__name__}: {e}")

    async def _async_update(self, entity: T) -> T:
        """Update existing entity asynchronously."""
        try:
            self.db.add(entity)
            await self.db.flush()
            await self.db.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error updating {self.model_class.__name__}: {e}")
            raise DatabaseError(f"Failed to update {self.model_class.__name__}: {e}")

    def _sync_update(self, entity: T) -> T:
        """Update existing entity synchronously."""
        try:
            self.db.add(entity)
            self.db.flush()
            self.db.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating {self.model_class.__name__}: {e}")
            raise DatabaseError(f"Failed to update {self.model_class.__name__}: {e}")

    async def _async_delete(self, id_value: Any) -> bool:
        """Delete entity by ID asynchronously."""
        try:
            # Pass original id_value to _async_get_by_id so it can handle UUIDs correctly
            entity = await self._async_get_by_id(id_value)
            if entity:
                await self.db.delete(entity)
                await self.db.flush()
                return True
            return False
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error deleting {self.model_class.__name__}: {e}")
            raise DatabaseError(f"Failed to delete {self.model_class.__name__}: {e}")

    def _sync_delete(self, id_value: Any) -> bool:
        """Delete entity by ID synchronously."""
        try:
            # Pass original id_value to _sync_get_by_id so it can handle UUIDs correctly
            entity = self._sync_get_by_id(id_value)
            if entity:
                self.db.delete(entity)
                self.db.flush()
                return True
            return False
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting {self.model_class.__name__}: {e}")
            raise DatabaseError(f"Failed to delete {self.model_class.__name__}: {e}")

    # Public interface methods that automatically dispatch to sync or async implementation

    async def get_by_id(self, id_value: Any) -> Optional[T]:
        """
        Get entity by ID.

        Automatically uses sync or async implementation based on session type.

        Args:
            id_value: Primary key value

        Returns:
            Entity or None if not found
        """
        if self.is_async:
            return await self._async_get_by_id(id_value)
        return self._sync_get_by_id(id_value)

    async def get_by_id_or_error(self, id_value: Any) -> T:
        """
        Get entity by ID or raise NotFoundError.

        Args:
            id_value: Primary key value

        Returns:
            Entity

        Raises:
            NotFoundError: If entity not found
        """
        entity = await self.get_by_id(id_value)
        if entity is None:
            model_name = self.model_class.__name__
            raise NotFoundError(f"{model_name} with ID {id_value} not found")
        return entity

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        """
        Get all entities with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of entities
        """
        if self.is_async:
            return await self._async_get_all(skip, limit)
        return self._sync_get_all(skip, limit)

    async def count(self) -> int:
        """
        Count total number of entities.

        Returns:
            Total count
        """
        if self.is_async:
            return await self._async_count()
        return self._sync_count()

    async def create(self, entity: T) -> T:
        """
        Create new entity.

        Args:
            entity: Entity to create

        Returns:
            Created entity with ID populated
        """
        if self.is_async:
            return await self._async_create(entity)
        return self._sync_create(entity)

    async def update(self, entity: T) -> T:
        """
        Update existing entity.

        Args:
            entity: Entity to update

        Returns:
            Updated entity
        """
        if self.is_async:
            return await self._async_update(entity)
        return self._sync_update(entity)

    async def delete(self, id_value: Any) -> bool:
        """
        Delete entity by ID.

        Args:
            id_value: Primary key value

        Returns:
            True if deleted, False if not found
        """
        if self.is_async:
            return await self._async_delete(id_value)
        return self._sync_delete(id_value)

    # Synchronous versions of methods for convenience in non-async contexts

    def get_by_id_sync(self, id_value: Any) -> Optional[T]:
        """
        Get entity by ID synchronously.

        This is a convenience method for when you need synchronous access
        and are sure you're using a sync session.

        Args:
            id_value: Primary key value

        Returns:
            Entity or None if not found
        """
        if self.is_async:
            raise ValueError("Cannot use sync methods with async session")
        return self._sync_get_by_id(id_value)

    def get_all_sync(self, skip: int = 0, limit: int = 100) -> list[T]:
        """
        Get all entities with pagination synchronously.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of entities
        """
        if self.is_async:
            raise ValueError("Cannot use sync methods with async session")
        return self._sync_get_all(skip, limit)

    def count_sync(self) -> int:
        """
        Count total number of entities synchronously.

        Returns:
            Total count
        """
        if self.is_async:
            raise ValueError("Cannot use sync methods with async session")
        return self._sync_count()

    def create_sync(self, entity: T) -> T:
        """
        Create new entity synchronously.

        Args:
            entity: Entity to create

        Returns:
            Created entity with ID populated
        """
        if self.is_async:
            raise ValueError("Cannot use sync methods with async session")
        return self._sync_create(entity)

    def update_sync(self, entity: T) -> T:
        """
        Update existing entity synchronously.

        Args:
            entity: Entity to update

        Returns:
            Updated entity
        """
        if self.is_async:
            raise ValueError("Cannot use sync methods with async session")
        return self._sync_update(entity)

    def delete_sync(self, id_value: Any) -> bool:
        """
        Delete entity by ID synchronously.

        Args:
            id_value: Primary key value

        Returns:
            True if deleted, False if not found
        """
        if self.is_async:
            raise ValueError("Cannot use sync methods with async session")
        return self._sync_delete(id_value)

    def execute(
        self,
        query: str,
        params: Optional[dict] = None,
        model: Optional[type[T]] = None,
    ) -> list[T]:
        """
        Execute a raw SQL query and return results.

        Args:
            query: SQL query string
            params: Parameters for the query
            model: Optional SQLAlchemy model class for mapping results
        Returns:
            List of results mapped to the specified model
        """
        if self.is_async:
            raise ValueError("Cannot use sync methods with async session")
        try:
            result = self.db.execute(query, params)
            if model:
                return [model(**row) for row in result]
            return result.fetchall()
        except SQLAlchemyError as e:
            logger.error(f"Error executing query: {e}")
            raise DatabaseError(f"Failed to execute query: {e}")


class AsyncBaseRepository(ABC, Generic[T]):
    """
    Base repository for asynchronous database operations.

    Provides standard async CRUD operations for database models.
    """

    # Flag to indicate this repository needs an async session
    uses_async_session = True

    def __init__(self, db: AsyncSession):
        """
        Initialize repository with async database session.

        Args:
            db: AsyncSession
        """
        self.db = db

        # Get the model class from generic type
        # This requires the specific repository to set model_class
        if not hasattr(self, "model_class"):
            raise TypeError("Repository must define 'model_class' attribute")

    async def get_by_id(self, id_value: Any) -> Optional[T]:
        """
        Get entity by ID asynchronously.

        Args:
            id_value: Primary key value

        Returns:
            Entity or None if not found
        """
        result = await self.db.execute(
            select(self.model_class).filter(self.model_class.id == id_value)
        )
        return result.scalars().first()

    async def get_by_id_or_error(self, id_value: Any) -> T:
        """
        Get entity by ID or raise NotFoundError asynchronously.

        Args:
            id_value: Primary key value

        Returns:
            Entity

        Raises:
            NotFoundError: If entity not found
        """
        entity = await self.get_by_id(id_value)
        if entity is None:
            model_name = self.model_class.__name__
            raise NotFoundError(f"{model_name} with ID {id_value} not found")
        return entity

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        """
        Get all entities with pagination asynchronously.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of entities
        """
        result = await self.db.execute(
            select(self.model_class).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        """
        Count total number of entities asynchronously.

        Returns:
            Total count
        """
        result = await self.db.execute(
            select(func.count()).select_from(self.model_class)
        )
        return result.scalar() or 0

    async def create(self, entity: T) -> T:
        """
        Create new entity asynchronously.

        Args:
            entity: Entity to create

        Returns:
            Created entity with ID populated
        """
        try:
            self.db.add(entity)
            await self.db.flush()
            await self.db.refresh(entity)
            return entity
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating {self.model_class.__name__}: {e}")
            raise DatabaseError(f"Failed to create {self.model_class.__name__}: {e}")

    async def update(self, entity: T) -> T:
        """
        Update existing entity asynchronously.

        Args:
            entity: Entity to update

        Returns:
            Updated entity
        """
        try:
            self.db.add(entity)
            await self.db.flush()
            await self.db.refresh(entity)
            return entity
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating {self.model_class.__name__}: {e}")
            raise DatabaseError(f"Failed to update {self.model_class.__name__}: {e}")

    async def delete(self, id_value: Any) -> bool:
        """
        Delete entity by ID asynchronously.

        Args:
            id_value: Primary key value

        Returns:
            True if deleted, False if not found
        """
        try:
            entity = await self.get_by_id(id_value)
            if entity:
                await self.db.delete(entity)
                await self.db.flush()
                return True
            return False
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting {self.model_class.__name__}: {e}")
            raise DatabaseError(f"Failed to delete {self.model_class.__name__}: {e}")
