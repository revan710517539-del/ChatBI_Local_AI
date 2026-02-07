"""
Core domain models for data source functionality.

This module defines the key business entities and value objects for data sources,
connection management, and database schema information.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from uuid import uuid4

from pydantic import SecretStr


class ConnectionType(str, Enum):
    """Types of database connections supported by the system."""

    POSTGRES = "postgres"
    MYSQL = "mysql"
    MSSQL = "mssql"
    SNOWFLAKE = "snowflake"
    BIGQUERY = "bigquery"
    CLICKHOUSE = "clickhouse"
    TRINO = "trino"
    DUCKDB = "duckdb"
    SQLITE = "sqlite"


class ColumnType(str, Enum):
    """Data types for database columns."""

    STRING = "string"
    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TIMESTAMP = "timestamp"
    TIME = "time"
    JSON = "json"
    ARRAY = "array"
    UUID = "uuid"
    BINARY = "binary"
    ENUM = "enum"
    UNKNOWN = "unknown"


class ColumnDefinition:
    """
    Value object representing a database column definition.
    """

    def __init__(
        self,
        name: str,
        data_type: ColumnType,
        nullable: bool = True,
        primary_key: bool = False,
        unique: bool = False,
        foreign_key: Optional[str] = None,
        description: Optional[str] = None,
        default_value: Optional[Any] = None,
        precision: Optional[int] = None,
        scale: Optional[int] = None,
        max_length: Optional[int] = None,
    ):
        self.name = name
        self.data_type = data_type
        self.nullable = nullable
        self.primary_key = primary_key
        self.unique = unique
        self.foreign_key = foreign_key
        self.description = description
        self.default_value = default_value
        self.precision = precision
        self.scale = scale
        self.max_length = max_length

    def to_dict(self) -> dict[str, Any]:
        """Convert column definition to dictionary representation."""
        result = {
            "name": self.name,
            "data_type": self.data_type.value,
            "nullable": self.nullable,
            "primary_key": self.primary_key,
            "unique": self.unique,
        }

        if self.foreign_key:
            result["foreign_key"] = self.foreign_key

        if self.description:
            result["description"] = self.description

        if self.default_value is not None:
            result["default_value"] = self.default_value

        if self.precision is not None:
            result["precision"] = self.precision

        if self.scale is not None:
            result["scale"] = self.scale

        if self.max_length is not None:
            result["max_length"] = self.max_length

        return result


class TableDefinition:
    """
    Value object representing a database table definition.
    """

    def __init__(
        self,
        name: str,
        schema: Optional[str] = None,
        columns: list[ColumnDefinition] | None = None,
        description: Optional[str] = None,
        primary_key: Optional[list[str]] = None,
        foreign_keys: Optional[dict[str, str]] = None,
        indexes: Optional[list[dict[str, Any]]] = None,
        row_count: Optional[int] = None,
    ):
        self.name = name
        self.schema = schema
        self.columns = columns or []
        self.description = description
        self.primary_key = primary_key or []
        self.foreign_keys = foreign_keys or {}
        self.indexes = indexes or []
        self.row_count = row_count

    def get_column(self, name: str) -> Optional[ColumnDefinition]:
        """Get a column by name."""
        for column in self.columns:
            if column.name == name:
                return column
        return None

    def get_primary_key_columns(self) -> list[ColumnDefinition]:
        """Get all primary key columns."""
        return [col for col in self.columns if col.primary_key]

    def get_full_table_name(self) -> str:
        """Get fully qualified table name."""
        if self.schema:
            return f"{self.schema}.{self.name}"
        return self.name

    def to_dict(self) -> dict[str, Any]:
        """Convert table definition to dictionary representation."""
        result = {
            "name": self.name,
            "columns": [col.to_dict() for col in self.columns],
        }

        if self.schema:
            result["schema"] = self.schema

        if self.description:
            result["description"] = self.description

        if self.primary_key:
            result["primary_key"] = self.primary_key

        if self.foreign_keys:
            result["foreign_keys"] = self.foreign_keys

        if self.indexes:
            result["indexes"] = self.indexes

        if self.row_count is not None:
            result["row_count"] = self.row_count

        return result


class DatabaseSchema:
    """
    Value object representing the schema of a database.

    Contains tables, views, and other database objects.
    """

    def __init__(
        self,
        name: str,
        tables: list[TableDefinition] | None = None,
        description: Optional[str] = None,
    ):
        self.name = name
        self.tables = tables or []
        self.description = description

    def get_table(self, name: str) -> Optional[TableDefinition]:
        """Get a table by name."""
        for table in self.tables:
            if table.name == name:
                return table
        return None

    def get_tables_with_schema(self, schema: str) -> list[TableDefinition]:
        """Get all tables in a specific schema."""
        return [table for table in self.tables if table.schema == schema]

    def to_dict(self) -> dict[str, Any]:
        """Convert database schema to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "tables": [table.to_dict() for table in self.tables],
        }


class ConnectionDetails:
    """
    Value object representing connection details for a data source.

    Contains the credentials and connection parameters needed to connect to a data source.
    Credentials are stored as SecretStr for security.
    """

    def __init__(
        self,
        connection_type: ConnectionType,
        host: Optional[SecretStr] = None,
        port: Optional[SecretStr] = None,
        database: Optional[SecretStr] = None,
        username: Optional[SecretStr] = None,
        password: Optional[SecretStr] = None,
        connection_string: Optional[SecretStr] = None,
        options: dict[str, Any] | None = None,
    ):
        self.connection_type = connection_type
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.connection_string = connection_string
        self.options = options or {}

    def to_dict(self, include_secrets: bool = False) -> dict[str, Any]:
        """
        Convert connection details to dictionary representation.

        Args:
            include_secrets: Whether to include secret values (default: False)
        """
        result = {
            "connection_type": self.connection_type.value,
            "options": self.options,
        }

        # Handle secret values
        if self.host:
            result["host"] = self.host.get_secret_value() if include_secrets else "***"

        if self.port:
            result["port"] = self.port.get_secret_value() if include_secrets else "***"

        if self.database:
            result["database"] = (
                self.database.get_secret_value() if include_secrets else "***"
            )

        if self.username:
            result["username"] = (
                self.username.get_secret_value() if include_secrets else "***"
            )

        if self.password:
            result["password"] = "***"  # Never include actual password

        if self.connection_string:
            result["connection_string"] = (
                "***"  # Never include actual connection string
            )

        return result


class DataSource:
    """
    Aggregate root representing a data source.

    Contains the complete definition of a data source including connection details
    and schema information.
    """

    def __init__(
        self,
        datasource_id: str | None = None,
        name: str | None = None,
        description: Optional[str] = None,
        connection: Optional[ConnectionDetails] = None,
        schema: Optional[DatabaseSchema] = None,
        metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.datasource_id = datasource_id or f"ds-{uuid4()}"
        self.name = name
        self.description = description
        self.connection = connection
        self.schema = schema
        self.field_metadata = metadata or {}
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or self.created_at

    def to_dict(self, include_secrets: bool = False) -> dict[str, Any]:
        """
        Convert data source to dictionary representation.

        Args:
            include_secrets: Whether to include secret values (default: False)
        """
        result = {
            "datasource_id": self.datasource_id,
            "name": self.name,
            "description": self.description,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

        if self.connection:
            result["connection"] = self.connection.to_dict(
                include_secrets=include_secrets
            )

        if self.schema:
            result["schema"] = self.schema.to_dict()

        return result
