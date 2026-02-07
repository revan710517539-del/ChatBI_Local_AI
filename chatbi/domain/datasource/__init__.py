"""
Datasource domain models and business logic.

This module contains the core domain models and business logic for data source management.
"""

from chatbi.domain.datasource.dtos import (
    AnalyzeSQLBatchDTO,
    AnalyzeSQLDTO,
    BigQueryConnectionInfo,
    ClickHouseConnectionInfo,
    ColumnMetadata,
    # Connection info DTOs
    ConnectionInfo,
    ConnectionUrl,
    DatabaseType,
    # Data source DTOs
    DataSourceCreate,
    DataSourceListResponse,
    # Metrics DTOs
    DatasourceMetricsResponse,
    DataSourceResponse,
    DataSourceStatus,
    DataSourceTestConnection,
    DataSourceTestResponse,
    DataSourceUpdate,
    DryPlanDTO,
    DuckDbConnectionInfo,
    IndexMetadata,
    MSSqlConnectionInfo,
    MySqlConnectionInfo,
    PostgresConnectionInfo,
    QueryBigQueryDTO,
    QueryClickHouseDTO,
    # Query DTOs
    QueryColumn,
    QueryDTO,
    QueryDuckDbDTO,
    QueryError,
    QueryMSSqlDTO,
    QueryMySqlDTO,
    QueryPostgresDTO,
    QueryRequest,
    QueryResult,
    QuerySnowflakeDTO,
    QueryTrinoDTO,
    SchemaMetadata,
    SnowflakeConnectionInfo,
    # System metrics DTO
    SystemHealthResponse,
    TableMetadata,
    TrinoConnectionInfo,
    # Other DTOs
    ValidateDTO,
)
from chatbi.domain.datasource.entities import (
    Datasource,
    DataSourceEntity,
    QueryHistory,
)
from chatbi.domain.datasource.models import (
    ColumnDefinition,
    ColumnType,
    ConnectionDetails,
    ConnectionType,
    DatabaseSchema,
    DataSource,
    TableDefinition,
)
from chatbi.domain.datasource.repository import DatasourceRepository
from chatbi.domain.datasource.router import router as DatasourceRouter
from chatbi.domain.datasource.service import DatasourceService

__all__ = [
    # Domain router
    "DatasourceRouter",
    # Domain repository
    "DatasourceRepository",
    # Domain service
    "DatasourceService",
    # ------------------------------------------------------------
    "DatabaseType",
    "DataSourceStatus",
    # Database entities
    "Datasource",
    "QueryHistory",
    # Domain entities
    "DataSourceEntity",
    # Domain models
    "DataSource",
    "ConnectionDetails",
    "ConnectionType",
    "TableDefinition",
    "ColumnDefinition",
    "ColumnType",
    "DatabaseSchema",
    # Connection info DTOs
    "ConnectionInfo",
    "ConnectionUrl",
    "DuckDbConnectionInfo",
    "BigQueryConnectionInfo",
    "ClickHouseConnectionInfo",
    "MSSqlConnectionInfo",
    "MySqlConnectionInfo",
    "PostgresConnectionInfo",
    "SnowflakeConnectionInfo",
    "TrinoConnectionInfo",
    # Query DTOs
    "QueryDTO",
    "QueryDuckDbDTO",
    "QueryBigQueryDTO",
    "QueryClickHouseDTO",
    "QueryMSSqlDTO",
    "QueryMySqlDTO",
    "QueryPostgresDTO",
    "QuerySnowflakeDTO",
    "QueryTrinoDTO",
    "QueryRequest",
    "QueryResult",
    "QueryError",
    "QueryColumn",
    # Response models
    "DataSourceResponse",
    "DataSourceListResponse",
    "DataSourceTestResponse",
    # Schema models
    "TableMetadata",
    "ColumnMetadata",
    "IndexMetadata",
    "SchemaMetadata",
    # Metrics models
    "DatasourceMetricsResponse",
    "SystemHealthResponse",
    # Other DTOs
    "ValidateDTO",
    "AnalyzeSQLDTO",
    "AnalyzeSQLBatchDTO",
    "DryPlanDTO",
]
