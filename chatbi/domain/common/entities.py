"""
Base entity models for database persistence.

This module contains base entity classes that provide common functionality
for database persistence across all domains.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Type, TypeVar

from sqlalchemy import Column, DateTime, MetaData, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

"""
Base models and utilities for database ORM models.

This module defines base classes and common utilities for database models.
It provides a common foundation for all ORM models in the application.
"""

# Define a common naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Create metadata with naming convention
metadata = MetaData(naming_convention=convention)

# Create a base class for models
Base = declarative_base(metadata=metadata)
ModelType = TypeVar("ModelType", bound=Base)


class BaseModel(Base):
    """
    Abstract base model with common attributes for all database models.
    """

    __abstract__ = True

    def to_dict(self) -> dict[str, Any]:
        """
        Convert model instance to dictionary.

        Returns:
            Dictionary representation of model
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            result[column.name] = value
        return result

    @classmethod
    def from_dict(cls: type[ModelType], data: dict[str, Any]) -> ModelType:
        """
        Create model instance from dictionary.

        Args:
            data: Dictionary containing model attributes

        Returns:
            New model instance
        """
        return cls(
            **{k: v for k, v in data.items() if k in cls.__table__.columns.keys()}
        )


class UUIDModel(BaseModel):
    """
    Base model with UUID primary key and timestamp fields.

    This provides a common base for all entity models requiring UUID as primary key
    along with creation and modification timestamps.
    """

    __abstract__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class EntityMixin:
    """
    Mixin providing common entity functionality for domain entities.

    This class can be used by both ORM and non-ORM domain entities
    to provide a consistent interface.
    """

    def to_dict(self) -> dict[str, Any]:
        """Convert entity to dictionary representation."""
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        """Create entity from dictionary data."""
        return cls(**{k: v for k, v in data.items() if not k.startswith("_")})
