import time
import uuid
from typing import Any, Dict, List, Optional

from chatbi.cache.base import Cache


class MemoryCache(Cache):
    """
    In-memory cache implementation with TTL support.

    This implementation stores cache entries and their expiration times in memory.
    It's efficient for single-instance deployments but doesn't work across multiple instances.
    """

    def __init__(self):
        # Main cache storage: {id: {field: value, ...}, ...}
        self.cache: dict[str, dict[str, Any]] = {}
        # TTL storage: {id: {field: expiration_time, ...}, ...}
        self.expiration: dict[str, dict[str, float]] = {}

    def generate_id(self, *args, **kwargs) -> str:
        """Generate a unique ID for the cache entry"""
        return str(uuid.uuid4())

    def get(self, id: str, field: str) -> Any:
        """Get a value from the cache, respecting TTL"""
        self._cleanup_expired(id, field)

        if id in self.cache and field in self.cache[id]:
            return self.cache[id][field]

        return None

    def has(self, id: str, field: Optional[str] = None) -> bool:
        """Check if a key exists in the cache, respecting TTL"""
        if field is not None:
            # Check specific field
            self._cleanup_expired(id, field)
            return id in self.cache and field in self.cache[id]
        else:
            # Check if ID exists with any valid fields
            if id not in self.cache:
                return False

            # Clean up all expired fields for this ID
            for field_name in list(self.cache[id].keys()):
                self._cleanup_expired(id, field_name)

            # Return True if there are any fields left
            return id in self.cache and bool(self.cache[id])

    def set(self, id: str, field: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in the cache with optional TTL"""
        if id not in self.cache:
            self.cache[id] = {}

        self.cache[id][field] = value

        # Handle TTL
        if ttl is not None:
            if id not in self.expiration:
                self.expiration[id] = {}
            self.expiration[id][field] = time.time() + ttl

    def delete(self, id: str) -> bool:
        """Delete a value from the cache"""
        if id in self.cache:
            del self.cache[id]
            if id in self.expiration:
                del self.expiration[id]
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.expiration.clear()

    def get_all(self) -> list[dict[str, Any]]:
        """Get all cache entries, respecting TTL"""
        result = []

        # Clean up expired entries first
        for id in list(self.cache.keys()):
            for field in list(self.cache[id].keys()):
                self._cleanup_expired(id, field)

            # Add to result if there are any fields left
            if self.cache.get(id):
                result.append(self.cache[id])

        return result

    def _cleanup_expired(self, id: str, field: str) -> None:
        """Remove expired cache entries"""
        if (
            id in self.expiration
            and field in self.expiration[id]
            and time.time() > self.expiration[id][field]
        ):
            # Remove expired field
            del self.cache[id][field]
            del self.expiration[id][field]

            # Clean up empty dictionaries
            if not self.cache[id]:
                del self.cache[id]
            if id in self.expiration and not self.expiration[id]:
                del self.expiration[id]
