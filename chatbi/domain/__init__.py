"""
Domain module for ChatBI.

This package contains all domain models, entities, and business logic for the application,
organized by domain/feature areas.
"""

# Re-export common domain components
# Re-export key domain entities for easy access
from chatbi.domain.auth import (
    # Core models
    User,
    UserSession,
    TokenPair,
    # DTOs
    LoginDTO,
    TokenResponse,
    UserDTO,
    CreateUserDTO,
    UpdateUserDTO,
)
from chatbi.domain.mdl import (
    # Core models
    MDLColumn,
    MDLRelationship,
    MDLModel,
    MDLMetric,
    MDLProject,
    # DTOs
    CreateMDLProjectDTO,
    UpdateMDLProjectDTO,
    MDLProjectDTO,
    MDLProjectDetailDTO,
    CreateMDLModelDTO,
    UpdateMDLModelDTO,
    MDLModelDTO,
    MDLModelDetailDTO,
    MDLSyncRequestDTO,
    MDLSyncResponseDTO,
)
from chatbi.domain.chat import (
    # DTOs
    ChatDTO,
    # Database entities
    ChatHistory,
    ChatMessage,
    # Domain entities
    ChatMessageEntity,
    # Core domain models
    ChatSession,
    ChatSessionDomainEntity,
    ChatSessionEntity,
    CommonResponse,
    ConversationContext,
    GenerateSqlRequest,
    Message,
    MessageRole,
    RunSqlRequest,
    RunSqlResponse,
    SavedQuery,
    Visualization,
)
from chatbi.domain.common import (
    Base,
    EntityMixin,
    ErrorModel,
    ErrorResponse,
    MetadataModel,
    PaginationModel,
    StatusResponse,
    UUIDModel,
)

from chatbi.domain.datasource import (
    # Core domain models
    ColumnDefinition,
    ColumnType,
    ConnectionDetails,
    # Connection DTOs
    ConnectionInfo,
    ConnectionType,
    DatabaseSchema,
    DatabaseType,
    DataSource,
    # Database entities
    Datasource,
    # API DTOs
    DataSourceCreate,
    # Domain entities
    DataSourceEntity,
    DataSourceResponse,
    DataSourceStatus,
    DataSourceUpdate,
    DuckDbConnectionInfo,
    MySqlConnectionInfo,
    PostgresConnectionInfo,
    QueryHistory,
    QueryRequest,
    QueryResult,
    SchemaMetadata,
    TableDefinition,
)

__all__ = [
    # Common domain components
    "Base",
    "UUIDModel",
    "EntityMixin",
    "ErrorModel",
    "ErrorResponse",
    "MetadataModel",
    "PaginationModel",
    "StatusResponse",
    # Chat domain
    "ChatSession",
    "ChatSessionEntity",
    "ChatSessionDomainEntity",
    "ChatMessage",
    "ChatMessageEntity",
    "Message",
    "MessageRole",
    "ConversationContext",
    "Visualization",
    "SavedQuery",
    "ChatHistory",
    "ChatDTO",
    "GenerateSqlRequest",
    "RunSqlRequest",
    "RunSqlResponse",
    "CommonResponse",

    # Datasource domain
    "DatabaseType",
    "DataSourceStatus",
    "Datasource",
    "QueryHistory",
    "DataSourceEntity",
    "DataSource",
    "ConnectionDetails",
    "ConnectionType",
    "TableDefinition",
    "ColumnDefinition",
    "ColumnType",
    "DatabaseSchema",
    "ConnectionInfo",
    "DataSourceCreate",
    "DataSourceResponse",
    "DataSourceUpdate",
    "DuckDbConnectionInfo",
    "MySqlConnectionInfo",
    "PostgresConnectionInfo",
    "QueryRequest",
    "QueryResult",
    "SchemaMetadata",
]
