import json
import time
import uuid
from datetime import timedelta
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple, Union

import redis
from loguru import logger

from chatbi.cache.base import Cache
from chatbi.config import get_config


def _with_redis_error_handling(func):
    """Decorator to handle Redis connection errors"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except redis.ConnectionError as e:
            logger.warning(
                f"Redis connection error: {e} - Falling back to default behavior"
            )
            return None  # Or appropriate fallback value
        except redis.RedisError as e:
            logger.error(f"Redis error in {func.__name__}: {e}")
            return None

    return wrapper


class RedisCache(Cache):
    """
    Redis-based cache implementation with TTL support.

    This implementation stores cache entries in Redis, making it suitable
    for distributed environments where multiple instances need to share cache.
    """

    def __init__(self, **kwargs):
        """Initialize Redis connection from config or passed parameters"""
        config = get_config()

        # Get Redis config from kwargs or fallback to config
        self.host = kwargs.get("host", config.redis.host)
        self.port = kwargs.get("port", config.redis.port)
        self.db = kwargs.get("db", config.redis.db)
        self.password = kwargs.get("password", config.redis.password)
        self.ssl = kwargs.get("ssl", config.redis.ssl)

        # Create Redis client
        try:
            self.redis = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                ssl=self.ssl,
                socket_timeout=5,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30,
                retry_on_timeout=True,
                decode_responses=True,  # Auto-decode responses to strings
            )
            # Test connection
            self.redis.ping()
            logger.info("Redis connection established successfully")
        except redis.ConnectionError as e:
            logger.error(f"Could not connect to Redis: {e}")
            logger.warning(
                "Redis cache will not be available - please check your configuration"
            )
            self.redis = None
        except Exception as e:
            logger.error(f"Redis initialization error: {e}")
            self.redis = None

    @_with_redis_error_handling
    def generate_id(self, *args, **kwargs) -> str:
        """Generate a unique ID for the cache entry"""
        # Generate a unique ID, optionally based on provided arguments
        if "question" in kwargs:
            # Create deterministic ID from question, which allows finding same question twice
            unique_id = str(hash(kwargs["question"]))
        else:
            # Use UUID for general purpose unique IDs
            unique_id = str(uuid.uuid4())

        # Add a timestamp prefix for better sorting
        timestamp = int(time.time())
        return f"{timestamp}:{unique_id}"

    @_with_redis_error_handling
    def get(self, id: str, field: str) -> Any:
        """Get a value from Redis"""
        if not self.redis:
            return None

        key = f"{id}:{field}"
        result = self.redis.get(key)

        # Return None if not found
        if result is None:
            return None

        # Try to deserialize the value
        try:
            return json.loads(result)
        except (json.JSONDecodeError, TypeError):
            # If not JSON, return the raw value
            return result

    @_with_redis_error_handling
    def get_all(self) -> list[dict[str, Any]]:
        """Get all values from the cache - limited to prevent memory issues"""
        if not self.redis:
            return []

        # This could be very resource intensive in production
        # Limiting to recent keys
        keys = self.redis.keys("*")[:1000]
        result = []

        # Group by ID
        id_groups = {}
        for key in keys:
            parts = key.split(":", 1)
            if len(parts) < 2:
                continue

            id, field = parts
            if id not in id_groups:
                id_groups[id] = {}

            value = self.get(id, field)
            id_groups[id][field] = value

        # Convert to list of dictionaries
        for id, fields in id_groups.items():
            result.append(fields)

        return result

    @_with_redis_error_handling
    def set(self, id: str, field: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in Redis with optional TTL"""
        if not self.redis:
            return

        key = f"{id}:{field}"

        # Serialize complex objects
        if not isinstance(value, (str, int, float, bool, type(None))):
            try:
                value = json.dumps(value)
            except (TypeError, ValueError) as e:
                logger.warning(f"Could not serialize value for {id}:{field}: {e}")
                return

        # Set the value with optional expiration
        if ttl:
            self.redis.setex(key, ttl, value)
        else:
            self.redis.set(key, value)

    @_with_redis_error_handling
    def has(self, id: str, field: Optional[str] = None) -> bool:
        """Check if a key exists in Redis"""
        if not self.redis:
            return False

        if field is not None:
            # Check specific field
            key = f"{id}:{field}"
            return bool(self.redis.exists(key))
        else:
            # Check if any field exists for this ID
            pattern = f"{id}:*"
            return bool(self.redis.keys(pattern))

    @_with_redis_error_handling
    def delete(self, id: str) -> bool:
        """Delete all fields for an ID from Redis"""
        if not self.redis:
            return False

        pattern = f"{id}:*"
        keys = self.redis.keys(pattern)

        if not keys:
            return False

        # Delete all matching keys
        self.redis.delete(*keys)
        return True

    @_with_redis_error_handling
    def clear(self) -> None:
        """Clear all cache entries - use with caution!"""
        if not self.redis:
            return

        # This is dangerous in production - limiting to namespace or pattern is safer
        self.redis.flushdb()
        logger.warning("Redis cache has been cleared")

    @_with_redis_error_handling
    def set_many(
        self, id: str, values: dict[str, Any], ttl: Optional[int] = None
    ) -> None:
        """Set multiple fields at once for better performance"""
        if not self.redis:
            return

        # Use pipeline for better performance
        with self.redis.pipeline() as pipe:
            for field, value in values.items():
                key = f"{id}:{field}"

                # Serialize complex objects
                if not isinstance(value, (str, int, float, bool, type(None))):
                    try:
                        value = json.dumps(value)
                    except (TypeError, ValueError):
                        continue

                if ttl:
                    pipe.setex(key, ttl, value)
                else:
                    pipe.set(key, value)

            # Execute all commands in a single network call
            pipe.execute()
