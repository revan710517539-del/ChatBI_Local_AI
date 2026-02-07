"""
Advanced error handling module for ChatBI API.

This module provides a unified error handling system for the FastAPI application,
ensuring consistent error responses across all endpoints. It includes:

1. Custom exception classes for different error types
2. Exception handlers for built-in and custom exceptions
3. Helper functions for registering all error handlers

Each exception maps to a specific HTTP status code and includes structured error information.
"""

import sys
import traceback
import uuid
from collections.abc import Callable
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from chatbi.middleware.standard_response import StandardResponse


# Base API Error Exception class
class APIError(Exception):
    """Base exception for all API errors with consistent structure."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_SERVER_ERROR",
        details: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        self.headers = headers
        super().__init__(message)


# Specific error classes
class BadRequestError(APIError):
    """400 Bad Request - Invalid request format or parameters."""

    def __init__(
        self,
        message: str = "Invalid request parameters or format",
        error_code: str = "BAD_REQUEST",
        details: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=error_code,
            details=details,
            headers=headers,
        )


class ValidationError(APIError):
    """422 Unprocessable Entity - Request validation failed."""

    def __init__(
        self,
        message: str = "Validation error in request data",
        error_code: str = "VALIDATION_ERROR",
        details: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code=error_code,
            details=details,
            headers=headers,
        )


class AuthenticationError(APIError):
    """401 Unauthorized - Authentication required or failed."""

    def __init__(
        self,
        message: str = "Authentication required",
        error_code: str = "AUTHENTICATION_REQUIRED",
        details: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        _headers = {"WWW-Authenticate": "Bearer"}
        if headers:
            _headers.update(headers)
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=error_code,
            details=details,
            headers=_headers,
        )


class AuthorizationError(APIError):
    """403 Forbidden - Permission denied."""

    def __init__(
        self,
        message: str = "Permission denied",
        error_code: str = "PERMISSION_DENIED",
        details: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code,
            details=details,
            headers=headers,
        )


class NotFoundError(APIError):
    """404 Not Found - Resource not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        error_code: str = "NOT_FOUND",
        details: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=error_code,
            details=details,
            headers=headers,
        )


class ConflictError(APIError):
    """409 Conflict - Resource conflict."""

    def __init__(
        self,
        message: str = "Resource conflict",
        error_code: str = "CONFLICT",
        details: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code=error_code,
            details=details,
            headers=headers,
        )


class RateLimitError(APIError):
    """429 Too Many Requests - Rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        error_code: str = "RATE_LIMIT_EXCEEDED",
        retry_after: int = 60,
        details: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        _headers = {"Retry-After": str(retry_after)}
        if headers:
            _headers.update(headers)

        _details = details or {}
        _details["retry_after_seconds"] = retry_after

        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code=error_code,
            details=_details,
            headers=_headers,
        )


class DatabaseError(APIError):
    """500 Internal Server Error - Database error."""

    def __init__(
        self,
        message: str = "Database error occurred",
        error_code: str = "DATABASE_ERROR",
        details: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code,
            details=details,
            headers=headers,
        )


class ServiceUnavailableError(APIError):
    """503 Service Unavailable - Service temporarily unavailable."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        error_code: str = "SERVICE_UNAVAILABLE",
        retry_after: Optional[int] = None,
        details: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        _headers = {}
        if retry_after is not None:
            _headers["Retry-After"] = str(retry_after)
        if headers:
            _headers.update(headers)

        _details = details or {}
        if retry_after is not None:
            _details["retry_after_seconds"] = retry_after

        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code=error_code,
            details=_details,
            headers=_headers,
        )


class LLMError(APIError):
    """500 Internal Server Error - LLM-specific error."""

    def __init__(
        self,
        message: str = "Language model error occurred",
        error_code: str = "LLM_ERROR",
        details: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code,
            details=details,
            headers=headers,
        )


# Exception handlers
async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle all API errors with standardized format."""
    # Log the error with appropriate level based on status code
    if exc.status_code >= 500:
        logger.error(f"API error {exc.status_code}: {exc.message}")
        if hasattr(exc, "details") and exc.details:
            logger.error(f"Error details: {exc.details}")
    else:
        logger.warning(f"API error {exc.status_code}: {exc.message}")
        if hasattr(exc, "details") and exc.details:
            logger.debug(f"Error details: {exc.details}")

    # Create error response
    errors = [
        {
            "type": exc.error_code,
            "detail": exc.details if hasattr(exc, "details") and exc.details else None,
        }
    ]

    # Create a standard response
    response = StandardResponse(
        status="error",
        message=exc.message,
        errors=errors,
        data=None,
        metadata={
            "error_type": exc.error_code,
            "path": request.url.path,
            "method": request.method,
            "request_id": str(uuid.uuid4()),
        },
    )

    # Return as JSON response with appropriate status code and headers
    return JSONResponse(
        status_code=exc.status_code,
        content=response.dict(),
        headers=exc.headers if hasattr(exc, "headers") and exc.headers else None,
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle Starlette HTTP exceptions."""
    # Map status code to error code
    status_code_mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        406: "NOT_ACCEPTABLE",
        409: "CONFLICT",
        410: "GONE",
        415: "UNSUPPORTED_MEDIA_TYPE",
        422: "UNPROCESSABLE_ENTITY",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
        501: "NOT_IMPLEMENTED",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT",
    }

    error_code = status_code_mapping.get(exc.status_code, "HTTP_ERROR")

    # Log the error
    if exc.status_code >= 500:
        logger.error(f"HTTP exception {exc.status_code}: {exc.detail}")
    else:
        logger.warning(f"HTTP exception {exc.status_code}: {exc.detail}")

    # Create a standard response
    response = StandardResponse(
        status="error",
        message=str(exc.detail),
        errors=[{"type": error_code, "detail": None}],
        data=None,
        metadata={
            "error_type": error_code,
            "path": request.url.path,
            "method": request.method,
            "request_id": str(uuid.uuid4()),
        },
    )

    # Return as JSON response
    return JSONResponse(
        status_code=exc.status_code,
        content=response.dict(),
        headers=exc.headers if hasattr(exc, "headers") else None,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors from Pydantic."""
    # Extract and format validation errors
    error_details = []
    for error in exc.errors():
        error_details.append(
            {
                "field": ".".join([str(loc) for loc in error["loc"]])
                if "loc" in error
                else None,
                "message": error["msg"],
                "type": error["type"],
            }
        )

    # Log the validation errors
    logger.warning(f"Validation error on {request.method} {request.url.path}")
    logger.debug(f"Validation error details: {error_details}")

    # Create a standard response
    response = StandardResponse(
        status="error",
        message="Validation error in request data",
        errors=[{"type": "VALIDATION_ERROR", "detail": error_details}],
        data=None,
        metadata={
            "error_type": "VALIDATION_ERROR",
            "path": request.url.path,
            "method": request.method,
            "request_id": str(uuid.uuid4()),
        },
    )

    # Return as JSON response
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=response.dict()
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle any unhandled exception."""
    # Generate a unique error ID for tracking
    error_id = str(uuid.uuid4())

    # Log the error with full traceback
    logger.error(f"Unhandled exception: {exc}")
    logger.error(f"Error ID: {error_id}")
    logger.debug(traceback.format_exc())

    # In development mode, include traceback in response
    from chatbi.config import get_config

    config = get_config()

    error_detail = None
    if config.env == "development":
        error_detail = {
            "traceback": traceback.format_exc().split("\n"),
            "error_type": exc.__class__.__name__,
        }

    # Create a standard response
    response = StandardResponse(
        status="error",
        message="An unexpected error occurred",
        errors=[{"type": "INTERNAL_SERVER_ERROR", "detail": error_detail}],
        data=None,
        metadata={
            "error_type": "INTERNAL_SERVER_ERROR",
            "error_id": error_id,
            "path": request.url.path,
            "method": request.method,
        },
    )

    # Return as JSON response
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response.dict()
    )


def add_error_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app."""
    # Register custom API error handler
    app.add_exception_handler(APIError, api_error_handler)

    # Register built-in exception handlers
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # Register catch-all exception handler
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("✅ Error handlers registered")


# Helper function to generate custom error response
def generate_error_response(
    error: Union[APIError, Exception], request: Request, include_traceback: bool = False
) -> dict[str, Any]:
    """
    Generate a standardized error response dictionary.

    Args:
        error: The exception that occurred
        request: The FastAPI request object
        include_traceback: Whether to include traceback in the response

    Returns:
        A dictionary with standardized error response format
    """
    if isinstance(error, APIError):
        error_code = error.error_code
        message = error.message
        status_code = error.status_code
        details = error.details if hasattr(error, "details") else None
    else:
        error_code = "INTERNAL_SERVER_ERROR"
        message = str(error) or "An unexpected error occurred"
        status_code = 500
        details = None

    error_response = {
        "status": "error",
        "message": message,
        "error_code": error_code,
        "request_id": str(uuid.uuid4()),
        "path": request.url.path,
        "method": request.method,
    }

    if details:
        error_response["details"] = details

    if include_traceback:
        error_response["traceback"] = traceback.format_exc()

    return error_response
