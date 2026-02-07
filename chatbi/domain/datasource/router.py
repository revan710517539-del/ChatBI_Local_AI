"""
Datasource API routes.

This module provides REST API endpoints for managing datasources, including
creating, updating, listing, deleting datasources, and executing queries.
"""

import uuid
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from loguru import logger
from pydantic import UUID4

from chatbi.dependencies import (
    AsyncSessionDep,
    PostgresSessionDep,
    RepositoryDependency,
    transactional,
)
from chatbi.domain.datasource import (
    DatabaseType,
    DataSourceCreate,
    DataSourceListResponse,
    DatasourceMetricsResponse,
    DataSourceResponse,
    DataSourceStatus,
    DataSourceTestConnection,
    DataSourceTestResponse,
    DataSourceUpdate,
    QueryError,
    QueryRequest,
    QueryResult,
    SchemaMetadata,
    SystemHealthResponse,
)
from chatbi.domain.datasource.repository import DatasourceRepository
from chatbi.domain.datasource.service import DatasourceService
from chatbi.exceptions import BadRequestError, DatabaseError, NotFoundError
from chatbi.middleware.standard_response import StandardResponse

# Create router
router = APIRouter(prefix="/api/v1/datasources", tags=["datasources"])

# Create repository dependency
DatasourceRepoDep = RepositoryDependency(DatasourceRepository)


@router.post(
    "",
    response_model=StandardResponse[DataSourceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new datasource",
    description="Create a new datasource connection for database queries",
)
@transactional
async def create_datasource(
    data: DataSourceCreate,
    repo: DatasourceRepository = Depends(DatasourceRepoDep),
) -> StandardResponse[DataSourceResponse]:
    """
    Create a new datasource with connection information.

    Args:
        data: Datasource creation data
        db: Database session

    Returns:
        Newly created datasource
    """
    datasource_service = DatasourceService(repo=repo)
    result = await datasource_service.create_datasource(data)
    return StandardResponse(
        status="success", message="Datasource created successfully", data=result
    )


@router.get(
    "",
    response_model=StandardResponse[DataSourceListResponse],
    summary="List all datasources",
    description="Retrieve a list of all datasources with optional filtering and pagination",
)
async def list_datasources(
    repo: DatasourceRepository = Depends(DatasourceRepoDep),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    type: Optional[str] = Query(None, description="Filter by datasource type"),
    status: Optional[str] = Query(None, description="Filter by datasource status"),
) -> StandardResponse[DataSourceListResponse]:
    """
    List all datasources with optional filtering and pagination.

    Args:
        repo: Datasource repository
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        type: Optional filter by datasource type
        status: Optional filter by datasource status

    Returns:
        List of datasources and total count
    """
    datasource_service = DatasourceService(repo=repo)

    datasources, total = await datasource_service.get_datasources(
        skip=skip, limit=limit, type_filter=type, status_filter=status
    )

    return StandardResponse(
        status="success",
        message="Datasources retrieved successfully",
        data=DataSourceListResponse(items=datasources, total=total),
    )


@router.get(
    "/{datasource_id}",
    response_model=StandardResponse[DataSourceResponse],
    summary="Get a specific datasource",
    description="Retrieve details of a specific datasource by ID",
)
async def get_datasource(
    datasource_id: uuid.UUID = Path(
        ..., description="The ID of the datasource to retrieve"
    ),
    repo: DatasourceRepository = Depends(DatasourceRepoDep),
) -> StandardResponse[DataSourceResponse]:
    """
    Get a specific datasource by ID.

    Args:
        datasource_id: The ID of the datasource
        repo: Datasource repository

    Returns:
        Datasource details if found

    Raises:
        NotFoundError: If datasource not found
    """
    datasource_service = DatasourceService(repo=repo)
    datasource = await datasource_service.get_datasource_by_id(datasource_id)
    if not datasource:
        raise NotFoundError(f"Datasource with ID {datasource_id} not found")

    # Create response with masked connection_info
    response_data = DataSourceResponse(
        id=datasource.id,
        name=datasource.name,
        description=datasource.description,
        type=datasource.type,
        status=datasource.status,
        created_at=datasource.created_at,
        updated_at=datasource.updated_at,
        last_used_at=datasource.last_used_at,
        connection_info=datasource_service.mask_connection_info(datasource.connection_info),
    )

    return StandardResponse(
        status="success", message="Datasource retrieved successfully", data=response_data
    )


@router.put(
    "/{datasource_id}",
    response_model=StandardResponse[DataSourceResponse],
    summary="Update a datasource",
    description="Update an existing datasource's properties",
)
@transactional
async def update_datasource(
    data: DataSourceUpdate,
    datasource_id: uuid.UUID = Path(
        ..., description="The ID of the datasource to update"
    ),
    repo: DatasourceRepository = Depends(DatasourceRepoDep),
) -> StandardResponse[DataSourceResponse]:
    """
    Update an existing datasource.

    Args:
        data: Updated datasource properties
        datasource_id: The ID of the datasource to update
        db: Database session

    Returns:
        Updated datasource

    Raises:
        NotFoundError: If datasource not found or update failed
    """
    datasource_service = DatasourceService(repo=repo)
    result = await datasource_service.update_datasource(datasource_id, data)

    return StandardResponse(
        status="success", message="Datasource updated successfully", data=result
    )


@router.delete(
    "/{datasource_id}",
    response_model=StandardResponse,
    summary="Delete a datasource",
    description="Delete an existing datasource",
)
@transactional
async def delete_datasource(
    datasource_id: uuid.UUID = Path(
        ..., description="The ID of the datasource to delete"
    ),
    repo: DatasourceRepository = Depends(DatasourceRepoDep),
) -> StandardResponse:
    """
    Delete a datasource.

    Args:
        datasource_id: The ID of the datasource to delete
        db: Database session

    Returns:
        Success message

    Raises:
        NotFoundError: If datasource not found or deletion failed
    """
    datasource_service = DatasourceService(repo=repo)
    await datasource_service.delete_datasource(datasource_id)

    return StandardResponse(status="success", message="Datasource deleted successfully")


@router.post(
    "/test-connection",
    response_model=StandardResponse[DataSourceTestResponse],
    summary="Test datasource connection",
    description="Test connection to a database without creating a datasource",
)
async def test_connection(
    data: DataSourceTestConnection,
    repo: DatasourceRepository = Depends(DatasourceRepoDep),
) -> StandardResponse[DataSourceTestResponse]:
    """
    Test connection to a database without creating a datasource.

    Args:
        data: Connection information to test

    Returns:
        Connection test results
    """
    datasource_service = DatasourceService(repo=repo)
    success, message, details = await datasource_service.test_connection(
        data.type, data.connection_info, datasource_id=data.datasource_id
    )

    return StandardResponse(
        status="success",
        message="Connection test completed",
        data=DataSourceTestResponse(success=success, message=message, details=details),
    )


@router.post(
    "/{datasource_id}/query",
    response_model=StandardResponse[Union[QueryResult, QueryError]],
    summary="Execute a query",
    description="Execute an SQL query against a datasource",
)
@transactional
async def execute_query(
    query: QueryRequest,
    datasource_id: uuid.UUID = Path(
        ..., description="The ID of the datasource to query"
    ),
    repo: DatasourceRepository = Depends(DatasourceRepoDep),
) -> StandardResponse[Union[QueryResult, QueryError]]:
    """
    Execute an SQL query against a datasource.

    Args:
        query: Query to execute
        datasource_id: The ID of the datasource to query
        db: Database session

    Returns:
        Query results

    Raises:
        NotFoundError: If datasource not found or query execution failed
    """
    datasource_service = DatasourceService(repo=repo)
    result = await datasource_service.execute_query(
        datasource_id,
        query.sql,
        timeout=query.timeout,
        max_rows=query.max_rows,
        parameters=query.parameters,
    )

    return StandardResponse(status="success", message="Query executed", data=result)


@router.get(
    "/{datasource_id}/schema",
    response_model=StandardResponse[SchemaMetadata],
    summary="Get datasource schema",
    description="Retrieve database schema information from a datasource",
)
@transactional
async def get_schema(
    datasource_id: uuid.UUID = Path(..., description="The ID of the datasource"),
    repo: DatasourceRepository = Depends(DatasourceRepoDep),
) -> StandardResponse[SchemaMetadata]:
    """
    Retrieve database schema information from a datasource.

    Args:
        datasource_id: The ID of the datasource
        db: Database session

    Returns:
        Schema metadata (tables, views, columns, etc.)

    Raises:
        NotFoundError: If datasource not found or schema retrieval failed
    """
    datasource_service = DatasourceService(repo=repo)
    schema = await datasource_service.get_schema_metadata(datasource_id)

    return StandardResponse(
        status="success", message="Schema retrieved successfully", data=schema
    )


@router.get(
    "/types",
    response_model=StandardResponse[list[dict[str, str]]],
    summary="Get available datasource types",
    description="Retrieve a list of supported database types",
)
async def get_datasource_types() -> StandardResponse[list[dict[str, str]]]:
    """
    Get all supported database types.

    Returns:
        List of database types with descriptions
    """
    types = [
        {
            "code": DatabaseType.POSTGRES,
            "name": "PostgreSQL",
            "description": "PostgreSQL relational database",
        },
        {
            "code": DatabaseType.MYSQL,
            "name": "MySQL",
            "description": "MySQL relational database",
        },
        {
            "code": DatabaseType.DUCKDB,
            "name": "DuckDB",
            "description": "Embedded analytical database",
        },
        {
            "code": DatabaseType.CLICKHOUSE,
            "name": "ClickHouse",
            "description": "Column-oriented OLAP database",
        },
        {
            "code": DatabaseType.MSSQL,
            "name": "SQL Server",
            "description": "Microsoft SQL Server",
        },
        {
            "code": DatabaseType.SNOWFLAKE,
            "name": "Snowflake",
            "description": "Snowflake data warehouse",
        },
    ]

    return StandardResponse(
        status="success", message="Database types retrieved successfully", data=types
    )
