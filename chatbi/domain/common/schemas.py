"""
Common schema models for API communication.

This module contains base Pydantic models that are used across different
domains for consistency and reuse in API requests and responses.
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

T = TypeVar("T")


class ErrorModel(BaseModel):
    """Model representing an API error."""

    code: str = Field(..., description="Error code identifier")
    message: str = Field(..., description="Human-readable error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    source: Optional[str] = Field(None, description="Source of the error")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input data",
                "detail": "The field 'email' must be a valid email address",
                "source": "validation",
            }
        }
    )


class PaginationModel(BaseModel):
    """Model for pagination metadata."""

    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page": 1,
                "page_size": 10,
                "total_items": 100,
                "total_pages": 10,
            }
        }
    )


class ApiInfoModel(BaseModel):
    """Model for API metadata information."""

    version: str = Field(..., description="API version")
    response_time_ms: float = Field(..., description="Response time in milliseconds")
    request_id: str = Field(..., description="Unique request identifier")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "version": "1.0.0",
                "response_time_ms": 42.3,
                "request_id": "abcd1234-5678-efgh-9012",
            }
        }
    )


class LinkModel(BaseModel):
    """HATEOAS link model."""

    href: str = Field(..., description="URL for the linked resource")
    rel: Optional[str] = Field(None, description="Link relationship")
    method: Optional[str] = Field(
        "GET", description="HTTP method for accessing the link"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"href": "/api/v1/resources/123", "rel": "self", "method": "GET"}
        }
    )


class MetadataModel(BaseModel):
    """Base metadata model for responses."""

    api: Optional[ApiInfoModel] = Field(None, description="API information")
    pagination: Optional[PaginationModel] = Field(
        None, description="Pagination information"
    )
    links: Optional[dict[str, LinkModel]] = Field(None, description="HATEOAS links")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )
    extras: Optional[dict[str, Any]] = Field(None, description="Additional metadata")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2025-05-16T12:00:00Z",
                "api": {
                    "version": "1.0.0",
                    "response_time_ms": 42.3,
                    "request_id": "abcd1234-5678-efgh-9012",
                },
                "pagination": {
                    "page": 1,
                    "page_size": 10,
                    "total_items": 100,
                    "total_pages": 10,
                },
                "links": {
                    "self": {
                        "href": "/api/v1/resources/123",
                        "rel": "self",
                        "method": "GET",
                    },
                    "next": {
                        "href": "/api/v1/resources?page=2",
                        "rel": "next",
                        "method": "GET",
                    },
                },
            }
        }
    )


class TimeRangeFilter(BaseModel):
    """
    Model for filtering by time range.
    """

    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")


class StatusResponse(BaseModel):
    """
    Simple status response for operations.
    """

    success: bool = Field(True, description="Whether the operation was successful")
    message: str = Field(
        "Operation completed successfully", description="Status message"
    )


class ValidationError(BaseModel):
    """
    Detailed validation error information.
    """

    field: str = Field(..., description="Field with error")
    message: str = Field(..., description="Error message")


class ErrorResponse(BaseModel):
    """
    Standard error response structure.
    """

    success: bool = Field(False, description="Operation failed")
    message: str = Field(..., description="Error message")
    errors: Optional[list[ValidationError]] = Field(
        None, description="Validation errors"
    )


class MetadataResponse(BaseModel, Generic[T]):
    """
    Response with metadata structure.
    """

    data: T = Field(..., description="Response data")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Response metadata"
    )
