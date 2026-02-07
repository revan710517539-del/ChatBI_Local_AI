"""
DuckDB database adapter.

This module provides an adapter for DuckDB databases, implementing
the DatabaseAdapter interface.
"""

import os
from contextlib import contextmanager
from typing import Any, Optional

import duckdb
from loguru import logger

from chatbi.database.drivers.base import (
    ConnectionInfo,
    DatabaseAdapter,
    QueryResult,
    SchemaMetadata,
)
from chatbi.database.drivers.factory import register_adapter
from chatbi.domain.datasource.dtos import DatabaseType
from chatbi.exceptions import DatabaseError


@register_adapter(DatabaseType.DUCKDB)
class DuckDBAdapter(DatabaseAdapter):
    """DuckDB database adapter implementation."""

    def __init__(self):
        """Initialize the DuckDB adapter with no active connection."""
        self.conn = None
        self.db_path = None
        self.is_connected = False

    async def connect(self, connection_info: ConnectionInfo) -> None:
        """
        Establish a connection to the DuckDB database.

        Args:
            connection_info: DuckDB connection parameters

        Raises:
            DatabaseError: If connection fails
        """
        try:
            database_path = connection_info.get("path", ":memory:")
            self.db_path = database_path

            # Create directory if it doesn't exist
            if database_path != ":memory:":
                directory = os.path.dirname(database_path)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)

            self.conn = duckdb.connect(database=database_path, read_only=False)

            # Apply optimization settings
            self._configure_connection()

            self.is_connected = True
            logger.info(f"Connected to DuckDB database: {database_path}")

        except Exception as e:
            self.is_connected = False
            logger.error(f"DuckDB connection error: {e!s}")
            raise DatabaseError(f"Failed to connect to DuckDB: {e!s}")

    def _configure_connection(self) -> None:
        """Configure connection with optimization settings."""
        if not self.conn:
            return

        try:
            # Set memory limit to 4GB
            self.conn.execute("SET memory_limit='4GB'")

            # Set temporary directory
            temp_dir = "/tmp"
            if self.db_path != ":memory:":
                temp_dir = os.path.dirname(self.db_path)
            self.conn.execute(f"SET temp_directory='{temp_dir}'")

            # Enable object cache for improved performance
            self.conn.execute("SET enable_object_cache=true")

            # Optimize for analytics workloads
            self.conn.execute("PRAGMA threads=4")

        except Exception as e:
            logger.warning(f"Could not apply all DuckDB optimizations: {e!s}")

    @contextmanager
    def get_connection(self):
        """
        Get the current connection or create a new one if needed.

        Returns:
            A DuckDB connection

        Raises:
            DatabaseError: If connection is not available
        """
        if not self.is_connected or not self.conn:
            if not self.db_path:
                raise DatabaseError("Not connected to any DuckDB database")

            try:
                self.conn = duckdb.connect(database=self.db_path, read_only=False)
                self._configure_connection()
                self.is_connected = True
            except Exception as e:
                raise DatabaseError(f"Failed to reconnect to DuckDB: {e!s}")

        try:
            yield self.conn
        except Exception as e:
            # Connection error might require reconnection next time
            if "connection" in str(e).lower():
                self.is_connected = False
                self.conn = None
            raise

    async def test_connection(
        self, connection_info: ConnectionInfo
    ) -> tuple[bool, str, Optional[dict[str, Any]]]:
        """
        Test if a connection to DuckDB can be established.

        Args:
            connection_info: DuckDB connection parameters

        Returns:
            A tuple with:
            - Boolean indicating success
            - Status message
            - Connection information (if successful)
        """
        try:
            database_path = connection_info.get("path", ":memory:")

            # Verify database file or create directory if needed
            if database_path != ":memory:" and not database_path.startswith(":"):
                directory = os.path.dirname(database_path)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)

            # Test connection with a temporary connection
            conn = duckdb.connect(database=database_path, read_only=False)

            # Apply basic settings
            conn.execute("SET memory_limit='1GB'")
            conn.execute("PRAGMA threads=2")

            # Run a simple query to verify the connection works
            current_time = conn.execute("SELECT current_timestamp").fetchone()[0]

            # Get version info
            version = conn.execute("SELECT version()").fetchone()[0]

            # Close temp connection
            conn.close()

            return (
                True,
                "Connection successful",
                {
                    "version": version,
                    "server_time": (current_time.isoformat() if current_time else None),
                },
            )

        except Exception as e:
            logger.error(f"DuckDB connection test error: {e!s}")
            return False, f"DuckDB connection error: {e!s}", None

    async def execute_query(
        self,
        connection_info: ConnectionInfo,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
        timeout: int = 30,
        max_rows: int = 1000,
    ) -> QueryResult:
        """
        Execute a query in the DuckDB database.

        Args:
            connection_info: DuckDB connection parameters (unused, kept for interface compatibility)
            query: SQL query to execute
            parameters: Query parameters
            timeout: Query timeout in seconds
            max_rows: Maximum rows to return

        Returns:
            QueryResult containing columns and data
        """
        with self.get_connection() as conn:
            try:
                # Some DuckDB builds don't support statement_timeout_ms; ignore if unavailable.
                try:
                    conn.execute(f"SET statement_timeout_ms={timeout * 1000}")
                except Exception:
                    pass

                # Prepare query parameters if provided
                prepared_query = query.strip().rstrip(";")
                if parameters:
                    # DuckDB uses $ for parameter placeholders
                    for param_name, param_value in parameters.items():
                        # Replace both :param and @param formats with $param
                        prepared_query = prepared_query.replace(
                            f":{param_name}", f"${param_name}"
                        )
                        prepared_query = prepared_query.replace(
                            f"@{param_name}", f"${param_name}"
                        )

                    # Execute the query with parameters
                    result = conn.execute(prepared_query, parameters)
                else:
                    # Execute the query without parameters
                    result = conn.execute(prepared_query)

                # Fetch rows with truncation detection
                raw_rows = result.fetchmany(max_rows + 1)  # Get one extra row
                truncated = len(raw_rows) > max_rows

                # Get column information without running extra SQL on the same cursor.
                columns = []
                column_names: list[str] = []
                for desc in result.description:
                    col_name = desc[0] if isinstance(desc, tuple) else str(desc)
                    col_type = str(desc[1]) if isinstance(desc, tuple) and len(desc) > 1 else "UNKNOWN"
                    column_names.append(col_name)
                    columns.append({"name": col_name, "type": col_type})

                # Format rows as dicts keyed by column name for cross-adapter consistency.
                rows = [
                    {column_names[i]: row[i] for i in range(len(column_names))}
                    for row in raw_rows[:max_rows]
                ]

                return QueryResult(
                    columns=columns, rows=rows, truncated=truncated, error=None
                )

            except Exception as e:
                logger.error(f"DuckDB query execution error: {e!s}")
                raise DatabaseError(f"Failed to execute DuckDB query: {e!s}")

    async def get_schema_metadata(
        self, connection_info: ConnectionInfo
    ) -> SchemaMetadata:
        """
        Retrieve database schema metadata.

        Args:
            connection_info: Connection parameters

        Returns:
            Schema metadata with tables, columns, etc.
        """
        with self.get_connection() as conn:
            try:
                # Get schemas
                schema_query = "SELECT schema_name FROM information_schema.schemata"
                schema_rows = conn.execute(schema_query).fetchall()

                schemas = [
                    row[0]
                    for row in schema_rows
                    if row[0] not in ["information_schema", "pg_catalog"]
                ]

                # If no custom schemas found, use 'main'
                if not schemas:
                    schemas = ["main"]

                all_tables = {}

                # For each schema, get table info
                for schema in schemas:
                    tables_query = f"""
                        SELECT 
                            table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = '{schema}'
                    """

                    table_rows = conn.execute(tables_query).fetchall()

                    for table_row in table_rows:
                        table_name = table_row[0]

                        # Get column info for each table
                        columns_query = f"""
                            SELECT
                                column_name as name,
                                data_type as type,
                                is_nullable
                            FROM information_schema.columns
                            WHERE table_schema = '{schema}'
                            AND table_name = '{table_name}'
                        """

                        column_rows = conn.execute(columns_query).fetchall()
                        columns = []

                        for col in column_rows:
                            columns.append(
                                {
                                    "name": col[0],
                                    "type": col[1],
                                    "nullable": col[2] == "YES",
                                }
                            )

                        # Store table with its columns
                        full_name = f"{schema}.{table_name}"
                        all_tables[full_name] = {
                            "name": table_name,
                            "schema": schema,
                            "columns": columns,
                            "primary_keys": [],  # DuckDB doesn't expose this easily
                            "foreign_keys": [],  # DuckDB doesn't expose this easily
                        }

                return SchemaMetadata(tables=all_tables)

            except Exception as e:
                logger.error(f"DuckDB schema metadata retrieval error: {e!s}")
                raise DatabaseError(f"Failed to retrieve DuckDB schema metadata: {e!s}")

    async def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            try:
                self.conn.close()
                self.is_connected = False
                self.conn = None
                logger.info("Closed DuckDB connection")
            except Exception as e:
                logger.error(f"DuckDB connection close error: {e!s}")
                raise DatabaseError(f"Failed to close DuckDB connection: {e!s}")
