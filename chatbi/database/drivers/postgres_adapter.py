"""
PostgreSQL database adapter.

This module provides an adapter for PostgreSQL databases, implementing
the DatabaseAdapter interface.
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple

import asyncpg
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


@register_adapter(DatabaseType.POSTGRES)
class PostgresAdapter(DatabaseAdapter):
    """PostgreSQL database adapter implementation."""

    def __init__(self):
        """Initialize the PostgreSQL adapter with no active connections."""
        self.conn = None
        self.pool = None
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        """Check if the adapter has an active connection."""
        return self._is_connected and (self.conn is not None or self.pool is not None)

    def _extract_conn_params(self, connection_info: ConnectionInfo) -> Dict[str, Any]:
        """Extract connection parameters from ConnectionInfo object or dict."""
        def get_val(key, default=None):
            if hasattr(connection_info, key):
                val = getattr(connection_info, key)
            elif isinstance(connection_info, dict):
                val = connection_info.get(key, default)
            else:
                val = default
            
            if hasattr(val, "get_secret_value"):
                return val.get_secret_value()
            return val
            
        return {
            "host": get_val("host"),
            "port": int(get_val("port", 5432)),
            "user": get_val("user"),
            "password": get_val("password"),
            "database": get_val("database"),
            "min_size": int(get_val("pool_size", 1)),
            "max_size": int(get_val("pool_limit", 5)),
            "connect_timeout": float(get_val("connect_timeout", 10.0)),
        }

    async def connect(self, connection_info: ConnectionInfo) -> None:
        """
        Establish a connection to the PostgreSQL database.

        Args:
            connection_info: PostgreSQL connection parameters

        Raises:
            DatabaseError: If connection fails
        """
        params = self._extract_conn_params(connection_info)
        
        try:
            self.pool = await asyncpg.create_pool(
                host=params["host"],
                port=params["port"],
                user=params["user"],
                password=params["password"],
                database=params["database"],
                min_size=params["min_size"],
                max_size=params["max_size"],
                command_timeout=params["connect_timeout"],
            )
            self._is_connected = True
        except Exception as e:
            logger.error(f"PostgreSQL connection error: {e!s}")
            from chatbi.exceptions import DatabaseError
            raise DatabaseError(detail=f"Failed to connect to PostgreSQL: {e!s}")

    async def test_connection(
        self, connection_info: ConnectionInfo
    ) -> tuple[bool, str, Optional[dict[str, Any]]]:
        """
        Test a PostgreSQL database connection without storing it.

        Args:
            connection_info: PostgreSQL connection parameters

        Returns:
            Tuple of (success, message, details)
        """
        params = self._extract_conn_params(connection_info)
        
        try:
            # Create a temporary connection for testing
            conn = await asyncpg.connect(
                host=params["host"],
                port=params["port"],
                user=params["user"],
                password=params["password"],
                database=params["database"],
                timeout=5.0,
            )

            # Test query to get server version
            version_row = await conn.fetchrow("SELECT version()")
            version = version_row[0] if version_row else "Unknown"

            # Get current timestamp
            timestamp_row = await conn.fetchrow("SELECT NOW()")
            server_time = timestamp_row[0] if timestamp_row else None

            await conn.close()

            return (
                True,
                "Connection successful",
                {
                    "version": version,
                    "server_time": server_time.isoformat() if server_time else None,
                },
            )

        except Exception as e:
            logger.error(f"PostgreSQL connection test error: {e!s}")
            return False, f"PostgreSQL connection error: {e!s}", None

    async def execute_query(
        self,
        connection_info: ConnectionInfo,
        query: str,
        timeout: int = 30,
        max_rows: int = 1000,
        parameters: Optional[dict[str, Any]] = None,
    ) -> QueryResult:
        """
        Execute a query on the PostgreSQL database.

        Args:
            connection_info: PostgreSQL connection parameters
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
            conn_params = self._extract_conn_params(connection_info)
            # Create a temporary connection
            conn = await asyncpg.connect(
                host=conn_params["host"],
                port=conn_params["port"],
                user=conn_params["user"],
                password=conn_params["password"],
                database=conn_params["database"],
                timeout=5.0,
                command_timeout=float(timeout),
            )
            try:
                # Prepare the query parameters if provided
                if parameters:
                    # Convert named parameters to positional parameters
                    # PostgreSQL uses $1, $2, etc. for positional parameters
                    param_values = []
                    for param_name, param_value in parameters.items():
                        # Replace named parameters in the query with positional ones
                        query = query.replace(
                            f":{param_name}", f"${len(param_values) + 1}"
                        )
                        query = query.replace(
                            f"@{param_name}", f"${len(param_values) + 1}"
                        )
                        param_values.append(param_value)

                    # Execute the query with the parameters
                    rows = await conn.fetch(query, *param_values)
                else:
                    # Execute without parameters
                    rows = await conn.fetch(query)

                # Get column definitions
                columns = []
                if rows:
                    # Get column definitions
                    for col_idx, col_name in enumerate(rows[0].keys()):
                        columns.append(
                            {
                                "name": col_name,
                                "type": str(type(rows[0][col_name]).__name__),
                            }
                        )

                # Convert rows to dictionaries
                result_rows = []
                truncated = False
                for idx, row in enumerate(rows):
                    if idx >= max_rows:
                        truncated = True
                        break
                    result_rows.append(dict(row))

                return {"columns": columns, "rows": result_rows, "truncated": truncated}
            finally:
                await conn.close()

        except Exception as e:
            logger.error(f"PostgreSQL query execution error: {e!s}")
            raise DatabaseError(f"Failed to execute PostgreSQL query: {e!s}")

    async def get_schema_metadata(
        self, connection_info: ConnectionInfo
    ) -> SchemaMetadata:
        """
        Get PostgreSQL database schema metadata.

        Args:
            connection_info: PostgreSQL connection parameters

        Returns:
            Schema metadata including tables, views, and columns

        Raises:
            DatabaseError: If metadata retrieval fails
        """
        try:
            conn_params = self._extract_conn_params(connection_info)
            conn = await asyncpg.connect(
                host=conn_params["host"],
                port=conn_params["port"],
                user=conn_params["user"],
                password=conn_params["password"],
                database=conn_params["database"],
                timeout=10.0,
            )
            try:
                # Get schemas
                schemas_query = """
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT LIKE 'pg_%' AND schema_name != 'information_schema'
                ORDER BY schema_name
                """
                schemas_rows = await conn.fetch(schemas_query)
                schemas = [row["schema_name"] for row in schemas_rows]

                # Get tables with their columns
                tables_query = """
                SELECT 
                    t.table_schema as schema,
                    t.table_name as name,
                    obj_description((t.table_schema || '.' || t.table_name)::regclass) as description,
                    (SELECT count(*) FROM information_schema.columns 
                        WHERE table_schema = t.table_schema AND table_name = t.table_name) as column_count
                FROM information_schema.tables t
                WHERE t.table_schema NOT LIKE 'pg_%' 
                  AND t.table_schema != 'information_schema'
                  AND t.table_type = 'BASE TABLE'
                ORDER BY t.table_schema, t.table_name
                """
                tables_rows = await conn.fetch(tables_query)

                tables = []
                for table in tables_rows:
                    # Get columns for each table
                    columns_query = """
                    SELECT 
                        column_name as name,
                        data_type as type,
                        column_default as default_value,
                        is_nullable,
                        col_description((table_schema || '.' || table_name)::regclass, ordinal_position) as description
                    FROM information_schema.columns
                    WHERE table_schema = $1 AND table_name = $2
                    ORDER BY ordinal_position
                    """
                    columns = await conn.fetch(
                        columns_query, table["schema"], table["name"]
                    )

                    tables.append(
                        {
                            "schema": table["schema"],
                            "name": table["name"],
                            "description": table["description"],
                            "column_count": table["column_count"],
                            "columns": [dict(col) for col in columns],
                        }
                    )

                # Get views
                views_query = """
                SELECT 
                    table_schema as schema,
                    table_name as name,
                    obj_description((table_schema || '.' || table_name)::regclass) as description
                FROM information_schema.views
                WHERE table_schema NOT LIKE 'pg_%' 
                  AND table_schema != 'information_schema'
                ORDER BY table_schema, table_name
                """
                views_rows = await conn.fetch(views_query)

                views = []
                for view in views_rows:
                    # Get columns for each view
                    columns_query = """
                    SELECT 
                        column_name as name,
                        data_type as type
                    FROM information_schema.columns
                    WHERE table_schema = $1 AND table_name = $2
                    ORDER BY ordinal_position
                    """
                    columns = await conn.fetch(
                        columns_query, view["schema"], view["name"]
                    )

                    views.append(
                        {
                            "schema": view["schema"],
                            "name": view["name"],
                            "description": view["description"],
                            "columns": [dict(col) for col in columns],
                        }
                    )

                return {"tables": tables, "views": views, "schemas": schemas}
            finally:
                await conn.close()

        except Exception as e:
            logger.error(f"PostgreSQL schema metadata retrieval error: {e!s}")
            raise DatabaseError(f"Failed to retrieve PostgreSQL schema metadata: {e!s}")

    async def close(self) -> None:
        """
        Close the PostgreSQL database connection.

        Raises:
            DatabaseError: If connection cannot be closed properly
        """
        try:
            if self.conn:
                await self.conn.close()
                self.conn = None

            if self.pool:
                await self.pool.close()
                self.pool = None

            self._is_connected = False

        except Exception as e:
            logger.error(f"PostgreSQL connection close error: {e!s}")
            raise DatabaseError(f"Failed to close PostgreSQL connection: {e!s}")
