from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union


class Cache(ABC):
    """
    Define the interface for a cache that can be used to store data.
    This abstract class provides a standard interface for different cache implementations.
    """

    @abstractmethod
    def generate_id(self, *args, **kwargs) -> str:
        """
        Generate a unique ID for the cache.

        Returns:
            str: A unique identifier
        """

    @abstractmethod
    def get(self, id: str, field: str) -> Any:
        """
        Get a value from the cache.

        Args:
            id: Unique identifier for the cached item
            field: The field to retrieve from the cached item

        Returns:
            Any: The cached value or None if not found
        """

    @abstractmethod
    def get_all(self) -> list[dict[str, Any]]:
        """
        Get all values from the cache.

        Returns:
            List[Dict[str, Any]]: A list of all cached values
        """

    @abstractmethod
    def set(self, id: str, field: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.

        Args:
            id: Unique identifier for the cached item
            field: The field to set in the cached item
            value: The value to cache
            ttl: Time to live in seconds (optional)
        """

    @abstractmethod
    def has(self, id: str, field: Optional[str] = None) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            id: Unique identifier for the cached item
            field: The specific field to check (optional)

        Returns:
            bool: True if the key exists, False otherwise
        """

    @abstractmethod
    def delete(self, id: str) -> bool:
        """
        Delete a value from the cache.

        Args:
            id: Unique identifier for the cached item

        Returns:
            bool: True if the item was deleted, False otherwise
        """

    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""
