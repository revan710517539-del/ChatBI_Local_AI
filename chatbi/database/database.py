"""
Unified PostgreSQL database access for ChatBI.

This module provides comprehensive PostgreSQL access with both synchronous
and asynchronous interfaces, proper connection pooling, and standardized
error handling for all database operations.
"""

import time
from collections.abc import AsyncGenerator, Callable, Generator
from contextlib import asynccontextmanager, contextmanager
from functools import wraps
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
    cast,
)

import asyncpg
from loguru import logger
from psycopg2 import OperationalError, connect, extras, pool
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from chatbi.config import get_config
from chatbi.exceptions import DatabaseError

# Load configuration
config = get_config()
db_config = config.database

print(f"Database config: {db_config}")

# PostgreSQL connection parameters
postgres_user = db_config.user
postgres_password = db_config.password
postgres_host = db_config.host
postgres_port = db_config.port
postgres_dbname = db_config.name

# Connection pool settings
db_pool_min = db_config.pool_min
db_pool_max = db_config.pool_max
db_pool_timeout = db_config.pool_timeout
db_max_retries = 3
db_retry_delay = 0.5  # seconds

# Connection strings
sync_connection_url = f"postgresql+psycopg2://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_dbname}"
async_connection_url = f"postgresql+asyncpg://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_dbname}"

# For development, show SQL queries (disable in production for better performance)
echo_sql = config.env != "production"

# Initialize sync engine and session factory
sync_engine = create_engine(
    sync_connection_url,
    echo=echo_sql,
    pool_size=db_pool_min,
    max_overflow=db_pool_max - db_pool_min,
    pool_timeout=db_pool_timeout,
    pool_pre_ping=True,  # Check connection health before use
    pool_recycle=db_config.pool_recycle,  # Recycle connections every 30 minutes
)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Initialize async engine and session factory
async_engine = create_async_engine(
    async_connection_url,
    echo=echo_sql,
    pool_size=db_config.pool_size,
    max_overflow=db_config.max_overflow,
    pool_pre_ping=True,
    pool_recycle=db_config.pool_recycle,
)
# Using bind instead of engine parameter for compatibility
AsyncSessionLocal = async_sessionmaker(bind=async_engine, expire_on_commit=False)

# Raw connection pools
psycopg2_pool = pool.ThreadedConnectionPool(
    minconn=db_pool_min,
    maxconn=db_pool_max,
    user=postgres_user,
    password=postgres_password,
    host=postgres_host,
    port=postgres_port,
    dbname=postgres_dbname,
)

# Global async connection pool
_asyncpg_pool = None

# Type for retry mechanism
F = TypeVar("F", bound=Callable[..., Any])

# =====================================
# Utility Functions and Decorators
# =====================================


def with_db_retry(
    max_retries: int = db_max_retries, delay: float = db_retry_delay
) -> Callable[[F], F]:
    """
    Decorator to retry database operations on connection errors.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error = None
            for attempt in range(1, max_retries + 2):  # +2 for base case + retries
                try:
                    return func(*args, **kwargs)
                except (OperationalError, SQLAlchemyError) as e:
                    last_error = e
                    # Only retry on connection errors, not query errors
                    if (
                        "connection" not in str(e).lower()
                        and "timeout" not in str(e).lower()
                    ):
                        raise

                    if attempt <= max_retries:
                        sleep_time = delay * attempt  # Exponential backoff
                        logger.warning(
                            f"Database connection error: {e}. Retrying in {sleep_time:.1f}s (attempt {attempt}/{max_retries})"
                        )
                        time.sleep(sleep_time)
                    else:
                        break

            # If we get here, all retries failed
            logger.error(
                f"Database operation failed after {max_retries} retries: {last_error}"
            )
            raise last_error

        return cast(F, wrapper)

    return decorator


async def with_async_db_retry(
    coro_func, max_retries=db_max_retries, delay=db_retry_delay, *args, **kwargs
):
    """
    Retry async database operations on connection errors.

    Args:
        coro_func: Async function to execute
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        args, kwargs: Arguments to pass to coro_func

    Returns:
        Result of coro_func

    Raises:
        The last exception encountered if all retries fail
    """
    import asyncio

    last_error = None
    for attempt in range(1, max_retries + 2):  # +2 for base case + retries
        try:
            return await coro_func(*args, **kwargs)
        except Exception as e:
            last_error = e
            # Only retry on connection errors
            if not any(
                err_msg in str(e).lower()
                for err_msg in [
                    "connection",
                    "timeout",
                    "terminated",
                    "reset",
                    "broken pipe",
                ]
            ):
                raise

            if attempt <= max_retries:
                sleep_time = delay * attempt  # Exponential backoff
                logger.warning(
                    f"Async database error: {e}. Retrying in {sleep_time:.1f}s (attempt {attempt}/{max_retries})"
                )
                await asyncio.sleep(sleep_time)
            else:
                break

    # If we get here, all retries failed
    logger.error(
        f"Async database operation failed after {max_retries} retries: {last_error}"
    )
    raise last_error


# =====================================
# Synchronous Database Access
# =====================================


class PostgresDB:
    """
    Synchronous PostgreSQL database access with connection pooling.

    Provides standardized methods for database access with proper
    connection management and resource cleanup.
    """

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """
        Context manager for SQLAlchemy sessions.

        Yields:
            SQLAlchemy session with automatic commit/rollback

        Example:
            ```python
            with postgres_db.session() as session:
                users = session.query(User).all()
            ```
        """
        session = SyncSessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def connection(
        self, dict_cursor: bool = True
    ) -> Generator[tuple[Any, Any], None, None]:
        """
        Get a raw database connection and cursor with automatic cleanup.

        Args:
            dict_cursor: Use dictionary cursor if True, regular cursor if False

        Yields:
            Tuple of (connection, cursor) with automatic cleanup

        Example:
            ```python
            with postgres_db.connection() as (conn, cursor):
                cursor.execute("SELECT * FROM users WHERE id = %s", [user_id])
                user = cursor.fetchone()
            ```
        """
        conn = None
        cursor = None
        try:
            conn = psycopg2_pool.getconn()

            # Create the appropriate cursor type
            if dict_cursor:
                cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
            else:
                cursor = conn.cursor()

            yield conn, cursor
            conn.commit()
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                psycopg2_pool.putconn(conn)

    @with_db_retry()
    def execute_query(
        self, sql: str, params: Optional[list[Any]] = None, fetch: bool = True
    ) -> list[dict[str, Any]]:
        """
        Execute SQL query and return results as dictionaries.

        Args:
            sql: SQL query string
            params: Query parameters
            fetch: Whether to fetch and return results

        Returns:
            Query results as list of dictionaries

        Example:
            ```python
            users = postgres_db.execute_query("SELECT * FROM users WHERE status = %s", ["active"])
            ```
        """
        with self.connection() as (conn, cursor):
            cursor.execute(sql, params or [])
            if fetch:
                return cursor.fetchall()
            return []

    @with_db_retry()
    def execute_batch(self, sql: str, params_list: list[list[Any]]) -> int:
        """
        Execute the same SQL query with different parameters in a batch.

        Args:
            sql: SQL query string
            params_list: List of parameter lists

        Returns:
            Number of rows affected

        Example:
            ```python
            params_list = [
                ["John", "Doe", "john@example.com"],
                ["Jane", "Smith", "jane@example.com"]
            ]
            postgres_db.execute_batch(
                "INSERT INTO users (first_name, last_name, email) VALUES (%s, %s, %s)",
                params_list
            )
            ```
        """
        with self.connection() as (conn, cursor):
            extras.execute_batch(cursor, sql, params_list)
            return cursor.rowcount

    @with_db_retry()
    def get_schemas(self) -> list[dict[str, Any]]:
        """
        Get database schema information including tables and their columns.

        Returns:
            List of dictionaries with table schema information
        """
        with self.connection() as (conn, cursor):
            # Get all tables in the public schema
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public';
            """)

            tables = cursor.fetchall()
            table_list = [table["table_name"] for table in tables]

            result = []
            for table in table_list:
                # Get column information for each table
                cursor.execute(
                    """
                    SELECT 
                        c.table_schema as table_schema,
                        c.table_name as table_name,
                        c.column_name as column,
                        c.udt_name as type,
                        c.is_nullable as nullable
                    FROM 
                        information_schema.columns c
                    WHERE 
                        c.table_schema = 'public' AND c.table_name = %s
                    ORDER BY 
                        c.ordinal_position;
                """,
                    [table],
                )

                rows = cursor.fetchall()
                fields = [
                    {
                        "column": row["column"],
                        "type": row["type"],
                        "nullable": row["nullable"],
                    }
                    for row in rows
                ]

                result.append(
                    {
                        "name": table,
                        "fields": fields,
                    }
                )

            return result

    @with_db_retry()
    def check_health(self) -> dict[str, Any]:
        """
        Check database health and connection status.

        Returns:
            Dictionary with health check results
        """
        start_time = time.time()
        try:
            with self.connection() as (conn, cursor):
                cursor.execute("SELECT version(), current_timestamp")
                info = cursor.fetchone()

                # Also check SQLAlchemy engine
                with self.session() as session:
                    result = session.execute(text("SELECT 1")).scalar()

                return {
                    "status": "healthy" if result == 1 else "degraded",
                    "message": "Database connection successful",
                    "version": info["version"],
                    "server_time": info["current_timestamp"],
                    "response_time_ms": int((time.time() - start_time) * 1000),
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {e!s}",
                "response_time_ms": int((time.time() - start_time) * 1000),
            }


# =====================================
# Asynchronous Database Access
# =====================================


class AsyncPostgresDB:
    """
    Asynchronous PostgreSQL database access with connection pooling.

    Provides high-performance non-blocking database operations.
    """

    def __init__(self):
        """Initialize AsyncPostgresDB"""
        self._pool = _asyncpg_pool
        self._init_kwargs = {
            "user": postgres_user,
            "password": postgres_password,
            "host": postgres_host,
            "port": postgres_port,
            "database": postgres_dbname,
            "min_size": db_pool_min,
            "max_size": db_pool_max,
            "timeout": db_pool_timeout,
            "command_timeout": 60.0,
        }

    async def _ensure_pool(self):
        """Ensure connection pool exists"""
        global _asyncpg_pool

        # Use the global pool if available
        if _asyncpg_pool is not None:
            self._pool = _asyncpg_pool
            return

        # Only create a new pool if necessary
        if self._pool is None:
            try:
                self._pool = await asyncpg.create_pool(**self._init_kwargs)
                _asyncpg_pool = self._pool
            except Exception as e:
                logger.error(f"Failed to create async PostgreSQL pool: {e!s}")
                raise DatabaseError(f"PostgreSQL connection error: {e!s}")

    @asynccontextmanager
    async def connection(self):
        """
        Get a raw asyncpg connection with automatic resource management.

        Yields:
            asyncpg.Connection: Direct asyncpg connection

        Example:
            ```python
            async with async_postgres.connection() as conn:
                result = await conn.fetch("SELECT * FROM users")
            ```
        """
        await self._ensure_pool()
        conn = await self._pool.acquire()
        try:
            yield conn
        except Exception as e:
            logger.error(f"Async database connection error: {e!s}")
            raise DatabaseError(f"Database query error: {e!s}")
        finally:
            await self._pool.release(conn)

    async def execute_query(
        self, query: str, params: list[Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Execute SQL query with parameters and return results as dictionaries.

        Args:
            query: SQL query string
            params: Query parameters as a list

        Returns:
            List of dictionaries representing the query results
        """

        async def _execute():
            await self._ensure_pool()
            async with self._pool.acquire() as conn:
                if params:
                    result = await conn.fetch(query, *params)
                else:
                    result = await conn.fetch(query)
                return [dict(row) for row in result]

        try:
            return await with_async_db_retry(_execute)
        except Exception as e:
            logger.error(f"Failed to execute async query: {e!s}")
            raise DatabaseError(f"Query execution failed: {e!s}")

    async def execute_script(self, script: str) -> bool:
        """
        Execute a SQL script with multiple statements.

        Args:
            script: SQL script string with multiple statements

        Returns:
            True if execution is successful
        """

        async def _execute_script():
            await self._ensure_pool()
            async with self._pool.acquire() as conn:
                # Split the script and execute each command
                commands = script.split(";")
                async with conn.transaction():
                    for cmd in commands:
                        cmd = cmd.strip()
                        if cmd:  # Skip empty commands
                            await conn.execute(cmd)
                return True

        try:
            return await with_async_db_retry(_execute_script)
        except Exception as e:
            logger.error(f"SQL script execution error: {e!s}")
            raise DatabaseError(f"Failed to execute SQL script: {e!s}")

    async def check_health(self) -> dict[str, Any]:
        """
        Check async database connection health.

        Returns:
            Dictionary with health check results
        """
        start_time = time.time()
        try:
            await self._ensure_pool()

            async with self._pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                timestamp = await conn.fetchval("SELECT current_timestamp")

                return {
                    "status": "healthy",
                    "message": "Async database connection successful",
                    "version": version,
                    "server_time": str(timestamp),
                    "response_time_ms": int((time.time() - start_time) * 1000),
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Async database connection failed: {e!s}",
                "response_time_ms": int((time.time() - start_time) * 1000),
            }


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session using async context manager pattern.

    This is the preferred way to get a session for most async database operations.

    Yields:
        AsyncSession: SQLAlchemy async session

    Example:
        ```python
        async with get_async_session() as session:
            result = await session.execute(select(User))
        ```
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Database session error: {e!s}")
        raise DatabaseError(f"Database session error: {e!s}")
    finally:
        await session.close()


async def get_async_session_direct() -> AsyncSession:
    """
    Get a database session directly without using a context manager.
    
    IMPORTANT: The caller is responsible for committing/rolling back
    and closing the session when done.
    
    Returns:
        AsyncSession: SQLAlchemy async session

    Example:
        ```python
        session = await get_async_session_direct()
        try:
            result = await session.execute(select(User))
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
        ```
    """
    return AsyncSessionLocal()


# =====================================
# Lifecycle Management
# =====================================


async def init_database() -> bool:
    """
    Initialize database connections and verify functionality.

    This function should be called during application startup.

    Returns:
        bool: True if initialization is successful

    Raises:
        DatabaseError: If database initialization fails
    """
    global _asyncpg_pool

    logger.info(
        f"Initializing database connections to {postgres_host}:{postgres_port}/{postgres_dbname}"
    )

    try:
        # Initialize the async connection pool
        _asyncpg_pool = await asyncpg.create_pool(
            user=postgres_user,
            password=postgres_password,
            host=postgres_host,
            port=postgres_port,
            database=postgres_dbname,
            min_size=db_pool_min,
            max_size=db_pool_max,
            timeout=10.0,
            command_timeout=60.0,
        )

        # Test both sync and async connections
        sync_db = PostgresDB()
        sync_health = sync_db.check_health()

        async_db = AsyncPostgresDB()
        async_health = await async_db.check_health()

        if sync_health["status"] != "healthy" or async_health["status"] != "healthy":
            logger.warning(
                f"Database health check issues: Sync={sync_health['status']}, Async={async_health['status']}"
            )

        logger.info("Database connections initialized successfully")
        return True

    except Exception as e:
        logger.critical(f"Database initialization failed: {e}")
        raise DatabaseError(f"Database initialization failed: {e}")


async def close_database() -> bool:
    """
    Close all database connections properly.

    This function should be called during application shutdown.

    Returns:
        bool: True if cleanup is successful
    """
    global _asyncpg_pool

    try:
        # Close asyncpg pool
        if _asyncpg_pool:
            await _asyncpg_pool.close()
            _asyncpg_pool = None
            logger.info("AsyncPG connection pool closed")

        # Close SQLAlchemy engines
        await async_engine.dispose()
        sync_engine.dispose()
        logger.info("SQLAlchemy engines disposed")

        # Note: psycopg2_pool will be cleaned up by Python's garbage collector
        # since we can't explicitly close it without risking errors if it's in use

        return True
    except Exception as e:
        logger.error(f"Error during database shutdown: {e}")
        return False


# =====================================
# Dependency Injection Functions
# =====================================

# Create singleton instances
postgres_db = PostgresDB()
async_postgres_db = AsyncPostgresDB()


def get_db() -> PostgresDB:
    """
    Get synchronous PostgreSQL database instance.

    Returns:
        PostgresDB instance
    """
    return postgres_db


def get_async_db() -> AsyncPostgresDB:
    """
    Get asynchronous PostgreSQL database instance.

    Returns:
        AsyncPostgresDB instance
    """
    return async_postgres_db


def get_db_session() -> Generator[Session, None, None]:
    """
    Get a SQLAlchemy database session for sync operations.

    Yields:
        SQLAlchemy Session
    """
    with postgres_db.session() as session:
        yield session


async def execute_sql_script(script: str) -> bool:
    """
    Execute a SQL script with multiple statements.

    Args:
        script: SQL script string with multiple statements

    Returns:
        bool: True if execution is successful
    """
    db = AsyncPostgresDB()
    return await db.execute_script(script)
