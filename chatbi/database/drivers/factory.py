"""
Database adapter factory with optimized connection pooling and caching.

This module provides a factory pattern implementation to manage database
adapters and connections efficiently with proper resource management.
"""

import asyncio
import hashlib
import importlib
import inspect
import json
import pkgutil
import sys
import time
import weakref
from contextlib import asynccontextmanager
from typing import Any, ClassVar, Dict, Optional, Set, Tuple, Type, Union
from uuid import UUID, uuid4

from loguru import logger

from chatbi.database.drivers.base import DatabaseAdapter
from chatbi.domain.datasource import ConnectionInfo, DatabaseType
from chatbi.exceptions import DatabaseError, ServiceUnavailableError

# Type to store adapter classes
_adapter_registry: dict[DatabaseType, type[DatabaseAdapter]] = {}


# Connection pool with metadata (global state)
class ConnectionPool:
    """Connection pool manager for database adapters."""

    # Class-level connection state
    _adapters: dict[UUID, DatabaseAdapter] = {}
    _last_used: dict[UUID, float] = {}
    _conn_hashes: dict[str, set[UUID]] = {}
    _lock = asyncio.Lock()

    # Configuration
    MAX_CONNECTIONS = 50  # Total connection limit
    MAX_CONNECTIONS_PER_DB = 10  # Max connections per database
    IDLE_TIMEOUT = 60 * 10  # 10 minutes
    CLEANUP_INTERVAL = 60 * 5  # 5 minutes

    # Performance metrics
    _stats = {
        "hits": 0,
        "misses": 0,
        "timeouts": 0,
        "errors": 0,
        "created": 0,
        "closed": 0,
        "last_cleanup": 0,
    }

    # Connection semaphore for limiting total connections
    _semaphore = asyncio.Semaphore(MAX_CONNECTIONS)

    @classmethod
    async def get_connection(
        cls,
        db_type: DatabaseType,
        connection_info: ConnectionInfo,
        timeout: float = 10.0,
    ) -> tuple[UUID, DatabaseAdapter]:
        """
        Get a database connection from the pool with intelligent reuse.

        Args:
            db_type: Type of database
            connection_info: Connection parameters
            timeout: Maximum time to wait for a connection

        Returns:
            Tuple of connection ID and connected adapter

        Raises:
            ServiceUnavailableError: If the connection pool is exhausted
            DatabaseError: If connection fails
        """
        # Calculate a unique hash for this connection config
        if hasattr(connection_info, "dict_hash"):
            ch = connection_info.dict_hash
        else:
            try:
                # Use model_dump_json for Pydantic v2
                dump = connection_info.model_dump_json(exclude_none=True)
            except AttributeError:
                # Fallback
                dump = str(connection_info)
            ch = hashlib.md5(dump.encode()).hexdigest()
        
        conn_hash = f"{db_type}:{ch}"

        # First try to find an existing connection
        async with cls._lock:
            # Try to reuse existing connection
            if conn_hash in cls._conn_hashes:
                for conn_id in cls._conn_hashes[conn_hash]:
                    adapter = cls._adapters.get(conn_id)
                    if adapter and adapter.is_connected:
                        # Update last used time
                        cls._last_used[conn_id] = time.time()
                        cls._stats["hits"] += 1
                        return conn_id, adapter

            cls._stats["misses"] += 1

        # No existing connection, try to acquire a semaphore with timeout
        try:
            # Wait for a connection slot
            async with asyncio.timeout(timeout):
                acquired = await cls._semaphore.acquire()
                if not acquired:
                    cls._stats["timeouts"] += 1
                    raise ServiceUnavailableError(
                        "Database connection pool is exhausted"
                    )
        except TimeoutError:
            cls._stats["timeouts"] += 1
            raise ServiceUnavailableError("Timeout waiting for database connection")

        # Create a new adapter and connection
        try:
            # Create and initialize adapter
            adapter = create_adapter(db_type)
            await adapter.connect(connection_info)

            # Register in the connection pool
            conn_id = uuid4()
            now = time.time()

            async with cls._lock:
                cls._adapters[conn_id] = adapter
                cls._last_used[conn_id] = now

                # Add to the hash-based lookup
                if conn_hash not in cls._conn_hashes:
                    cls._conn_hashes[conn_hash] = set()
                cls._conn_hashes[conn_hash].add(conn_id)

                cls._stats["created"] += 1

                # Check if we need to run cleanup
                if now - cls._stats["last_cleanup"] > cls.CLEANUP_INTERVAL:
                    # Schedule background cleanup, don't wait for it
                    asyncio.create_task(cls._cleanup_expired())

            return conn_id, adapter

        except Exception as e:
            # Make sure to release the semaphore on error
            cls._semaphore.release()
            cls._stats["errors"] += 1

            if isinstance(e, DatabaseError):
                raise
            else:
                raise DatabaseError(
                    detail=f"Failed to create database connection: {e!s}"
                )

    @classmethod
    def release_connection(cls, conn_id: UUID):
        """
        Release a connection back to the pool.

        Args:
            conn_id: Connection ID to release
        """
        if conn_id in cls._adapters:
            # Just update the last used time, don't close yet
            cls._last_used[conn_id] = time.time()
            # Release the semaphore to allow new connections
            cls._semaphore.release()

    @classmethod
    async def _cleanup_expired(cls):
        """
        Clean up expired connections.

        This method is called periodically and closes connections that have been
        idle for too long.
        """
        now = time.time()
        cls._stats["last_cleanup"] = now
        expired_conn_ids = []

        # Identify expired connections
        async with cls._lock:
            for conn_id, last_used in cls._last_used.items():
                if now - last_used > cls.IDLE_TIMEOUT:
                    expired_conn_ids.append(conn_id)

        # Close expired connections
        closed_count = 0
        for conn_id in expired_conn_ids:
            await cls._close_connection(conn_id)
            closed_count += 1

        if closed_count > 0:
            logger.info(f"Cleaned up {closed_count} idle database connections")

    @classmethod
    async def _close_connection(cls, conn_id: UUID):
        """
        Close a specific connection.

        Args:
            conn_id: Connection ID to close
        """
        async with cls._lock:
            if conn_id not in cls._adapters:
                return

            adapter = cls._adapters[conn_id]

            # Find and remove from conn_hashes
            for conn_hash, conn_ids in list(cls._conn_hashes.items()):
                if conn_id in conn_ids:
                    conn_ids.remove(conn_id)
                    if not conn_ids:
                        del cls._conn_hashes[conn_hash]
                    break

            # Close the adapter connection
            try:
                await adapter.close()
                cls._stats["closed"] += 1
            except Exception as e:
                logger.warning(f"Error closing database connection: {e!s}")

            # Remove from tracking dictionaries
            del cls._adapters[conn_id]
            del cls._last_used[conn_id]

    @classmethod
    async def close_all_connections(cls):
        """Close all connections in the pool."""
        async with cls._lock:
            for conn_id in list(cls._adapters.keys()):
                await cls._close_connection(conn_id)

        logger.info("All database connections have been closed")

    @classmethod
    def get_stats(cls) -> dict[str, Any]:
        """Get statistics about the connection pool."""
        return {
            **cls._stats,
            "active_connections": len(cls._adapters),
            "max_connections": cls.MAX_CONNECTIONS,
            "available_slots": cls._semaphore._value,
            "connection_types": {
                db_type.value: len(
                    [
                        1
                        for conn_hash in cls._conn_hashes
                        if conn_hash.startswith(f"{db_type}:")
                    ]
                )
                for db_type in DatabaseType
            },
        }


def register_adapter(db_type: DatabaseType) -> callable:
    """
    Decorator to register a database adapter class.

    Args:
        db_type: The database type this adapter handles

    Returns:
        Decorator function
    """

    def decorator(cls: type[DatabaseAdapter]) -> type[DatabaseAdapter]:
        if not issubclass(cls, DatabaseAdapter):
            raise ValueError(f"Class {cls.__name__} must inherit from DatabaseAdapter")
        _adapter_registry[db_type] = cls
        logger.debug(f"Registered {cls.__name__} for database type {db_type}")
        return cls

    return decorator


def create_adapter(db_type: DatabaseType) -> DatabaseAdapter:
    """
    Create a new instance of the appropriate database adapter.

    Args:
        db_type: Type of database

    Returns:
        DatabaseAdapter instance

    Raises:
        DatabaseError: If no adapter is registered for the database type
    """
    if db_type not in _adapter_registry:
        raise DatabaseError(
            message=f"No adapter registered for database type: {db_type}"
        )

    adapter_class = _adapter_registry[db_type]
    return adapter_class()


def get_adapter(db_type: DatabaseType) -> DatabaseAdapter:
    """
    Get a database adapter instance.

    Args:
        db_type: Type of database

    Returns:
        DatabaseAdapter instance
    """
    # Always create new stateless adapters
    return create_adapter(db_type)


@asynccontextmanager
async def get_pooled_connection(
    db_type: DatabaseType, connection_info: ConnectionInfo, timeout: float = 10.0
) -> tuple[UUID, DatabaseAdapter]:
    """
    Get a database connection from the pool with proper resource management.

    This context manager handles getting and returning connections to the pool.

    Args:
        db_type: Type of database
        connection_info: Connection parameters
        timeout: Maximum time to wait for a connection

    Yields:
        Tuple of (connection_id, adapter)
    """
    conn_id = None

    try:
        # Get a connection from the pool
        conn_id, adapter = await ConnectionPool.get_connection(
            db_type, connection_info, timeout
        )

        # Yield to the caller
        yield conn_id, adapter

    finally:
        # Return the connection to the pool
        if conn_id:
            ConnectionPool.release_connection(conn_id)


async def cleanup_expired_adapters() -> int:
    """
    Clean up expired adapter connections.

    Returns:
        Number of connections closed
    """
    # Force an immediate cleanup
    await ConnectionPool._cleanup_expired()
    return ConnectionPool._stats["closed"]


async def close_all_connections() -> None:
    """Close all database connections."""
    await ConnectionPool.close_all_connections()


def get_adapter_status() -> dict[str, Any]:
    """
    Get status information about database adapters and connections.

    Returns:
        Dictionary with adapter status information
    """
    return {
        "registered_adapters": list(_adapter_registry.keys()),
        **ConnectionPool.get_stats(),
    }


def auto_discover_adapters() -> None:
    """
    Auto-discover and register database adapters.

    This function finds all adapter classes in the current package that
    follow the naming convention of *Adapter and registers them with
    the appropriate database type.
    """
    import chatbi.database.drivers as drivers_pkg
    from chatbi.database.drivers import base

    # Map class names to database types
    name_to_type = {
        "PostgresAdapter": DatabaseType.POSTGRES,
        "MySqlAdapter": DatabaseType.MYSQL,
        "MsSqlAdapter": DatabaseType.MSSQL,
        "ClickHouseAdapter": DatabaseType.CLICKHOUSE,
        "DuckDbAdapter": DatabaseType.DUCKDB,
        "BigQueryAdapter": DatabaseType.BIGQUERY,
        "SnowflakeAdapter": DatabaseType.SNOWFLAKE,
        "TrinoAdapter": DatabaseType.TRINO,
        "SqliteAdapter": DatabaseType.SQLITE,
    }

    # Get the package path
    pkg_path = drivers_pkg.__path__
    pkg_name = drivers_pkg.__name__

    # Find all modules in the package
    for _, module_name, is_pkg in pkgutil.iter_modules(pkg_path, pkg_name + "."):
        if is_pkg or module_name in (f"{pkg_name}.base", f"{pkg_name}.factory"):
            continue

        try:
            # Import the module
            module = importlib.import_module(module_name)

            # Find all classes that are DatabaseAdapter subclasses
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, base.DatabaseAdapter)
                    and obj != base.DatabaseAdapter
                    and name in name_to_type
                ):
                    # Get the database type for this adapter
                    db_type = name_to_type[name]

                    # Register the adapter
                    logger.info(
                        f"Auto-discovered database adapter: {name} for {db_type}"
                    )
                    _adapter_registry[db_type] = obj

        except (ImportError, AttributeError) as e:
            logger.warning(f"Error auto-discovering adapters in {module_name}: {e!s}")


# Auto-discover and register adapters on module import
auto_discover_adapters()
