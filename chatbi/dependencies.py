"""
Dependency injection system for ChatBI.

This module provides centralized dependency management for FastAPI routes,
improving reusability, testability, and separation of concerns.
"""

import functools
import inspect
import os
import threading
from collections.abc import Callable
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Annotated, Any, AsyncGenerator, Dict, Generic, Optional, Type, TypeVar, Union, cast

from fastapi import Depends, Header, HTTPException, Request, Security, status
from fastapi.security.api_key import APIKeyHeader
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

# Generic type for database repositories
T = TypeVar("T")
R = TypeVar("R")  # Return type for functions

# Track if we're in a transaction - used by transactional decorator
_in_transaction: ContextVar[bool] = ContextVar("in_transaction", default=False)

# Get database instances
from chatbi.database import get_async_session, get_db_session

# Session types
PostgresSessionDep = Annotated[Session, Depends(get_db_session)]
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]

# Initialize config
from chatbi.config import get_config

config = get_config()

# API key security scheme (deprecated - use JWT instead)
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# JWT security scheme
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

oauth2_scheme = HTTPBearer(auto_error=False)

# ContextVar to track active transaction for transaction boundary control
active_transaction = ContextVar("active_transaction", default=None)


class RepositoryDependency(Generic[T]):
    """
    Generic dependency provider for repository classes.

    Automatically handles injecting the appropriate session type
    based on current context and route requirements.

    Usage:
        MyRepoDep = RepositoryDependency(MyRepository)

        @router.get("/items")
        async def get_items(repo: MyRepository = Depends(MyRepoDep)):
            return await repo.get_all()
    """

    def __init__(self, repo_class: type[T], use_async_session: bool = True):
        """
        Initialize with the repository class.

        Args:
            repo_class: Repository class to create
            use_async_session: Force using async session even if route is not async
        """
        self.repo_class = repo_class
        self.use_async_session = use_async_session

    async def __call__(self) -> AsyncGenerator[T, None]:
        """
        Create repository instance with appropriate session.

        This method is now async by default, which works in both async and sync routes.
        FastAPI handles this correctly.

        Returns:
            Repository instance
        """
        if self.use_async_session:
            # Keep session lifecycle bounded to each request to prevent pool leaks.
            async with get_async_session() as session:
                yield self.repo_class(session)
            return

        # Otherwise use sync session by default for better compatibility.
        from chatbi.database.database import SyncSessionLocal

        sync_session = SyncSessionLocal()
        try:
            yield self.repo_class(sync_session)
        finally:
            sync_session.close()


def transactional(func: Callable[..., R]) -> Callable[..., R]:
    """
    Decorator for transaction management.

    Ensures that database operations are committed on success and
    rolled back on error. Also prevents nested transaction issues.

    Usage:
        @router.post("/items")
        @transactional
        def create_item(data: ItemCreate, db: PostgresSessionDep):
            # db operations here
            # No need to commit - decorator handles it
    """
    is_async = inspect.iscoroutinefunction(func)

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> R:
        """Wrapper for synchronous functions."""
        # Check if we're already in a transaction
        if _in_transaction.get():
            # Just call the function without transaction handling
            return func(*args, **kwargs)

        # Set transaction context
        token = _in_transaction.set(True)

        try:
            # Execute the function
            result = func(*args, **kwargs)

            # Try to find a session parameter
            session = _find_session_in_args(args, kwargs)
            if session:
                session.commit()

            return result

        except Exception as e:
            # Try to find a session parameter
            session = _find_session_in_args(args, kwargs)
            if session:
                session.rollback()
                logger.debug(f"Transaction rolled back due to: {e!s}")

            # Re-raise the exception
            raise

        finally:
            # Reset the transaction context
            _in_transaction.reset(token)

    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> R:
        """Wrapper for asynchronous functions."""
        # Check if we're already in a transaction
        if _in_transaction.get():
            # Just call the function without transaction handling
            return await func(*args, **kwargs)

        # Set transaction context
        token = _in_transaction.set(True)

        try:
            # Execute the function
            result = await func(*args, **kwargs)

            # Try to find a session parameter
            session = _find_session_in_args(args, kwargs)
            if session:
                if isinstance(session, AsyncSession):
                    await session.commit()
                else:
                    session.commit()

            return result

        except Exception as e:
            # Try to find a session parameter
            session = _find_session_in_args(args, kwargs)
            if session:
                if isinstance(session, AsyncSession):
                    await session.rollback()
                else:
                    session.rollback()
                logger.debug(f"Transaction rolled back due to: {e!s}")

            # Re-raise the exception
            raise

        finally:
            # Reset the transaction context
            _in_transaction.reset(token)

    # Return the appropriate wrapper based on function type
    return async_wrapper if is_async else sync_wrapper


def _find_session_in_args(
    args: tuple, kwargs: dict
) -> Optional[Union[Session, AsyncSession]]:
    """
    Find a database session in function arguments or keyword arguments.

    Args:
        args: Function positional arguments
        kwargs: Function keyword arguments

    Returns:
        Session or AsyncSession if found, None otherwise
    """
    # First check kwargs
    for arg_value in kwargs.values():
        if isinstance(arg_value, (Session, AsyncSession)):
            return arg_value
        # Check if argument is a repository with .db attribute
        if hasattr(arg_value, "db") and isinstance(arg_value.db, (Session, AsyncSession)):
            return arg_value.db

    # Then check positional args
    for arg_value in args:
        if isinstance(arg_value, (Session, AsyncSession)):
            return arg_value
        # Check if argument is a repository with .db attribute
        if hasattr(arg_value, "db") and isinstance(arg_value.db, (Session, AsyncSession)):
            return arg_value.db

    return None


# Cache dependencies


def get_cache_client() -> Any:
    """
    Get cache client dependency.

    Returns:
        Cache client instance
    """
    from chatbi.cache import get_cache_client as _get_client

    return _get_client()


# Authentication dependencies


async def verify_api_key(
    api_key: str = Security(api_key_header),
) -> str:
    """
    Verify the API key and return the associated user or client ID.

    Args:
        api_key: API key from request header

    Returns:
        str: User or client ID associated with the API key

    Raises:
        UnauthorizedError: If API key is missing or invalid
    """
    if config.env == "development" and not config.api.require_auth:
        return "dev-user"  # Skip auth in development mode if not required

    if api_key is None:
        raise UnauthorizedError("Missing API key")

    # In production, check API key against secure storage
    # For development, allow a simple comparison
    if config.env == "production":
        # TODO: Implement proper API key validation against database
        valid_api_key = os.getenv("API_KEY", "test-api-key")
        if api_key != valid_api_key:
            logger.warning(f"Invalid API key attempted: {api_key[:5]}...")
            raise UnauthorizedError("Invalid API key")
    elif api_key != "test-api-key":
        raise UnauthorizedError("Invalid API key")

    # Here you could look up the user/client ID associated with this API key
    # For now, we'll return a fixed value
    return "default-user"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> "User":
    """
    Get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token credentials
        session: Async database session

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If token is missing or invalid
    """
    from chatbi.domain.auth.models import User
    from chatbi.domain.auth.repository import AsyncUserRepository
    from chatbi.domain.auth.service import AuthService
    from chatbi.domain.auth.repository import AsyncUserSessionRepository
    
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = credentials.credentials
    
    try:
        # 创建临时 service 来验证 token
        user_repo = AsyncUserRepository(session)
        session_repo = AsyncUserSessionRepository(session)
        auth_service = AuthService(user_repo, session_repo)
        
        user = await auth_service.get_current_user(access_token)
        return user
    except Exception as e:
        logger.warning(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_admin_user(user: "User" = Depends(get_current_user)) -> "User":
    """
    Verify the user has admin privileges.

    Args:
        user: Current authenticated user

    Returns:
        User: User information if admin

    Raises:
        HTTPException: If user is not an admin
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )

    return user


# Other utilities


def get_logger() -> Any:
    """
    Get configured logger instance.

    Returns:
        Logger instance
    """
    return logger


# =====================================
# Rate Limiting
# =====================================


async def check_rate_limit(
    user_id: str = Depends(verify_api_key),
    client_ip: Optional[str] = Header(None, alias="X-Forwarded-For"),
) -> None:
    """
    Check if the user has exceeded their rate limit.

    This is a secondary check beyond the middleware rate limit.
    It enforces user-specific limits based on their tier/subscription.

    Args:
        user_id: User ID from API key verification
        client_ip: Client IP address from X-Forwarded-For header

    Raises:
        ForbiddenError: If rate limit exceeded
    """
    # For now, this is a placeholder
    # In a production app, check a database or Redis cache for rate limit data


# =====================================
# Qdrant Vector Database Dependencies
# =====================================

from chatbi.database.qdrant import (
    AsyncQdrantManager,
    QdrantManager,
    get_async_qdrant_manager,
    get_qdrant_manager,
)


def get_qdrant_client() -> QdrantManager:
    """Get synchronous Qdrant manager instance."""
    return get_qdrant_manager()


def get_async_qdrant_client() -> AsyncQdrantManager:
    """Get asynchronous Qdrant manager instance."""
    return get_async_qdrant_manager()


QdrantDep = Annotated[QdrantManager, Depends(get_qdrant_client)]
AsyncQdrantDep = Annotated[AsyncQdrantManager, Depends(get_async_qdrant_client)]


# =====================================
# Rate Limiting
# =====================================

from functools import wraps
from typing import Optional


async def check_rate_limit_dependency(
    request: Request,
    rate_limiter: "EnhancedRateLimiter" = Depends(lambda: get_rate_limiter()),
) -> None:
    """FastAPI dependency for checking rate limits.
    
    Usage:
        ```python
        @router.post("/api/v1/ask", dependencies=[Depends(check_rate_limit_dependency)])
        async def ask_question(...):
            pass
        ```
    
    Args:
        request: FastAPI request
        rate_limiter: Rate limiter instance
    
    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    from chatbi.middleware.enhanced_rate_limiter import get_rate_limiter
    
    rate_limiter = get_rate_limiter()
    
    # Extract user info from request state (set by auth middleware)
    user_id = getattr(request.state, "user_id", None)
    is_admin = getattr(request.state, "is_admin", False)
    
    # Check rate limit
    allowed, error_msg, retry_after = await rate_limiter.check_rate_limit(
        request=request,
        user_id=user_id,
        is_admin=is_admin,
    )
    
    if not allowed:
        logger.warning(
            f"Rate limit exceeded for {'user:' + user_id if user_id else 'IP:' + rate_limiter._get_client_ip(request)}: "
            f"{error_msg}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_msg,
            headers={"Retry-After": str(retry_after)} if retry_after else {},
        )


def rate_limit(
    per_minute: Optional[int] = None,
    per_hour: Optional[int] = None,
):
    """Decorator for applying custom rate limits to specific endpoints.
    
    Usage:
        ```python
        @router.post("/api/v1/expensive-operation")
        @rate_limit(per_minute=5, per_hour=20)
        async def expensive_operation(...):
            pass
        ```
    
    Args:
        per_minute: Maximum requests per minute (None = use default)
        per_hour: Maximum requests per hour (None = use default)
    
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request = None, **kwargs):
            from chatbi.middleware.enhanced_rate_limiter import get_rate_limiter
            
            if request is None:
                # Try to find request in args/kwargs
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                if request is None:
                    request = kwargs.get("request")
            
            if request is None:
                logger.warning("Rate limit decorator: Request not found, skipping check")
                return await func(*args, **kwargs)
            
            # Get rate limiter
            rate_limiter = get_rate_limiter()
            
            # Extract user info
            user_id = getattr(request.state, "user_id", None)
            is_admin = getattr(request.state, "is_admin", False)
            
            # Skip check for admins
            if is_admin:
                return await func(*args, **kwargs)
            
            # Create custom limits if specified
            if per_minute or per_hour:
                # Temporarily override limits for this check
                original_limits = (
                    rate_limiter.user_limits if user_id else rate_limiter.anonymous_limits
                )
                custom_limits = (
                    per_minute or original_limits[0],
                    per_hour or original_limits[1],
                )
                
                # Monkey patch limits (not ideal but works for prototype)
                if user_id:
                    rate_limiter.user_limits = custom_limits
                else:
                    rate_limiter.anonymous_limits = custom_limits
                
                try:
                    # Check with custom limits
                    allowed, error_msg, retry_after = await rate_limiter.check_rate_limit(
                        request=request,
                        user_id=user_id,
                        is_admin=is_admin,
                    )
                finally:
                    # Restore original limits
                    if user_id:
                        rate_limiter.user_limits = original_limits
                    else:
                        rate_limiter.anonymous_limits = original_limits
                
                if not allowed:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=error_msg,
                        headers={"Retry-After": str(retry_after)} if retry_after else {},
                    )
            else:
                # Use default limits
                await check_rate_limit_dependency(request, rate_limiter)
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


RateLimitDep = Annotated[None, Depends(check_rate_limit_dependency)]


# =====================================
# Analytics Tracking
# =====================================


async def track_request(
    user_id: str = Depends(verify_api_key),
    user_agent: Optional[str] = Header(None),
    referer: Optional[str] = Header(None),
) -> None:
    """
    Track request for analytics purposes.

    Args:
        user_id: User ID from API key verification
        user_agent: User agent from request header
        referer: Referer from request header
    """
    # This would log usage metrics to a database or analytics service
    # For now, just log to debug
    if config.env != "production":
        logger.debug(
            f"Request from {user_id} - Agent: {user_agent}, Referer: {referer}"
        )
