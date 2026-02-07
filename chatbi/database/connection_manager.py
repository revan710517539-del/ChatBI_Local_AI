"""
Enhanced database connection manager with optimized pooling.

This module provides centralized connection management with optimized pooling,
automatic health checks, and connection lifecycle management.
"""

import asyncio
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from loguru import logger

from chatbi.database.drivers.factory import (
    create_adapter,
    get_adapter_status,
    get_pooled_connection,
)
from chatbi.domain.datasource import ConnectionInfo, DatabaseType
from chatbi.exceptions import DatabaseError, ServiceUnavailableError


def with_retry(max_retries=None):
    """
    Decorator for methods that should retry on temporary database errors.

    Args:
        max_retries: Maximum number of retry attempts
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            retry_count = 0
            actual_max_retries = max_retries or ConnectionManager.MAX_RETRIES

            while retry_count <= actual_max_retries:
                try:
                    return await func(*args, **kwargs)
                except (DatabaseError, ServiceUnavailableError) as e:
                    # Only retry on potentially transient errors
                    if (
                        retry_count >= actual_max_retries
                        or not ConnectionManager._is_retryable_error(e)
                    ):
                        raise

                    last_error = e
                    retry_count += 1
                    wait_time = ConnectionManager.RETRY_DELAY * (
                        2 ** (retry_count - 1)
                    )  # Exponential backoff

                    logger.warning(
                        f"Retrying database operation ({retry_count}/{actual_max_retries}) after error: {e!s}"
                    )
                    await asyncio.sleep(wait_time)

            # If we exit the loop without returning, raise the last error
            raise last_error or DatabaseError(detail="Retry failed with unknown error")

        return wrapper

    return decorator


class ConnectionManager:
    """
    Enhanced connection manager for database connections.

    This class provides a centralized interface for database connections
    with advanced features like connection pooling, health monitoring,
    and automatic recovery.
    """

    # Configuration defaults
    DEFAULT_TIMEOUT = 30
    DEFAULT_MAX_ROWS = 1000
    HEALTH_CHECK_INTERVAL = 60 * 5  # 5 minutes
    CONNECTION_IDLE_TIMEOUT = 60 * 10  # 10 minutes
    MAX_RETRIES = 2
    RETRY_DELAY = 1.0  # seconds

    # Connection metrics
    _metrics = {
        "queries_executed": 0,
        "queries_failed": 0,
        "total_rows_fetched": 0,
        "total_execution_time_ms": 0,
        "health_checks_performed": 0,
        "connections_recovered": 0,
        "last_health_check": None,
    }

    @classmethod
    @asynccontextmanager
    async def get_connection(
        cls,
        db_type: DatabaseType,
        connection_info: ConnectionInfo,
        timeout: float = 10.0,
    ):
        """
        Get a database connection with proper lifecycle management.

        Args:
            db_type: Database type enum
            connection_info: Connection parameters
            timeout: Connection timeout in seconds

        Yields:
            Connected database adapter

        Raises:
            DatabaseError: If connection fails
            ServiceUnavailableError: If connection pool is exhausted
        """
        start_time = time.time()

        try:
            # Use the factory's pooled connection
            async with get_pooled_connection(
                db_type=db_type, connection_info=connection_info, timeout=timeout
            ) as (conn_id, adapter):
                yield adapter
        except Exception as e:
            logger.error(f"Connection error to {db_type}: {e!s}")
            if isinstance(e, (DatabaseError, ServiceUnavailableError)):
                raise
            else:
                raise DatabaseError(detail=f"Connection error: {e!s}")
        finally:
            # Record connection metrics
            duration_ms = int((time.time() - start_time) * 1000)
            cls._metrics["total_execution_time_ms"] += duration_ms

    @staticmethod
    def _is_retryable_error(error: Exception) -> bool:
        """
        Determine if an error is potentially transient and retryable.

        Args:
            error: The exception to check

        Returns:
            True if the error is retryable
        """
        error_str = str(error).lower()

        # Common transient error patterns
        transient_patterns = [
            "connection reset",
            "connection refused",
            "temporarily unavailable",
            "timeout",
            "deadlock",
            "too many connections",
            "server closed the connection",
            "connection terminated",
            "broken pipe",
            "connection timed out",
            "lock timeout",
            "resource unavailable",
        ]

        return any(pattern in error_str for pattern in transient_patterns)

    @classmethod
    @with_retry(max_retries=2)
    async def execute_query(
        cls,
        db_type: DatabaseType,
        connection_info: ConnectionInfo,
        query: str,
        timeout: int = None,
        max_rows: int = None,
        params: Optional[dict[str, Any]] = None,
        datasource_id: Optional[UUID] = None,
    ) -> dict[str, Any]:
        """
        Execute a query on the specified database with retry capability.

        Args:
            db_type: Type of database to connect to
            connection_info: Connection parameters
            query: SQL query to execute
            timeout: Query timeout in seconds
            max_rows: Maximum number of rows to return
            params: Query parameters
            datasource_id: Optional datasource ID for logging

        Returns:
            Query results

        Raises:
            DatabaseError: If query execution fails
        """
        timeout = timeout or cls.DEFAULT_TIMEOUT
        max_rows = max_rows or cls.DEFAULT_MAX_ROWS
        start_time = time.time()
        query_id = str(uuid4())[:8]

        try:
            logger.debug(
                f"Executing query {query_id} on {db_type} {datasource_id or ''}: {query[:100]}..."
            )

            async with cls.get_connection(db_type, connection_info) as adapter:
                # Execute the query
                result = await adapter.execute_query(
                    connection_info=connection_info,
                    query=query,
                    timeout=timeout,
                    max_rows=max_rows,
                    parameters=params,
                )

                # Update metrics
                cls._metrics["queries_executed"] += 1
                execution_time = time.time() - start_time
                execution_time_ms = int(execution_time * 1000)
                cls._metrics["total_execution_time_ms"] += execution_time_ms
                cls._metrics["total_rows_fetched"] += len(result.get("rows", []))

                logger.info(
                    f"Query {query_id} executed successfully in {execution_time:.2f}s, "
                    f"returned {len(result.get('rows', []))} rows"
                )

                return result

        except Exception as e:
            cls._metrics["queries_failed"] += 1
            execution_time = time.time() - start_time
            logger.error(f"Query {query_id} failed after {execution_time:.2f}s: {e!s}")

            if isinstance(e, DatabaseError):
                raise
            else:
                raise DatabaseError(detail=f"Query execution error: {e!s}")

    @classmethod
    @with_retry(max_retries=2)
    async def test_connection(
        cls,
        db_type: DatabaseType,
        connection_info: ConnectionInfo,
        timeout: float = 10.0,
    ) -> tuple[bool, str, Optional[dict[str, Any]]]:
        """
        Test a database connection without storing it.

        Args:
            db_type: Type of database to connect to
            connection_info: Connection parameters
            timeout: Connection timeout in seconds

        Returns:
            Tuple of (success, message, details)
        """
        start_time = time.time()

        try:
            # Create a temporary adapter for testing
            adapter = create_adapter(db_type)
            result = await adapter.test_connection(connection_info)

            # Add execution time to the details
            if result[0] and result[2] is not None:
                result[2]["connection_time_ms"] = int((time.time() - start_time) * 1000)

            return result

        except Exception as e:
            logger.error(f"Connection test error for {db_type}: {e!s}")
            return False, f"Connection error: {e!s}", None

    @classmethod
    @with_retry(max_retries=2)
    async def get_schema_metadata(
        cls,
        db_type: DatabaseType,
        connection_info: ConnectionInfo,
        datasource_id: Optional[UUID] = None,
    ) -> dict[str, Any]:
        """
        Get database schema metadata.

        Args:
            db_type: Type of database
            connection_info: Connection parameters
            datasource_id: Optional datasource ID for logging

        Returns:
            Schema metadata

        Raises:
            DatabaseError: If metadata retrieval fails
        """
        start_time = time.time()

        try:
            logger.debug(
                f"Fetching schema metadata for {db_type} {datasource_id or ''}"
            )

            async with cls.get_connection(db_type, connection_info) as adapter:
                # Get schema metadata
                metadata = await adapter.get_schema_metadata(connection_info)

                execution_time = time.time() - start_time
                logger.info(
                    f"Schema metadata retrieved successfully in {execution_time:.2f}s, "
                    f"found {len(metadata.get('tables', []))} tables"
                )

                # Add extra metadata
                metadata["retrieval_time_ms"] = int(execution_time * 1000)
                metadata["datasource_type"] = db_type.value
                metadata["datasource_id"] = (
                    str(datasource_id) if datasource_id else None
                )

                return metadata

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Schema metadata retrieval failed after {execution_time:.4f}s: {e!s}"
            )

            if isinstance(e, DatabaseError):
                raise
            else:
                raise DatabaseError(detail=f"Schema metadata retrieval error: {e!s}")

    @classmethod
    async def run_health_check(cls) -> dict[str, Any]:
        """
        Run health check on the connection system.

        Returns:
            Health check results
        """
        start_time = time.time()

        try:
            # Get adapter status
            adapter_status = get_adapter_status()

            # Update metrics
            cls._metrics["health_checks_performed"] += 1
            cls._metrics["last_health_check"] = datetime.utcnow().isoformat()

            # Calculate additional metrics
            avg_query_time = 0
            if cls._metrics["queries_executed"] > 0:
                avg_query_time = (
                    cls._metrics["total_execution_time_ms"]
                    / cls._metrics["queries_executed"]
                )

            # Compile health report
            return {
                "status": "healthy",
                "adapter_status": adapter_status,
                "metrics": {
                    **cls._metrics,
                    "avg_query_time_ms": round(avg_query_time, 2),
                    "health_check_time_ms": int((time.time() - start_time) * 1000),
                },
            }

        except Exception as e:
            logger.error(f"Health check failed: {e!s}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "health_check_time_ms": int((time.time() - start_time) * 1000),
            }

    @classmethod
    def get_metrics(cls) -> dict[str, Any]:
        """
        Get connection metrics.

        Returns:
            Current connection metrics
        """
        return {
            **cls._metrics,
            "adapter_status": get_adapter_status(),
        }


# Global connection manager instance
connection_manager = ConnectionManager()
