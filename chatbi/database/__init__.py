"""
Database module for ChatBI.

This module provides a unified PostgreSQL database interface for both
synchronous and asynchronous operations with proper connection management.
"""

from chatbi.database.database import (
    AsyncPostgresDB,
    # Core database classes
    PostgresDB,
    close_database,
    # Utility functions
    execute_sql_script,
    # Asynchronous access functions
    get_async_db,
    get_async_session,
    # Synchronous access functions
    get_db,
    get_db_session,
    # Database lifecycle management
    init_database,
)

# Aliases for backward compatibility
from chatbi.database.database import AsyncPostgresDB as ConnectionManager

__all__ = [
    # Core database classes
    "PostgresDB",
    "AsyncPostgresDB",
    "ConnectionManager",  # Alias for backward compatibility
    # Synchronous access
    "get_db",
    "get_db_session",
    # Asynchronous access
    "get_async_db",
    "get_async_session",
    # Database lifecycle
    "init_database",
    "close_database",
    # Utilities
    "execute_sql_script",
]
