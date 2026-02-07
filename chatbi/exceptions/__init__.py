"""
Centralized exception handling for the ChatBI API.

This module defines all custom exceptions used in the application,
ensuring consistent error handling and response format across the API.
"""

from typing import Any, Dict, Optional, Union

from fastapi import HTTPException, status


class BaseAPIException(HTTPException):
    """Base exception class for all API exceptions"""

    def __init__(
        self,
        detail: Union[str, dict[str, Any]],
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: str = "api_error",
        headers: Optional[dict[str, str]] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize the base API exception.

        Args:
            detail: Human-readable error message or dict with details
            status_code: HTTP status code
            error_code: Machine-readable error code for client handling
            headers: Optional response headers
            details: Optional additional error details
        """
        self.error_code = error_code
        self.details = details
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class DatabaseError(BaseAPIException):
    """Exception raised for database-related errors"""

    def __init__(
        self,
        detail: str = "Database operation failed",
        error_code: str = "db_error",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code,
            details=details,
        )


class ValidationError(BaseAPIException):
    """Exception raised for data validation errors"""

    def __init__(
        self,
        detail: str = "Validation error",
        error_code: str = "validation_error",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code=error_code,
            details=details,
        )


class NotFoundError(BaseAPIException):
    """Exception raised when a requested resource is not found"""

    def __init__(
        self,
        detail: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="not_found",
            details=details if details else None,
        )


class UnauthorizedError(BaseAPIException):
    """Exception raised for authentication failures"""

    def __init__(
        self,
        detail: str = "Authentication required",
        error_code: str = "unauthorized",
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=error_code,
            headers={"WWW-Authenticate": "ApiKeyHeader"},
        )


class ForbiddenError(BaseAPIException):
    """Exception raised for authorization failures"""

    def __init__(
        self,
        detail: str = "Permission denied",
        error_code: str = "forbidden",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code,
            details=details,
        )


class RateLimitError(BaseAPIException):
    """Exception raised when rate limit is exceeded"""

    def __init__(
        self,
        detail: str = "Too many requests",
        retry_after: int = 60,
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="rate_limit_exceeded",
            headers={"Retry-After": str(retry_after)},
            details={"retry_after_seconds": retry_after},
        )


class ServiceUnavailableError(BaseAPIException):
    """Exception raised when a required service is unavailable"""

    def __init__(
        self,
        detail: str = "Service temporarily unavailable",
        service_name: Optional[str] = None,
    ):
        details = {"service": service_name} if service_name else None

        super().__init__(
            detail=detail,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="service_unavailable",
            details=details,
        )


class BadRequestError(BaseAPIException):
    """Exception raised for invalid request data"""

    def __init__(
        self,
        detail: str = "Invalid request",
        error_code: str = "bad_request",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=error_code,
            details=details,
        )


class ConflictError(BaseAPIException):
    """Exception raised for resource conflicts"""

    def __init__(
        self,
        detail: str = "Resource conflict",
        error_code: str = "conflict",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_409_CONFLICT,
            error_code=error_code,
            details=details,
        )


class UnprocessableEntityError(BaseAPIException):
    """Exception raised when request is semantically invalid"""

    def __init__(
        self,
        detail: str = "Unprocessable entity",
        error_code: str = "unprocessable_entity",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code=error_code,
            details=details,
        )


class LLMError(BaseAPIException):
    """Exception raised for Language Model errors"""

    def __init__(
        self,
        detail: str = "Language Model error",
        error_code: str = "llm_error",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code,
            details=details,
        )


class ConfigError(BaseAPIException):
    """Exception raised for configuration errors"""

    def __init__(
        self,
        detail: str = "Configuration error",
        error_code: str = "config_error",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code,
            details=details,
        )
