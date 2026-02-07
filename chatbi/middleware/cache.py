import hashlib
import json
import re
import time
from collections.abc import Callable
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional, Set, Union, cast

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from chatbi.cache.memory import MemoryCache
from chatbi.cache.redis import RedisCache
from chatbi.config import get_config

# Get application configuration
config = get_config()

# Determine which cache implementation to use
if config.cache.type == "redis":
    # Parse Redis URL to get components
    redis_url = config.cache.url
    pattern = r"redis://(?:(?P<username>.*?):(?P<password>.*?)@)?(?P<host>.*?):(?P<port>\d+)(?:/(?P<db>\d+))?"
    match = re.match(pattern, redis_url)

    if match:
        redis_config = match.groupdict()
        cache_backend = RedisCache(
            host=redis_config.get("host", "localhost"),
            port=int(redis_config.get("port", 6379)),
            password=redis_config.get("password", None),
            db=int(redis_config.get("db", 0)),
            prefix="chatbi:cache:",
        )
    else:
        logger.warning(f"Invalid Redis URL: {redis_url}, falling back to memory cache")
        cache_backend = MemoryCache(max_size=1000)
else:
    # Default to in-memory cache
    cache_backend = MemoryCache(max_size=1000)


class ResponseCacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware to cache responses for GET requests to improve performance.

    This implements HTTP caching with proper invalidation and conditional requests.
    """

    def __init__(
        self,
        app,
        ttl_seconds: int = 300,
        exclude_paths: Optional[list[str]] = None,
        exclude_query_params: Optional[list[str]] = None,
    ):
        super().__init__(app)
        self.ttl_seconds = ttl_seconds
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
        ]
        self.exclude_query_params = exclude_query_params or [
            "_",
            "timestamp",
            "cache_buster",
        ]

    def get_cache_key(self, request: Request) -> str:
        """
        Generate a unique cache key for the request based on path and relevant query params.

        Excludes certain transient query parameters like timestamps to avoid cache misses.
        """
        # Start with path
        key_parts = [request.url.path]

        # Add method
        key_parts.append(request.method)

        # Add query params, sorted for consistency and filtered to exclude transient params
        query_params = request.query_params
        filtered_params = {
            k: v for k, v in query_params.items() if k not in self.exclude_query_params
        }

        if filtered_params:
            sorted_params = sorted(filtered_params.items())
            key_parts.append(str(sorted_params))

        # Add headers that might affect the response
        for header in ["Accept", "Accept-Language"]:
            if header in request.headers:
                key_parts.append(f"{header}:{request.headers[header]}")

        # Add API key or auth token hash if present (to separate cached responses by user)
        api_key = request.headers.get("X-API-Key", "")
        if api_key:
            # Only store a hash of the API key for security
            key_parts.append(
                f"api_key:{hashlib.sha256(api_key.encode()).hexdigest()[:8]}"
            )

        auth_header = request.headers.get("Authorization", "")
        if auth_header and auth_header.startswith("Bearer "):
            # Only store a hash of the token for security
            key_parts.append(
                f"auth:{hashlib.sha256(auth_header.encode()).hexdigest()[:8]}"
            )

        # Generate final key
        cache_key = hashlib.sha256(":".join(key_parts).encode()).hexdigest()

        return f"response:{cache_key}"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process a request with caching for eligible GET requests.
        """
        # Only cache GET requests to eligible paths
        if request.method != "GET" or any(
            request.url.path.startswith(path) for path in self.exclude_paths
        ):
            return await call_next(request)

        # Check for cache bypass header (useful for forcing fresh content)
        if request.headers.get("Cache-Control") == "no-cache":
            return await call_next(request)

        # Generate cache key for this request
        cache_key = self.get_cache_key(request)

        # Try to get from cache
        cached_data = cache_backend.get(cache_key)
        if cached_data:
            # Check for conditional request with If-None-Match header
            if "ETag" in cached_data["headers"]:
                etag = cached_data["headers"]["ETag"]
                if_none_match = request.headers.get("if-none-match")
                if if_none_match and if_none_match == etag:
                    # Client already has the latest version
                    return Response(status_code=304, headers=cached_data["headers"])

            # Reconstruct cached response
            response_cls = Response
            if cached_data["content_type"] == "application/json":
                from fastapi.responses import JSONResponse

                response_cls = JSONResponse

            response = response_cls(
                content=cached_data["content"],
                status_code=cached_data["status_code"],
                headers=cached_data["headers"],
            )

            # Add header to indicate cache hit
            response.headers["X-Cache"] = "HIT"
            return response

        # No cache hit, process request normally
        response = await call_next(request)

        # Only cache successful responses
        if 200 <= response.status_code < 300:
            # Extract data to cache
            cache_data = {
                "content": response.body,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content_type": response.headers.get("Content-Type", "text/plain"),
                "cached_at": datetime.utcnow().isoformat(),
            }

            # Add ETag if not present
            if "ETag" not in response.headers and hasattr(response, "body"):
                etag = f'W/"{hashlib.md5(response.body).hexdigest()}"'
                response.headers["ETag"] = etag
                cache_data["headers"]["ETag"] = etag

            # Store in cache with TTL
            cache_backend.set(cache_key, cache_data, self.ttl_seconds)

            # Add header to indicate cache miss
            response.headers["X-Cache"] = "MISS"

        return response


def cached_response(ttl_seconds: int = 300):
    """
    Decorator for endpoint functions to cache their responses.

    Example usage:
    @router.get("/example")
    @cached_response(ttl_seconds=60)
    def get_example(request: Request):
        # This response will be cached for 60 seconds
        return {"data": "example"}
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
            # Only cache GET requests
            if request.method != "GET":
                return await func(request, *args, **kwargs)

            # Check for cache bypass header
            if request.headers.get("Cache-Control") == "no-cache":
                return await func(request, *args, **kwargs)

            # Generate a cache key based on function name, args and kwargs
            key_parts = [func.__module__, func.__name__]

            # Add query params, sorted for consistency
            query_params = dict(request.query_params)
            if query_params:
                # Filter out cache busting params
                filtered_params = {
                    k: v
                    for k, v in sorted(query_params.items())
                    if k not in ["_", "timestamp", "cache_buster"]
                }
                if filtered_params:
                    key_parts.append(str(filtered_params))

            # Add path params from kwargs that look like they're from the path
            path_params = {k: v for k, v in kwargs.items() if isinstance(v, (str, int))}
            if path_params:
                key_parts.append(str(sorted(path_params.items())))

            # Add API key or auth token hash if present
            api_key = request.headers.get("X-API-Key", "")
            if api_key:
                # Only store a hash of the API key for security
                key_parts.append(
                    f"api_key:{hashlib.sha256(api_key.encode()).hexdigest()[:8]}"
                )

            auth_header = request.headers.get("Authorization", "")
            if auth_header and auth_header.startswith("Bearer "):
                # Only store a hash of the token for security
                key_parts.append(
                    f"auth:{hashlib.sha256(auth_header.encode()).hexdigest()[:8]}"
                )

            # Generate final key
            cache_key = hashlib.sha256(
                ":".join(map(str, key_parts)).encode()
            ).hexdigest()
            decorated_func_key = f"endpoint:{cache_key}"

            # Try to get from cache
            cached_value = cache_backend.get(decorated_func_key)
            if cached_value:
                logger.debug(f"Cache hit for {func.__name__}")

                # Check for conditional request with If-None-Match
                etag = cached_value.get("etag")
                if etag:
                    if_none_match = request.headers.get("if-none-match")
                    if if_none_match and if_none_match == etag:
                        # Return 304 Not Modified
                        response = Response(status_code=304)
                        response.headers["ETag"] = etag
                        return response

                # Convert cached value back to a response
                if isinstance(cached_value["data"], dict):
                    from fastapi.responses import JSONResponse

                    response = JSONResponse(content=cached_value["data"])
                else:
                    response = Response(content=cached_value["data"])

                # Add cache headers
                response.headers["X-Cache"] = "HIT"
                if etag:
                    response.headers["ETag"] = etag

                return response

            # No cache hit, execute the function
            response = await func(request, *args, **kwargs)

            # Only cache successful responses
            if hasattr(response, "status_code") and 200 <= response.status_code < 300:
                # Extract data to cache
                if hasattr(response, "body"):
                    data = response.body
                else:
                    # Try to get the response data
                    try:
                        data = response.body
                    except:
                        # Fallback for non-standard responses
                        data = str(response)

                # Calculate ETag
                if hasattr(response, "body") and response.body:
                    etag = f'W/"{hashlib.md5(response.body).hexdigest()}"'
                else:
                    etag = None

                # Store in cache with TTL
                cache_data = {
                    "data": data,
                    "cached_at": datetime.utcnow().isoformat(),
                }

                if etag:
                    cache_data["etag"] = etag
                    if hasattr(response, "headers"):
                        response.headers["ETag"] = etag

                cache_backend.set(decorated_func_key, cache_data, ttl_seconds)

                # Add cache header to indicate miss
                if hasattr(response, "headers"):
                    response.headers["X-Cache"] = "MISS"

            return response

        return wrapper

    return decorator


# Cache control decorator that adds max-age and cache-control headers to responses
def with_cache_control(
    max_age: int = 60, private: bool = False, no_store: bool = False
):
    """
    Decorator to add Cache-Control headers to responses.

    Args:
        max_age: Maximum time in seconds the response is fresh
        private: Whether the response should be private to the user
        no_store: Whether the response should not be stored
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            response = await func(*args, **kwargs)

            # Build Cache-Control header
            cache_control_parts = []

            if no_store:
                cache_control_parts.append("no-store")
            else:
                if private:
                    cache_control_parts.append("private")
                else:
                    cache_control_parts.append("public")

                cache_control_parts.append(f"max-age={max_age}")

            # Add header to response
            if hasattr(response, "headers"):
                response.headers["Cache-Control"] = ", ".join(cache_control_parts)

                # Add Expires header for HTTP/1.0 compatibility
                expiry_time = datetime.utcnow() + timedelta(seconds=max_age)
                response.headers["Expires"] = expiry_time.strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                )

            return response

        return wrapper

    return decorator


# Helper for cache key generation based on request and parameters
def make_cache_key(request: Request, *args, **kwargs) -> str:
    """
    Generate a cache key for a request with additional parameters.
    """
    # Start with path and method
    key_parts = [request.url.path, request.method]

    # Add query params, sorted for consistency
    query_params = dict(request.query_params)
    if query_params:
        # Filter out cache busting params
        filtered_params = {
            k: v
            for k, v in sorted(query_params.items())
            if k not in ["_", "timestamp", "cache_buster"]
        }
        if filtered_params:
            key_parts.append(str(filtered_params))

    # Add extra args and kwargs
    if args:
        key_parts.append(str(args))
    if kwargs:
        key_parts.append(str(sorted(kwargs.items())))

    # Add API key or auth token hash if present
    api_key = request.headers.get("X-API-Key", "")
    if api_key:
        # Only store a hash of the API key for security
        key_parts.append(f"api_key:{hashlib.sha256(api_key.encode()).hexdigest()[:8]}")

    auth_header = request.headers.get("Authorization", "")
    if auth_header and auth_header.startswith("Bearer "):
        # Only store a hash of the token for security
        key_parts.append(f"auth:{hashlib.sha256(auth_header.encode()).hexdigest()[:8]}")

    # Generate final key
    return hashlib.sha256(":".join(map(str, key_parts)).encode()).hexdigest()
