"""
Base database adapter interface definition.

This module defines the abstract base class that all database adapters must implement,
providing a consistent interface for different database types.
"""

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Protocol, Tuple, TypeVar, Union

from chatbi.domain.datasource import ConnectionInfo


class SchemaMetadata(dict[str, Any]):
    """Type definition for schema metadata returned by adapters."""


class QueryResult(dict[str, Any]):
    """Type definition for query execution results."""


class DatabaseAdapter(ABC):
    """
    Abstract base class for database adapters.

    Every database adapter must implement these methods to provide
    a consistent interface regardless of the underlying database technology.
    """

    def __init__(self):
        """Initialize the database adapter."""
        self.is_connected = False
        self.connection_hash = None

    @abstractmethod
    async def connect(self, connection_info: ConnectionInfo) -> None:
        """
        Establish a connection to the database.

        Args:
            connection_info: Database connection parameters

        Raises:
            DatabaseError: If connection fails
        """

    @abstractmethod
    async def test_connection(
        self, connection_info: ConnectionInfo
    ) -> tuple[bool, str, Optional[dict[str, Any]]]:
        """
        Test a database connection without storing it.

        Args:
            connection_info: Database connection parameters

        Returns:
            Tuple of (success, message, details)
        """

    @abstractmethod
    async def execute_query(
        self,
        connection_info: ConnectionInfo,
        query: str,
        timeout: int = 30,
        max_rows: int = 1000,
        parameters: Optional[Union[list[Any], dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """
        Execute a query on the database.

        Args:
            connection_info: Database connection parameters
            query: SQL query to execute
            timeout: Query timeout in seconds
            max_rows: Maximum rows to return
            parameters: Optional query parameters

        Returns:
            Query result with columns, rows and metadata

        Raises:
            DatabaseError: If query execution fails
        """

    @abstractmethod
    async def get_schema_metadata(
        self, connection_info: ConnectionInfo
    ) -> dict[str, Any]:
        """
        Get database schema metadata.

        Args:
            connection_info: Database connection parameters

        Returns:
            Schema metadata including tables, views, and columns

        Raises:
            DatabaseError: If metadata retrieval fails
        """

    @abstractmethod
    async def close(self) -> None:
        """
        Close the database connection and cleanup resources.

        Raises:
            DatabaseError: If connection cannot be closed properly
        """

    async def execute(
        self, query: str, params: Optional[Union[list[Any], dict[str, Any]]] = None
    ) -> list[dict[str, Any]]:
        """
        Execute a SQL query and return results as a list of dictionaries.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            List of dictionaries containing query results

        Raises:
            DatabaseError: If query execution fails
        """
        raise NotImplementedError(
            "This method must be implemented by subclasses that support direct execution"
        )

    @asynccontextmanager
    async def transaction(self):
        """
        Context manager for transaction handling.

        Usage:
            async with adapter.transaction():
                await adapter.execute(query1)
                await adapter.execute(query2)
        """
        raise NotImplementedError(
            "This method must be implemented by subclasses that support transactions"
        )

    async def get_tables(self) -> list[str]:
        """
        Get list of tables in the database.

        Returns:
            List of table names

        Raises:
            DatabaseError: If operation fails
        """
        raise NotImplementedError(
            "This method must be implemented by subclasses that support schema introspection"
        )

    async def get_table_schema(self, table_name: str) -> list[dict[str, Any]]:
        """
        Get schema information for a specific table.

        Args:
            table_name: Name of the table

        Returns:
            List of column definitions

        Raises:
            DatabaseError: If operation fails
        """
        raise NotImplementedError(
            "This method must be implemented by subclasses that support schema introspection"
        )
