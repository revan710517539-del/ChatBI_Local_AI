"""
Data Transfer Objects (DTOs) for datasource functionality.

This module contains all the Pydantic models used for API request/response serialization
related to datasource functionality, including connection information DTOs.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator

# Common fields used across models
manifest_str_field = Field(alias="manifestStr", description="Base64 manifest")
connection_info_field = Field(alias="connectionInfo")


class DatabaseType(str, Enum):
    """Enum for supported database types"""

    SQLITE = "sqlite"
    POSTGRES = "postgres"
    MYSQL = "mysql"
    DUCKDB = "duckdb"
    MSSQL = "mssql"
    CLICKHOUSE = "clickhouse"
    BIGQUERY = "bigquery"
    SNOWFLAKE = "snowflake"
    TRINO = "trino"


class DataSourceStatus(str, Enum):
    """Enum for datasource connection status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DELETED = "deleted"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    DISCONNECTING = "disconnecting"


# Base models for datasource operations
class DataSourceBase(BaseModel):
    """Base model for datasource configuration"""

    name: str = Field(
        ...,
        description="Unique name for the datasource",
        examples=["production_postgres", "analytics_warehouse"],
        min_length=3,
        max_length=100,
    )
    description: Optional[str] = Field(
        None,
        description="Optional description of the datasource's purpose and contents",
        examples=[
            "Production database with customer data",
            "Analytics warehouse with aggregated metrics",
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={"description": "Core datasource properties"}
    )


class DataSourceCreate(DataSourceBase):
    """
    Model for creating a new datasource connection.

    The connection_info should match the requirements for the selected database type.
    """

    type: DatabaseType = Field(
        ..., description="Database system type", examples=["postgres", "mysql"]
    )
    connection_info: dict[str, Any] = Field(
        ...,
        description="Connection parameters specific to the database type",
        examples=[
            {
                "host": "localhost",
                "port": 5432,
                "database": "analytics",
                "username": "user",
                "password": "****",
            }
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "description": "Create a new datasource connection",
            "example": {
                "name": "analytics_db",
                "description": "Main analytics database",
                "type": "postgres",
                "connection_info": {
                    "host": "db.example.com",
                    "port": 5432,
                    "database": "analytics",
                    "username": "analyst",
                    "password": "****",
                    "ssl": True,
                },
            },
        }
    )


class DataSourceUpdate(BaseModel):
    """Model for updating an existing datasource"""

    name: Optional[str] = Field(
        None,
        description="New name for the datasource",
        examples=["updated_postgres"],
        min_length=3,
        max_length=100,
    )
    description: Optional[str] = Field(
        None,
        description="Updated description",
        examples=["Updated database description"],
    )
    connection_info: Optional[dict[str, Any]] = Field(
        None, description="Updated connection parameters"
    )
    status: Optional[DataSourceStatus] = Field(
        None, description="Change the datasource status"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "description": "Update an existing datasource's properties",
            "example": {
                "name": "updated_analytics_db",
                "description": "Updated analytics database",
                "connection_info": {
                    "host": "new-db.example.com",
                    "password": "new-password",
                },
                "status": "active",
            },
        }
    )


class DataSourceResponse(DataSourceBase):
    """Response model for datasource information"""

    id: UUID = Field(..., description="Unique identifier")
    type: DatabaseType = Field(..., description="Database type")
    status: DataSourceStatus = Field(..., description="Connection status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_used_at: Optional[datetime] = Field(None, description="Last used timestamp")
    connection_info: Optional[dict[str, Any]] = Field(
        None,
        description="Connection info (passwords masked for security)",
        exclude=False,
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "name": "analytics_db",
                "description": "Main analytics database",
                "type": "postgres",
                "status": "active",
                "created_at": "2023-01-15T12:00:00Z",
                "updated_at": "2023-01-15T12:00:00Z",
                "last_used_at": "2023-01-15T14:35:42Z",
            }
        },
    )


class DataSourceListResponse(BaseModel):
    """Response model for listing datasources with pagination information"""

    items: list[DataSourceResponse] = Field(..., description="List of datasources")
    total: int = Field(..., description="Total number of datasources")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                        "name": "analytics_db",
                        "description": "Main analytics database",
                        "type": "postgres",
                        "status": "active",
                        "created_at": "2023-01-15T12:00:00Z",
                        "updated_at": "2023-01-15T12:00:00Z",
                        "last_used_at": "2023-01-15T14:35:42Z",
                    }
                ],
                "total": 1,
            }
        }
    )


# Connection info DTOs (already defined earlier)
class QueryDTO(BaseModel):
    """Base query DTO for executing SQL against a datasource."""

    sql: str
    manifest_str: str = manifest_str_field
    connection_info: ConnectionInfo = connection_info_field


class DuckDbConnectionInfo(BaseModel):
    """Connection info for DuckDB datasource."""

    connection_url: SecretStr


class BigQueryConnectionInfo(BaseModel):
    """Connection info for BigQuery datasource."""

    project_id: SecretStr
    dataset_id: SecretStr
    credentials: SecretStr = Field(description="Base64 encode `credentials.json`")


class ClickHouseConnectionInfo(BaseModel):
    """Connection info for ClickHouse datasource."""

    host: SecretStr
    port: SecretStr
    database: SecretStr
    user: SecretStr
    password: SecretStr


class MSSqlConnectionInfo(BaseModel):
    """Connection info for Microsoft SQL Server datasource."""

    host: SecretStr
    port: SecretStr
    database: SecretStr
    user: SecretStr
    password: SecretStr
    driver: str = Field(
        default="FreeTDS",
        description="On Mac and Linux this is usually `FreeTDS. On Windows, it is usually `ODBC Driver 18 for SQL Server`",
    )


class MySqlConnectionInfo(BaseModel):
    """Connection info for MySQL datasource."""

    host: SecretStr
    port: SecretStr
    database: SecretStr
    user: SecretStr
    password: SecretStr


class ConnectionUrl(BaseModel):
    """Generic connection URL."""

    connection_url: SecretStr = Field(alias="connectionUrl")


class PostgresConnectionInfo(BaseModel):
    """Connection info for PostgreSQL datasource."""

    host: SecretStr = Field(examples=["localhost"])
    port: SecretStr = Field(examples=[5432])
    database: SecretStr
    user: SecretStr
    password: SecretStr


class SnowflakeConnectionInfo(BaseModel):
    """Connection info for Snowflake datasource."""

    user: SecretStr
    password: SecretStr
    account: SecretStr
    database: SecretStr
    sf_schema: SecretStr = Field(
        alias="schema"
    )  # Use `sf_schema` to avoid `schema` shadowing in BaseModel


class TrinoConnectionInfo(BaseModel):
    """Connection info for Trino datasource."""

    host: SecretStr
    port: SecretStr = Field(default="8080")
    catalog: SecretStr
    trino_schema: SecretStr = Field(
        alias="schema"
    )  # Use `trino_schema` to avoid `schema` shadowing in BaseModel
    user: SecretStr | None = None
    password: SecretStr | None = None


# Define Union type for connection info
ConnectionInfo = Union[
    DuckDbConnectionInfo,
    BigQueryConnectionInfo,
    ConnectionUrl,
    MSSqlConnectionInfo,
    MySqlConnectionInfo,
    PostgresConnectionInfo,
    SnowflakeConnectionInfo,
    TrinoConnectionInfo,
]


# Connection testing models
class DataSourceTestConnection(BaseModel):
    """Model for testing a datasource connection without creating it"""

    type: DatabaseType = Field(..., description="Database system type to test")
    datasource_id: Optional[UUID] = Field(
        None, description="ID of existing datasource to merge credentials from"
    )
    connection_info: dict[str, Any] = Field(
        ..., description="Connection parameters to test"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "postgres",
                "connection_info": {
                    "host": "db.example.com",
                    "port": 5432,
                    "database": "analytics",
                    "username": "test_user",
                    "password": "test_password",
                },
            }
        }
    )

    def get_connection_info(self) -> Any:
        """Convert generic connection info to specific type"""
        if self.type == DatabaseType.POSTGRES:
            return PostgresConnectionInfo(**self.connection_info)
        elif self.type == DatabaseType.MYSQL:
            return MySqlConnectionInfo(**self.connection_info)
        elif self.type == DatabaseType.DUCKDB:
            return DuckDbConnectionInfo(**self.connection_info)
        elif self.type == DatabaseType.MSSQL:
            return MSSqlConnectionInfo(**self.connection_info)
        elif self.type == DatabaseType.CLICKHOUSE:
            return ClickHouseConnectionInfo(**self.connection_info)
        elif self.type == DatabaseType.BIGQUERY:
            return BigQueryConnectionInfo(**self.connection_info)
        elif self.type == DatabaseType.SNOWFLAKE:
            return SnowflakeConnectionInfo(**self.connection_info)
        elif self.type == DatabaseType.TRINO:
            return TrinoConnectionInfo(**self.connection_info)
        else:
            raise ValueError(f"Unsupported database type: {self.type}")


class DataSourceTestResponse(BaseModel):
    """Response model for connection test results"""

    success: bool = Field(..., description="Whether the connection test was successful")
    message: str = Field(..., description="Human-readable result message")
    details: Optional[dict[str, Any]] = Field(
        None, description="Additional details about the test result"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "message": "Connection successful",
                    "details": {
                        "version": "PostgreSQL 14.5",
                        "server_time": "2023-05-15T10:23:54Z",
                    },
                },
                {
                    "success": False,
                    "message": "Connection failed",
                    "details": {
                        "error_type": "authentication",
                        "error_message": "Invalid username or password",
                    },
                },
            ]
        }
    )


# Query models
class QueryRequest(BaseModel):
    """Model for executing a SQL query against a datasource"""

    sql: str = Field(
        ...,
        description="SQL query to execute",
        examples=["SELECT * FROM users LIMIT 10"],
    )
    timeout: Optional[int] = Field(
        30, description="Query timeout in seconds", ge=1, le=300
    )
    max_rows: Optional[int] = Field(
        1000, description="Maximum number of rows to return", ge=1, le=10000
    )
    parameters: Optional[dict[str, Any]] = Field(
        None,
        description="Query parameters for parameterized queries",
        examples=[{"user_id": 123, "status": "active"}],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sql": "SELECT name, email FROM users WHERE status = :status LIMIT :limit",
                "timeout": 60,
                "max_rows": 500,
                "parameters": {"status": "active", "limit": 100},
            }
        }
    )


class QueryColumn(BaseModel):
    """Model for a query result column metadata"""

    name: str = Field(..., description="Column name")
    type: str = Field(..., description="Data type of the column")


class QueryResult(BaseModel):
    """Model for a successful query result"""

    query_id: UUID = Field(..., description="Unique identifier for the query execution")
    sql: str = Field(..., description="SQL query that was executed")
    columns: list[QueryColumn] = Field(..., description="Metadata about result columns")
    rows: list[dict[str, Any]] = Field(
        ..., description="Query result rows as dictionaries"
    )
    truncated: bool = Field(
        False, description="Whether the result was truncated due to row limit"
    )
    row_count: int = Field(..., description="Total number of rows returned")
    status: str = Field("success", description="Result status")
    duration_ms: int = Field(..., description="Query execution time in milliseconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "sql": "SELECT name, email FROM users LIMIT 2",
                "columns": [
                    {"name": "name", "type": "varchar"},
                    {"name": "email", "type": "varchar"},
                ],
                "rows": [
                    {"name": "John Doe", "email": "john@example.com"},
                    {"name": "Jane Smith", "email": "jane@example.com"},
                ],
                "truncated": False,
                "row_count": 2,
                "status": "success",
                "duration_ms": 45,
            }
        }
    )


class QueryError(BaseModel):
    """Model for a query execution error"""

    query_id: UUID = Field(..., description="Unique identifier for the query execution")
    sql: str = Field(..., description="SQL query that failed")
    error: str = Field(..., description="Error message")
    error_type: str = Field(
        ..., description="Type of error (syntax, access, timeout, etc.)"
    )
    status: str = Field("error", description="Result status")
    duration_ms: int = Field(..., description="Time spent before error in milliseconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "sql": "SELECT * FROM non_existent_table",
                "error": 'relation "non_existent_table" does not exist',
                "error_type": "syntax",
                "status": "error",
                "duration_ms": 15,
            }
        }
    )


# Schema models
class ColumnMetadata(BaseModel):
    """Model for database column metadata"""

    name: str = Field(..., description="Column name")
    type: str = Field(..., description="Data type of the column")
    nullable: bool = Field(..., description="Whether the column allows NULL values")
    primary_key: bool = Field(
        False, description="Whether the column is part of the primary key"
    )
    foreign_key: Optional[dict[str, str]] = Field(
        None, description="Foreign key reference if applicable (table and column)"
    )
    description: Optional[str] = Field(None, description="Column description/comment")

    @model_validator(mode="before")
    @classmethod
    def map_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Map data_type to type
            if "type" not in data and "data_type" in data:
                data["type"] = data["data_type"]

            # Map is_nullable to nullable
            if "nullable" not in data and "is_nullable" in data:
                val = data["is_nullable"]
                if isinstance(val, str):
                    data["nullable"] = val.upper() in ["YES", "TRUE", "1"]
                else:
                    data["nullable"] = bool(val)
            
            # Map is_primary_key to primary_key
            if "primary_key" not in data and "is_primary_key" in data:
                data["primary_key"] = bool(data["is_primary_key"])

            # Ensure primary_key and foreign_key have defaults if missing
            if "primary_key" not in data:
                data["primary_key"] = False
            if "foreign_key" not in data:
                data["foreign_key"] = None
        return data

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "user_id",
                "type": "integer",
                "nullable": False,
                "primary_key": True,
                "foreign_key": None,
                "description": "Unique user identifier",
            }
        }
    )


class IndexMetadata(BaseModel):
    """Model for database index metadata"""

    name: str = Field(..., description="Index name")
    columns: list[str] = Field(..., description="Columns included in the index")
    unique: bool = Field(False, description="Whether the index enforces uniqueness")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"name": "idx_users_email", "columns": ["email"], "unique": True}
        }
    )


class TableMetadata(BaseModel):
    """Model for database table metadata"""

    name: str = Field(..., description="Table name")
    schema_name: Optional[str] = Field(
        None, description="Schema name containing the table"
    )
    description: Optional[str] = Field(None, description="Table description/comment")
    columns: list[ColumnMetadata] = Field(..., description="Columns in the table")
    indexes: Optional[list[IndexMetadata]] = Field(
        None, description="Indexes on the table"
    )

    @model_validator(mode="before")
    @classmethod
    def map_schema_name(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "schema_name" not in data and "schema" in data:
                data["schema_name"] = data["schema"]
        return data

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "users",
                "schema_name": "public",
                "description": "User accounts",
                "columns": [
                    {
                        "name": "id",
                        "type": "integer",
                        "nullable": False,
                        "primary_key": True,
                    },
                    {
                        "name": "email",
                        "type": "varchar",
                        "nullable": False,
                        "primary_key": False,
                    },
                ],
                "indexes": [
                    {"name": "idx_users_email", "columns": ["email"], "unique": True}
                ],
            }
        }
    )


class SchemaMetadata(BaseModel):
    """Response model for complete database schema metadata"""

    tables: list[TableMetadata] = Field(
        ..., description="List of tables in the database"
    )
    views: list[TableMetadata] = Field([], description="List of views in the database")
    schemas: list[str] = Field([], description="List of schema names in the database")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tables": [
                    {
                        "name": "users",
                        "schema_name": "public",
                        "description": "User accounts",
                        "columns": [
                            {
                                "name": "id",
                                "type": "integer",
                                "nullable": False,
                                "primary_key": True,
                            },
                            {
                                "name": "email",
                                "type": "varchar",
                                "nullable": False,
                                "primary_key": False,
                            },
                        ],
                    }
                ],
                "views": [],
                "schemas": ["public", "data"],
            }
        }
    )


# Query-specific DTOs for each database type
class QueryDuckDbDTO(QueryDTO):
    """DTO for DuckDB queries."""


class QueryBigQueryDTO(QueryDTO):
    """DTO for BigQuery queries."""


class QueryClickHouseDTO(QueryDTO):
    """DTO for ClickHouse queries."""


class QueryMSSqlDTO(QueryDTO):
    """DTO for Microsoft SQL Server queries."""


class QueryMySqlDTO(QueryDTO):
    """DTO for MySQL queries."""


class QueryPostgresDTO(QueryDTO):
    """DTO for PostgreSQL queries."""


class QuerySnowflakeDTO(QueryDTO):
    """DTO for Snowflake queries."""


class QueryTrinoDTO(QueryDTO):
    """DTO for Trino queries."""


# SQL Analysis DTOs
class ValidateDTO(BaseModel):
    """DTO for validating SQL syntax."""

    sql: str = Field(..., description="SQL query to validate")
    dialect: str = Field(..., description="SQL dialect to use for validation")


class AnalyzeSQLDTO(BaseModel):
    """DTO for analyzing SQL queries."""

    sql: str = Field(..., description="SQL query to analyze")
    dialect: str = Field(..., description="SQL dialect to use for analysis")
    include_plan: bool = Field(
        False, description="Whether to include execution plan in analysis"
    )


class AnalyzeSQLBatchDTO(BaseModel):
    """DTO for analyzing multiple SQL queries together."""

    queries: list[str] = Field(..., description="List of SQL queries to analyze")
    dialect: str = Field(..., description="SQL dialect to use for analysis")
    include_plan: bool = Field(
        False, description="Whether to include execution plans in analysis"
    )


class DryPlanDTO(BaseModel):
    """DTO for generating an execution plan without running the query."""

    sql: str = Field(..., description="SQL query to plan")
    dialect: str = Field(..., description="SQL dialect to use for planning")


# Metrics models
class QueryMetrics(BaseModel):
    """Model for query execution metrics"""

    total_queries: int = Field(..., description="Total number of queries executed")
    avg_execution_time_ms: float = Field(
        ..., description="Average query execution time in milliseconds"
    )
    max_execution_time_ms: float = Field(
        ..., description="Maximum query execution time in milliseconds"
    )
    min_execution_time_ms: float = Field(
        ..., description="Minimum query execution time in milliseconds"
    )
    error_rate: float = Field(..., description="Query error rate as percentage")
    recent_queries: list[dict[str, Any]] = Field(
        ..., description="Recent query history"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_queries": 1250,
                "avg_execution_time_ms": 345.8,
                "max_execution_time_ms": 5432.1,
                "min_execution_time_ms": 12.4,
                "error_rate": 2.5,
                "recent_queries": [
                    {
                        "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                        "sql": "SELECT * FROM users LIMIT 10",
                        "status": "success",
                        "duration_ms": 42,
                        "executed_at": "2025-05-16T10:23:54Z",
                    }
                ],
            }
        }
    )


class UsageMetrics(BaseModel):
    """Model for datasource usage metrics"""

    total_connections: int = Field(
        ..., description="Total number of established connections"
    )
    active_connections: int = Field(..., description="Number of active connections")
    avg_connection_duration_ms: float = Field(
        ..., description="Average connection duration in milliseconds"
    )
    connections_per_hour: list[dict[str, Any]] = Field(
        ..., description="Connections per hour over time"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_connections": 500,
                "active_connections": 5,
                "avg_connection_duration_ms": 12500.0,
                "connections_per_hour": [
                    {"hour": "2025-05-16T10:00:00Z", "count": 45},
                    {"hour": "2025-05-16T11:00:00Z", "count": 62},
                ],
            }
        }
    )


class PerformanceStats(BaseModel):
    """Model for database performance statistics"""

    avg_response_time_ms: float = Field(
        ..., description="Average response time in milliseconds"
    )
    p95_response_time_ms: float = Field(
        ..., description="95th percentile response time in milliseconds"
    )
    p99_response_time_ms: float = Field(
        ..., description="99th percentile response time in milliseconds"
    )
    uptime_percentage: float = Field(..., description="Database uptime as percentage")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "avg_response_time_ms": 35.2,
                "p95_response_time_ms": 120.5,
                "p99_response_time_ms": 350.1,
                "uptime_percentage": 99.98,
            }
        }
    )


class DatasourceMetricsResponse(BaseModel):
    """Response model for datasource metrics"""

    datasource_id: UUID = Field(..., description="ID of the datasource")
    name: str = Field(..., description="Name of the datasource")
    type: DatabaseType = Field(..., description="Type of the datasource")
    query_metrics: QueryMetrics = Field(..., description="Query execution metrics")
    usage_metrics: UsageMetrics = Field(..., description="Usage metrics")
    performance_stats: PerformanceStats = Field(
        ..., description="Performance statistics"
    )
    last_updated: datetime = Field(
        ..., description="Timestamp when metrics were last updated"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "datasource_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "name": "analytics_db",
                "type": "postgres",
                "query_metrics": {
                    "total_queries": 1250,
                    "avg_execution_time_ms": 345.8,
                    "max_execution_time_ms": 5432.1,
                    "min_execution_time_ms": 12.4,
                    "error_rate": 2.5,
                    "recent_queries": [
                        {
                            "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                            "sql": "SELECT * FROM users LIMIT 10",
                            "status": "success",
                            "duration_ms": 42,
                            "executed_at": "2025-05-16T10:23:54Z",
                        }
                    ],
                },
                "usage_metrics": {
                    "total_connections": 500,
                    "active_connections": 5,
                    "avg_connection_duration_ms": 12500.0,
                    "connections_per_hour": [
                        {"hour": "2025-05-16T10:00:00Z", "count": 45},
                        {"hour": "2025-05-16T11:00:00Z", "count": 62},
                    ],
                },
                "performance_stats": {
                    "avg_response_time_ms": 35.2,
                    "p95_response_time_ms": 120.5,
                    "p99_response_time_ms": 350.1,
                    "uptime_percentage": 99.98,
                },
                "last_updated": "2025-05-16T12:00:00Z",
            }
        }
    )


class ConnectionPoolMetrics(BaseModel):
    """Model for connection pool metrics"""

    total_pools: int = Field(..., description="Total number of connection pools")
    active_pools: int = Field(..., description="Number of active connection pools")
    total_connections: int = Field(
        ..., description="Total connections across all pools"
    )
    active_connections: int = Field(..., description="Currently active connections")
    idle_connections: int = Field(..., description="Currently idle connections")
    connection_waiters: int = Field(
        ..., description="Number of connections waiting for a pool slot"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_pools": 5,
                "active_pools": 3,
                "total_connections": 50,
                "active_connections": 12,
                "idle_connections": 38,
                "connection_waiters": 0,
            }
        }
    )


class QueryPerformanceMetrics(BaseModel):
    """Model for system-wide query performance metrics"""

    queries_per_minute: float = Field(..., description="Queries executed per minute")
    avg_query_time_ms: float = Field(
        ..., description="Average query execution time in milliseconds"
    )
    error_rate: float = Field(..., description="Query error rate as percentage")
    slow_queries_count: int = Field(
        ..., description="Number of slow queries (>1s execution time)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "queries_per_minute": 250.5,
                "avg_query_time_ms": 125.3,
                "error_rate": 1.2,
                "slow_queries_count": 5,
            }
        }
    )


class SystemResourceMetrics(BaseModel):
    """Model for system resource usage metrics"""

    cpu_usage_percent: float = Field(..., description="CPU usage percentage")
    memory_usage_percent: float = Field(..., description="Memory usage percentage")
    disk_usage_percent: float = Field(..., description="Disk usage percentage")
    network_io_mbps: float = Field(
        ..., description="Network I/O in megabits per second"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cpu_usage_percent": 35.2,
                "memory_usage_percent": 42.8,
                "disk_usage_percent": 68.5,
                "network_io_mbps": 25.4,
            }
        }
    )


class SystemHealthResponse(BaseModel):
    """Response model for system health metrics"""

    overall_status: str = Field(..., description="Overall system health status")
    connection_pool: ConnectionPoolMetrics = Field(
        ..., description="Connection pool metrics"
    )
    query_performance: QueryPerformanceMetrics = Field(
        ..., description="Query performance metrics"
    )
    system_resources: SystemResourceMetrics = Field(
        ..., description="System resource metrics"
    )
    datasource_statuses: dict[str, str] = Field(
        ..., description="Status of each datasource"
    )
    uptime_seconds: int = Field(..., description="System uptime in seconds")
    last_updated: datetime = Field(
        ..., description="Timestamp when metrics were last updated"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "overall_status": "healthy",
                "connection_pool": {
                    "total_pools": 5,
                    "active_pools": 3,
                    "total_connections": 50,
                    "active_connections": 12,
                    "idle_connections": 38,
                    "connection_waiters": 0,
                },
                "query_performance": {
                    "queries_per_minute": 250.5,
                    "avg_query_time_ms": 125.3,
                    "error_rate": 1.2,
                    "slow_queries_count": 5,
                },
                "system_resources": {
                    "cpu_usage_percent": 35.2,
                    "memory_usage_percent": 42.8,
                    "disk_usage_percent": 68.5,
                    "network_io_mbps": 25.4,
                },
                "datasource_statuses": {
                    "analytics_db": "active",
                    "data_warehouse": "active",
                    "reporting_db": "inactive",
                },
                "uptime_seconds": 1209600,
                "last_updated": "2025-05-16T12:00:00Z",
            }
        }
    )
