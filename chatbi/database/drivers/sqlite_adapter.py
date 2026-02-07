"""
SQLite database adapter implementation with advanced connection pooling.
"""

import asyncio
import os
import sqlite3
import time
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

from loguru import logger

from chatbi.database.drivers.base import DatabaseAdapter
from chatbi.database.drivers.factory import register_adapter
from chatbi.domain.datasource import ConnectionInfo, DatabaseType
from chatbi.exceptions import DatabaseError


@register_adapter(DatabaseType.SQLITE)
class SQLiteAdapter(DatabaseAdapter):
    """SQLite database adapter implementation with enhanced connection pooling."""

    # Class level connection pool with metadata
    _connection_pool: dict[str, dict[str, Any]] = {}
    _pool_lock = asyncio.Lock()
    # Max idle time before connection cleanup (seconds)
    _MAX_IDLE_TIME = 60 * 10  # 10 minutes
    # Interval for checking idle connections
    _CLEANUP_INTERVAL = 60 * 5  # 5 minutes
    # Last cleanup time
    _last_cleanup_time = 0

    def __init__(self):
        self.connection_id = str(uuid4())
        self.is_connected = False
        self._db_path = None

    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool or create a new one with validation."""
        if not self.is_connected:
            raise DatabaseError(detail="Not connected to SQLite database")

        await self._cleanup_check()

        async with self._pool_lock:
            conn_info = self._connection_pool.get(self._db_path)

            # If no connection exists or it's invalid, create a new one
            if not conn_info or not self._is_connection_valid(conn_info["connection"]):
                conn = await self._create_connection()
                self._connection_pool[self._db_path] = {
                    "connection": conn,
                    "last_used": time.time(),
                    "created": time.time(),
                }
                conn_info = self._connection_pool[self._db_path]
            else:
                # Update last used timestamp
                conn_info["last_used"] = time.time()

        try:
            yield conn_info["connection"]
        except Exception as e:
            logger.error(f"Error during database operation: {e!s}")
            # If it's a database corruption error, invalidate the connection
            if "database disk image is malformed" in str(
                e
            ) or "database is locked" in str(e):
                async with self._pool_lock:
                    if self._db_path in self._connection_pool:
                        with suppress(Exception):
                            self._connection_pool[self._db_path]["connection"].close()
                        del self._connection_pool[self._db_path]
            raise DatabaseError(detail=str(e))

    def _is_connection_valid(self, conn: sqlite3.Connection) -> bool:
        """Check if connection is valid and responsive with timeout."""
        try:
            # Set shorter timeout for validation query
            conn.execute("PRAGMA quick_check(1)").fetchone()
            return True
        except (sqlite3.Error, Exception):
            return False

    async def _create_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection with optimized settings."""
        try:
            conn = await asyncio.to_thread(
                sqlite3.connect,
                self._db_path,
                check_same_thread=False,
                isolation_level=None,
                timeout=30.0,  # Connection timeout in seconds
            )

            # Configure connection with optimized settings
            conn.row_factory = sqlite3.Row

            # Execute performance optimization pragmas
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=10000")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.execute("PRAGMA mmap_size=30000000000")
            cursor.execute("PRAGMA busy_timeout=30000")  # 30 seconds busy timeout
            cursor.close()

            return conn
        except Exception as e:
            raise DatabaseError(detail=f"Failed to create SQLite connection: {e!s}")

    async def _cleanup_check(self):
        """Check if we need to clean up idle connections."""
        current_time = time.time()

        # Only check every CLEANUP_INTERVAL seconds
        if current_time - self._last_cleanup_time < self._CLEANUP_INTERVAL:
            return

        # Run the cleanup
        async with self._pool_lock:
            self._last_cleanup_time = current_time
            to_remove = []

            for db_path, conn_info in self._connection_pool.items():
                if current_time - conn_info["last_used"] > self._MAX_IDLE_TIME:
                    to_remove.append(db_path)

            for db_path in to_remove:
                try:
                    self._connection_pool[db_path]["connection"].close()
                except Exception as e:
                    logger.warning(f"Error closing idle connection: {e!s}")
                del self._connection_pool[db_path]

            if to_remove:
                logger.info(f"Cleaned up {len(to_remove)} idle SQLite connections")

    async def connect(self, connection_info: ConnectionInfo) -> None:
        """
        Connect to SQLite database with connection pooling and validation.

        Args:
            connection_info: Connection parameters

        Raises:
            DatabaseError: If connection fails
        """
        try:
            db_path = connection_info.database

            # If path is not absolute, make it relative to the current directory
            if not os.path.isabs(db_path):
                db_path = os.path.abspath(db_path)

            # Verify the database file exists
            if not os.path.exists(db_path):
                raise DatabaseError(
                    message=f"SQLite database file not found: {db_path}"
                )

            self._db_path = db_path

            # Test connection by creating one
            async with self.get_connection() as _:
                pass

            self.is_connected = True
            logger.info(f"Connected to SQLite database: {db_path}")

        except Exception as e:
            self.is_connected = False
            raise DatabaseError(detail=f"Failed to connect to SQLite database: {e!s}")

    async def execute(
        self, query: str, params: Optional[Union[tuple, list[tuple], dict]] = None
    ) -> list[dict[str, Any]]:
        """
        Execute a SQL query with improved error handling and connection management.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            List of dictionaries containing query results

        Raises:
            DatabaseError: If query execution fails
        """
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()

                try:
                    start_time = time.time()
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)

                    if cursor.description:
                        columns = [col[0] for col in cursor.description]
                        results = []
                        for row in cursor.fetchall():
                            results.append(dict(zip(columns, row)))

                        query_time = time.time() - start_time
                        logger.debug(
                            f"SQLite query executed in {query_time:.4f}s: {query[:100]}..."
                        )
                        return results
                    return []

                except sqlite3.Error as e:
                    error_message = str(e)
                    # Add more context to the error
                    if "syntax error" in error_message.lower():
                        error_message = f"SQL syntax error: {error_message} in query: {query[:100]}..."
                    raise DatabaseError(
                        detail=f"Query execution failed: {error_message}"
                    )
                finally:
                    cursor.close()

        except DatabaseError:
            raise
        except Exception as e:
            raise DatabaseError(detail=f"Database operation failed: {e!s}")

    async def execute_many(self, query: str, params: list[tuple]) -> None:
        """
        Execute multiple SQL queries in batch with improved performance.

        Args:
            query: SQL query template
            params: List of parameter tuples

        Raises:
            DatabaseError: If batch execution fails
        """
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()
                try:
                    start_time = time.time()
                    await asyncio.to_thread(cursor.executemany, query, params)
                    query_time = time.time() - start_time
                    logger.debug(
                        f"SQLite batch query executed in {query_time:.4f}s with {len(params)} items"
                    )
                except sqlite3.Error as e:
                    raise DatabaseError(detail=f"Batch query execution failed: {e!s}")
                finally:
                    cursor.close()
        except DatabaseError:
            raise
        except Exception as e:
            raise DatabaseError(detail=f"Database operation failed: {e!s}")

    @asynccontextmanager
    async def transaction(self):
        """
        Context manager for transaction handling with improved error management.

        Usage:
            async with adapter.transaction():
                await adapter.execute(query1)
                await adapter.execute(query2)
        """
        async with self.get_connection() as conn:
            try:
                await asyncio.to_thread(conn.execute, "BEGIN")
                yield
                await asyncio.to_thread(conn.execute, "COMMIT")
                logger.debug("SQLite transaction committed successfully")
            except Exception as e:
                await asyncio.to_thread(conn.execute, "ROLLBACK")
                logger.warning(f"SQLite transaction rolled back due to error: {e!s}")
                raise DatabaseError(detail=f"Transaction failed: {e!s}")

    async def close(self) -> None:
        """
        Close all connections in the pool and cleanup resources.
        """
        if not self.is_connected:
            return

        async with self._pool_lock:
            if self._db_path in self._connection_pool:
                try:
                    self._connection_pool[self._db_path]["connection"].close()
                    del self._connection_pool[self._db_path]
                    logger.info(f"Closed SQLite database connection: {self._db_path}")
                except Exception as e:
                    logger.error(f"Error closing database connection: {e!s}")
                    raise DatabaseError(detail=f"Failed to close connection: {e!s}")

            self.is_connected = False

    @classmethod
    async def close_all_connections(cls) -> None:
        """
        Close all SQLite connections in the pool (static method).
        """
        async with cls._pool_lock:
            for db_path, conn_info in list(cls._connection_pool.items()):
                try:
                    conn_info["connection"].close()
                except Exception as e:
                    logger.warning(f"Error closing connection to {db_path}: {e!s}")
            cls._connection_pool.clear()
            logger.info("Closed all SQLite database connections")

    async def get_tables(self) -> list[str]:
        """
        Get list of tables in the database with improved error handling.

        Returns:
            List of table names

        Raises:
            DatabaseError: If operation fails
        """
        query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """
        try:
            results = await self.execute(query)
            return [row["name"] for row in results]
        except Exception as e:
            raise DatabaseError(detail=f"Failed to get tables: {e!s}")

    async def get_table_schema(self, table_name: str) -> list[dict[str, Any]]:
        """
        Get schema information for a specific table with improved error handling.

        Args:
            table_name: Name of the table

        Returns:
            List of column definitions

        Raises:
            DatabaseError: If operation fails
        """
        query = f"PRAGMA table_info({table_name})"
        try:
            return await self.execute(query)
        except Exception as e:
            raise DatabaseError(
                message=f"Failed to get schema for table {table_name}: {e!s}"
            )

    async def vacuum(self) -> None:
        """
        Optimize database by rebuilding it to reclaim unused space.

        Raises:
            DatabaseError: If operation fails
        """
        try:
            async with self.get_connection() as conn:
                await asyncio.to_thread(conn.execute, "VACUUM")
                logger.info("Database vacuum completed successfully")
        except Exception as e:
            raise DatabaseError(detail=f"Database vacuum failed: {e!s}")

    async def test_connection(
        self, connection_info: ConnectionInfo
    ) -> tuple[bool, str, dict[str, Any]]:
        """
        Test the connection to the database.

        Args:
            connection_info: Connection parameters

        Returns:
            Tuple of (success, message, details)
        """
        try:
            # Create a temporary adapter instance for testing
            adapter = SQLiteAdapter()
            await adapter.connect(connection_info)

            # Execute a simple query to verify functionality
            tables = await adapter.get_tables()

            # Close the test connection
            await adapter.close()

            return True, "Connection successful", {"tables_count": len(tables)}

        except Exception as e:
            return False, f"Connection failed: {e!s}", {}
