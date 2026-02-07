"""
Common domain module for shared functionality across domains.

This module contains common schema models and utilities that are reused
across different domain areas.
"""

from chatbi.domain.common.entities import (
    Base,
    BaseModel,
    EntityMixin,
    ModelType,
    UUIDModel,
)
from chatbi.domain.common.schemas import (
    ApiInfoModel,
    ErrorModel,
    ErrorResponse,
    LinkModel,
    MetadataModel,
    MetadataResponse,
    PaginationModel,
    StatusResponse,
    TimeRangeFilter,
    ValidationError,
)

__all__ = [
    # Base entity classes
    "Base",
    "BaseModel",
    "ModelType",
    "UUIDModel",
    "EntityMixin",
    # Schema models
    "ErrorModel",
    "PaginationModel",
    "ApiInfoModel",
    "LinkModel",
    "MetadataModel",
    "TimeRangeFilter",
    "StatusResponse",
    "ValidationError",
    "ErrorResponse",
    "MetadataResponse",
]
