from enum import Enum
from typing import Dict, Optional, Type

from loguru import logger

from chatbi.cache.base import Cache
from chatbi.cache.memory import MemoryCache
from chatbi.cache.redis import RedisCache


class CacheType(str, Enum):
    MEMORY = "memory"
    REDIS = "redis"


# Cache registry to store singleton instances
_cache_instances: dict[str, Cache] = {}

# Cache implementation registry
_cache_implementations: dict[str, type[Cache]] = {
    CacheType.MEMORY: MemoryCache,
    CacheType.REDIS: RedisCache,
}


def get_cache(cache_type: str = CacheType.MEMORY, **kwargs) -> Cache:
    """
    Get a cache instance of the specified type.

    This factory function returns a singleton instance of the requested cache type.

    Args:
        cache_type: Type of cache to use (memory or redis)
        **kwargs: Additional arguments to pass to the cache constructor

    Returns:
        Cache: An instance of the requested cache type
    """
    # Use normalized cache type as the key
    cache_type = cache_type.lower()

    # Check if we already have an instance of this cache type
    if cache_type in _cache_instances:
        return _cache_instances[cache_type]

    # Check if the requested cache type is supported
    if cache_type not in _cache_implementations:
        logger.warning(
            f"Unsupported cache type: {cache_type}, falling back to memory cache"
        )
        cache_type = CacheType.MEMORY

    # Create a new instance of the requested cache type
    cache_class = _cache_implementations[cache_type]
    cache_instance = cache_class(**kwargs)

    # Store the instance for future use
    _cache_instances[cache_type] = cache_instance

    return cache_instance


def register_cache_implementation(cache_type: str, implementation: type[Cache]) -> None:
    """
    Register a new cache implementation.

    This allows extending the caching system with custom implementations.

    Args:
        cache_type: Name to identify the cache type
        implementation: Cache class to register
    """
    _cache_implementations[cache_type.lower()] = implementation
    logger.debug(f"Registered cache implementation for {cache_type}")


# Default cache instance - convenience shortcut for common usage
default_cache = get_cache(CacheType.MEMORY)
