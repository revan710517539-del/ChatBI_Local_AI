"""
MySQL database adapter.

This module provides an adapter for MySQL databases, implementing
the DatabaseAdapter interface.
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple

import aiomysql
from loguru import logger

from chatbi.database.drivers.base import (
    ConnectionInfo,
    DatabaseAdapter,
    QueryResult,
    SchemaMetadata,
)
from chatbi.database.drivers.factory import register_adapter
from chatbi.domain.datasource import DatabaseType
from chatbi.exceptions import DatabaseError


@register_adapter(DatabaseType.MYSQL)
class MySqlAdapter(DatabaseAdapter):
    """MySQL database adapter implementation."""

    def __init__(self):
        """Initialize the MySQL adapter with no active connections."""
        self.conn = None
        self.pool = None
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        """Check if the adapter has an active connection."""
        return self._is_connected and (self.conn is not None or self.pool is not None)

    async def connect(self, connection_info: ConnectionInfo) -> None:
        """
        Establish a connection to the MySQL database.

        Args:
            connection_info: MySQL connection parameters

        Raises:
            DatabaseError: If connection fails
        """
        try:
            self.pool = await aiomysql.create_pool(
                host=connection_info.get("host"),
                port=connection_info.get("port", 3306),
                user=connection_info.get("user"),
                password=connection_info.get("password"),
                db=connection_info.get("database"),
                maxsize=connection_info.get("pool_size", 5),
                connect_timeout=connection_info.get("connect_timeout", 10),
            )
            self._is_connected = True
        except Exception as e:
            logger.error(f"MySQL connection error: {e!s}")
            raise DatabaseError(f"Failed to connect to MySQL: {e!s}")

    async def test_connection(
        self, connection_info: ConnectionInfo
    ) -> tuple[bool, str, Optional[dict[str, Any]]]:
        """
        Test a MySQL database connection without storing it.

        Args:
            connection_info: MySQL connection parameters

        Returns:
            Tuple of (success, message, details)
        """
        try:
            # Create a temporary connection for testing
            conn = await aiomysql.connect(
                host=connection_info.get("host"),
                port=connection_info.get("port", 3306),
                user=connection_info.get("user"),
                password=connection_info.get("password"),
                db=connection_info.get("database"),
                connect_timeout=5,
            )

            async with conn.cursor() as cursor:
                # Test query to get server version
                await cursor.execute("SELECT VERSION()")
                version_row = await cursor.fetchone()
                version = version_row[0] if version_row else "Unknown"

                # Get current timestamp
                await cursor.execute("SELECT NOW()")
                timestamp_row = await cursor.fetchone()
                server_time = timestamp_row[0] if timestamp_row else None

            conn.close()

            return (
                True,
                "Connection successful",
                {
                    "version": version,
                    "server_time": server_time.isoformat() if server_time else None,
                },
            )

        except Exception as e:
            logger.error(f"MySQL connection test error: {e!s}")
            return False, f"MySQL connection error: {e!s}", None

    async def execute_query(
        self,
        connection_info: ConnectionInfo,
        query: str,
        timeout: int = 30,
        max_rows: int = 1000,
        parameters: Optional[dict[str, Any]] = None,
    ) -> QueryResult:
        """
        Execute a query on the MySQL database.

        Args:
            connection_info: MySQL connection parameters
            query: SQL query to execute
            timeout: Query timeout in seconds
            max_rows: Maximum rows to return
            parameters: Optional query parameters

        Returns:
            Query result with columns, rows and metadata

        Raises:
            DatabaseError: If query execution fails
        """
        try:
            # Create a temporary connection
            conn = await aiomysql.connect(
                host=connection_info.get("host"),
                port=connection_info.get("port", 3306),
                user=connection_info.get("user"),
                password=connection_info.get("password"),
                db=connection_info.get("database"),
                connect_timeout=5,
            )

            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # Set the query timeout
                await cursor.execute(
                    f"SET SESSION MAX_EXECUTION_TIME = {timeout * 1000}"
                )

                # Prepare the query parameters if provided
                if parameters:
                    # Replace named parameters in the query
                    # MySQL uses %s for parameters, but we need to convert the dict to a tuple
                    param_names = []
                    param_values = []

                    for param_name, param_value in parameters.items():
                        # Replace named parameters in the query with %s
                        query = query.replace(f":{param_name}", "%s")
                        query = query.replace(f"@{param_name}", "%s")
                        param_names.append(param_name)
                        param_values.append(param_value)

                    # Execute the query with parameters
                    await cursor.execute(query, tuple(param_values))
                else:
                    # Execute without parameters
                    await cursor.execute(query)

                # Get column definitions
                columns = []
                if cursor.description:
                    for col in cursor.description:
                        columns.append({"name": col[0], "type": str(col[1])})

                # Fetch rows
                rows = []
                truncated = False

                count = 0
                async for row in cursor:
                    if count >= max_rows:
                        truncated = True
                        break
                    rows.append(dict(row))
                    count += 1

                conn.close()

                return {"columns": columns, "rows": rows, "truncated": truncated}

        except Exception as e:
            logger.error(f"MySQL query execution error: {e!s}")
            raise DatabaseError(f"Failed to execute MySQL query: {e!s}")

    async def get_schema_metadata(
        self, connection_info: ConnectionInfo
    ) -> SchemaMetadata:
        """
        Get MySQL database schema metadata.

        Args:
            connection_info: MySQL connection parameters

        Returns:
            Schema metadata including tables, views, and columns

        Raises:
            DatabaseError: If metadata retrieval fails
        """
        try:
            conn = await aiomysql.connect(
                host=connection_info.get("host"),
                port=connection_info.get("port", 3306),
                user=connection_info.get("user"),
                password=connection_info.get("password"),
                db=connection_info.get("database"),
                connect_timeout=10,
            )

            current_database = connection_info.get("database")

            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # Get schemas (in MySQL, schemas are databases)
                await cursor.execute("SHOW DATABASES")
                schema_rows = await cursor.fetchall()
                schemas = [
                    row["Database"]
                    for row in schema_rows
                    if row["Database"]
                    not in ["information_schema", "mysql", "performance_schema", "sys"]
                ]

                # Get tables
                await cursor.execute(
                    """
                    SELECT 
                        TABLE_SCHEMA as `schema`,
                        TABLE_NAME as name,
                        TABLE_COMMENT as description,
                        TABLE_TYPE as type
                    FROM information_schema.TABLES
                    WHERE TABLE_SCHEMA = %s
                    ORDER BY TABLE_SCHEMA, TABLE_NAME
                """,
                    (current_database,),
                )

                table_rows = await cursor.fetchall()

                tables = []
                views = []

                for table in table_rows:
                    # Get columns for this table
                    await cursor.execute(
                        """
                        SELECT 
                            COLUMN_NAME as name,
                            DATA_TYPE as type,
                            COLUMN_DEFAULT as default_value,
                            IS_NULLABLE as is_nullable,
                            COLUMN_COMMENT as description
                        FROM information_schema.COLUMNS
                        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                        ORDER BY ORDINAL_POSITION
                    """,
                        (table["schema"], table["name"]),
                    )

                    columns = await cursor.fetchall()

                    table_info = {
                        "schema": table["schema"],
                        "name": table["name"],
                        "description": table["description"],
                        "column_count": len(columns),
                        "columns": [dict(col) for col in columns],
                    }

                    if table["type"] == "BASE TABLE":
                        tables.append(table_info)
                    elif table["type"] == "VIEW":
                        views.append(table_info)

            conn.close()

            return {"tables": tables, "views": views, "schemas": schemas}

        except Exception as e:
            logger.error(f"MySQL schema metadata retrieval error: {e!s}")
            raise DatabaseError(f"Failed to retrieve MySQL schema metadata: {e!s}")

    async def close(self) -> None:
        """
        Close the MySQL database connection.

        Raises:
            DatabaseError: If connection cannot be closed properly
        """
        try:
            if self.conn:
                self.conn.close()
                self.conn = None

            if self.pool:
                self.pool.close()
                await self.pool.wait_closed()
                self.pool = None

            self._is_connected = False

        except Exception as e:
            logger.error(f"MySQL connection close error: {e!s}")
            raise DatabaseError(f"Failed to close MySQL connection: {e!s}")
