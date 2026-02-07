from typing import Any, Dict, Optional

from fastapi import status


class BaseAPIException(Exception):
    """
    Base exception for all API errors with standardized structure
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "server_error"

    def __init__(
        self,
        detail: str = "An unexpected error occurred",
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        headers: Optional[dict[str, Any]] = None,
    ):
        self.detail = detail
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code
        self.headers = headers

    def __str__(self) -> str:
        return f"{self.error_code}: {self.detail}"


class DatabaseError(BaseAPIException):
    """Exception raised for database-related errors"""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "database_error"

    def __init__(self, detail: str = "Database error"):
        super().__init__(detail=detail)


class ValidationError(BaseAPIException):
    """Exception raised for validation errors"""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "validation_error"

    def __init__(self, detail: str = "Validation error"):
        super().__init__(detail=detail)


class NotFoundError(BaseAPIException):
    """Exception raised when a resource is not found"""

    status_code = status.HTTP_404_NOT_FOUND
    error_code = "not_found"

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail=detail)


class UnauthorizedError(BaseAPIException):
    """Exception raised for authentication errors"""

    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "unauthorized"

    def __init__(
        self,
        detail: str = "Authentication required",
        headers: Optional[dict[str, Any]] = None,
    ):
        if headers is None:
            headers = {"WWW-Authenticate": "Bearer"}
        super().__init__(detail=detail, headers=headers)


class ForbiddenError(BaseAPIException):
    """Exception raised for authorization errors"""

    status_code = status.HTTP_403_FORBIDDEN
    error_code = "forbidden"

    def __init__(self, detail: str = "Permission denied"):
        super().__init__(detail=detail)


class RateLimitError(BaseAPIException):
    """Exception raised when rate limit is exceeded"""

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = "rate_limit_exceeded"

    def __init__(
        self,
        detail: str = "Rate limit exceeded",
        headers: Optional[dict[str, Any]] = None,
    ):
        if headers is None:
            headers = {"Retry-After": "60"}
        super().__init__(detail=detail, headers=headers)


class ServiceUnavailableError(BaseAPIException):
    """Exception raised when a service is unavailable"""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "service_unavailable"

    def __init__(
        self,
        detail: str = "Service temporarily unavailable",
        headers: Optional[dict[str, Any]] = None,
    ):
        if headers is None:
            headers = {"Retry-After": "300"}
        super().__init__(detail=detail, headers=headers)


class BadRequestError(BaseAPIException):
    """Exception raised for malformed requests"""

    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "bad_request"

    def __init__(self, detail: str = "Bad request"):
        super().__init__(detail=detail)


class ConflictError(BaseAPIException):
    """Exception raised for resource conflicts"""

    status_code = status.HTTP_409_CONFLICT
    error_code = "conflict"

    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(detail=detail)


class UnprocessableEntityError(BaseAPIException):
    """Exception raised for semantically incorrect requests"""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "unprocessable_entity"

    def __init__(self, detail: str = "Unprocessable entity"):
        super().__init__(detail=detail)


class LLMError(BaseAPIException):
    """Exception raised for LLM-related errors"""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "llm_error"

    def __init__(self, detail: str = "Error with language model"):
        super().__init__(detail=detail)


class ConfigError(BaseAPIException):
    """Exception raised for configuration errors"""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "config_error"

    def __init__(self, detail: str = "Configuration error"):
        super().__init__(detail=detail)
