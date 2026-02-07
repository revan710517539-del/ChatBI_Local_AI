"""
Datasource service with optimized PostgreSQL connection handling.

This service provides operations for managing datasources with improved
connection management, error handling, and performance optimization.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from chatbi.database import PostgresDB
from chatbi.database.connection_manager import ConnectionManager
from chatbi.dependencies import transactional
from chatbi.domain.datasource import (
    ConnectionInfo,
    DatabaseType,
    DataSourceCreate,
    DataSourceResponse,
    DataSourceStatus,
    DataSourceUpdate,
)
from chatbi.domain.datasource.entities import Datasource, QueryHistory
from chatbi.domain.datasource.repository import DatasourceRepository
from chatbi.exceptions import BadRequestError, DatabaseError, NotFoundError


class DatasourceService:
    """
    Service for managing datasources with optimized database operations.

    Uses repository pattern, connection pooling, and standardized error
    handling for improved reliability and performance.
    """

    # Default timeouts and limits
    DEFAULT_QUERY_TIMEOUT = 30
    DEFAULT_MAX_ROWS = 1000
    DEFAULT_CONN_TIMEOUT = 10.0

    def __init__(self, repo: DatasourceRepository):
        """
        Initialize with required repository dependency injection.

        Args:
            repo: Repository instance for database operations
        """
        if repo is None:
            raise ValueError("Repository cannot be None")

        self.repo = repo

    async def create_datasource(self, data: DataSourceCreate) -> Datasource:
        """
        Create a new datasource with optimized connection validation.

        Args:
            db: Database session
            data: Datasource creation data

        Returns:
            Newly created datasource

        Raises:
            DatabaseError: If there's a database-related error
            BadRequestError: If the datasource name already exists or connection test fails
        """
        try:
            repo = self.repo

            # Test connection before saving to database
            connection_info = data.connection_info
            success, message, details = await ConnectionManager.test_connection(
                DatabaseType(data.type), connection_info
            )

            if not success:
                raise BadRequestError(message=f"Connection test failed: {message}")

            # Sanitize connection info before storing
            sanitized_info = self._sanitize_connection_info(data.connection_info)

            # Check if we're using SQLAlchemy or SQLModel
            model_has_connection_info = hasattr(Datasource, "connection_info")
            connection_field_name = (
                "connection_info" if model_has_connection_info else "config"
            )

            # Create datasource data dictionary
            datasource_kwargs = {
                "name": data.name,
                "description": data.description,
                "type": data.type,
                "status": DataSourceStatus.ACTIVE,
            }

            # Add the connection info to the appropriate field
            datasource_kwargs[connection_field_name] = sanitized_info

            # Create datasource using repository
            datasource = await repo.create_datasource(datasource_kwargs)

            logger.info(
                f"Created new datasource: {datasource.name} (ID: {datasource.id})"
            )
            return datasource

        except (BadRequestError, DatabaseError):
            raise

    @transactional
    async def update_datasource(
        self, datasource_id: uuid.UUID, data: DataSourceUpdate
    ) -> Datasource:
        """
        Update an existing datasource with optimized connection validation.

        Args:
            db: Database session
            datasource_id: ID of the datasource to update
            data: Updated datasource data

        Returns:
            Updated datasource

        Raises:
            NotFoundError: If datasource not found
            BadRequestError: If connection test fails
            DatabaseError: If there's a database-related error
        """
        repo = self.repo

        # Get existing datasource
        datasource: Datasource = await repo.get_by_id_or_error(datasource_id)
        logger.debug(f"Current datasource name: {datasource.name}, Requested name: {data.name}")

        # Check if we're using SQLAlchemy or SQLModel based models
        model_has_connection_info = hasattr(datasource, "connection_info")
        connection_field_name = (
            "connection_info" if model_has_connection_info else "config"
        )

        # Get current connection info
        current_conn_info = getattr(datasource, connection_field_name, {})

        # Apply updates to the datasource
        updated = False
        if data.name is not None and data.name != datasource.name:
            logger.info(f"Updating name from '{datasource.name}' to '{data.name}'")
            datasource.name = data.name
            updated = True
        else:
            logger.debug(f"Name not changed or None: data.name={data.name}, current={datasource.name}")

        if data.description is not None and data.description != datasource.description:
            logger.info(f"Updating description")
            datasource.description = data.description
            updated = True

        if data.status is not None and data.status != datasource.status:
            logger.info(f"Updating status")
            datasource.status = data.status
            updated = True

        # If connection info is updated, test the new connection
        if data.connection_info is not None:
            logger.debug(f"Processing connection_info update for datasource {datasource_id}")
            
            # Filter out masked values (values that contain only asterisks)
            # and preserve original values for those fields
            cleaned_connection_info = {}
            has_real_changes = False
            
            for key, value in data.connection_info.items():
                str_value = str(value) if value is not None else ""
                # Check if this is a masked value (contains only * or is like "x****y")
                is_masked = (
                    str_value 
                    and ("****" in str_value or str_value == "********")
                )
                
                if is_masked and key in current_conn_info:
                    # Keep the original value for masked fields
                    cleaned_connection_info[key] = current_conn_info[key]
                    logger.debug(f"Keeping masked field '{key}' with original value")
                else:
                    # Use the new value
                    cleaned_connection_info[key] = value
                    # Check if this is actually different from current
                    if key not in current_conn_info or current_conn_info[key] != value:
                        has_real_changes = True
                        logger.debug(f"Field '{key}' has real changes")
            
            # Merge existing and cleaned connection info
            updated_connection_info = {
                **current_conn_info,
                **cleaned_connection_info,
            }

            logger.debug(f"Has real connection changes: {has_real_changes}")
            
            # Only test if connection params actually changed
            if has_real_changes and updated_connection_info != current_conn_info:
                logger.info(f"Testing connection for datasource {datasource_id}")
                
                # Test the updated connection - pass dict directly
                success, message, details = await ConnectionManager.test_connection(
                    DatabaseType(datasource.type), updated_connection_info
                )

                if not success:
                    raise BadRequestError(
                        message=f"Connection test failed with updated credentials: {message}"
                    )

                # Update connection info if test passed
                sanitized_info = self._sanitize_connection_info(updated_connection_info)
                setattr(datasource, connection_field_name, sanitized_info)
                updated = True
            else:
                logger.debug(f"No real connection changes detected, skipping test")

        if updated:
            # Update timestamp
            datasource.updated_at = datetime.utcnow()

            logger.info(f"Updating datasource {datasource_id} with updated={updated}")
            
            # Update datasource
            updated_datasource = await repo.update(datasource)

            logger.info(
                f"Updated datasource: {updated_datasource.name} (ID: {updated_datasource.id})"
            )
            return updated_datasource

        # No updates needed
        logger.info(f"No updates needed for datasource {datasource_id}")
        return datasource

    @transactional
    async def delete_datasource(self, datasource_id: uuid.UUID) -> bool:
        """
        Delete a datasource with proper cleanup.

        Args:
            db: Database session
            datasource_id: ID of the datasource to delete

        Returns:
            True if deleted successfully

        Raises:
            NotFoundError: If datasource not found
            DatabaseError: If there's a database-related error
        """
        repo = self.repo

        # Get existing datasource first to check if it exists
        datasource = await repo.get_by_id_or_error(datasource_id)

        # Record the name and ID before deletion for logging
        name = datasource.name
        id_str = str(datasource.id)

        # Delete using repository
        success = await repo.delete(datasource_id)

        if success:
            logger.info(f"Deleted datasource: {name} (ID: {id_str})")

        return success

    async def get_datasource_by_id(self, datasource_id: uuid.UUID) -> Optional[Datasource]:
        """
        Get a datasource by ID with optimized query.

        Args:
            db: Database session
            datasource_id: ID of the datasource

        Returns:
            Datasource if found, None otherwise
        """
        return await self.repo.get_by_id(datasource_id)

    async def get_datasources(
        self,
        skip: int = 0,
        limit: int = 100,
        type_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> tuple[list[Datasource], int]:
        """
        Get all datasources with efficient filtering and pagination.

        Uses repository pattern for improved database access.

        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            type_filter: Optional filter by datasource type
            status_filter: Optional filter by datasource status

        Returns:
            Tuple of (list of datasources, total count)
        """
        # Using the correct repository method for getting datasources with pagination
        datasources = await self.repo.get_all(
            skip=skip,
            limit=limit,
            type_filter=type_filter,
            status_filter=status_filter,
        )

        # Get the total count for pagination
        total = await self.repo.count(
            type_filter=type_filter, 
            status_filter=status_filter
        )

        return datasources, total

    async def test_connection(
        self,
        db_type: DatabaseType,
        connection_info_dict: dict[str, Any],
        datasource_id: Optional[uuid.UUID] = None,
    ) -> tuple[bool, str, Optional[dict[str, Any]]]:
        """
        Test connection to a datasource using the optimized ConnectionManager.

        Args:
            db_type: Database type
            connection_info_dict: Connection parameters
            datasource_id: Optional ID of existing datasource to merge credentials from

        Returns:
            Tuple of (success: bool, message: str, details: Optional[Dict])
        """
        try:
            # If datasource_id is provided, merge with existing credentials
            final_connection_info = connection_info_dict
            if datasource_id:
                try:
                    datasource = await self.repo.get_by_id(datasource_id)
                    if datasource:
                        model_has_connection_info = hasattr(datasource, "connection_info")
                        connection_field_name = (
                            "connection_info" if model_has_connection_info else "config"
                        )
                        current_conn_info = getattr(datasource, connection_field_name, {})

                        # Merge logic similar to update_datasource
                        merged_info = {}
                        for key, value in connection_info_dict.items():
                            str_value = str(value) if value is not None else ""
                            is_masked = str_value and (
                                "****" in str_value or str_value == "********"
                            )

                            if is_masked and key in current_conn_info:
                                merged_info[key] = current_conn_info[key]
                            else:
                                merged_info[key] = value

                        # Add any keys from current that might be missing in input
                        for k, v in current_conn_info.items():
                            if k not in merged_info:
                                merged_info[k] = v

                        final_connection_info = merged_info
                        logger.debug(
                            f"Merged connection info for datasource {datasource_id} (masked)"
                        )

                except Exception as e:
                    logger.warning(
                        f"Failed to load existing datasource {datasource_id} for credential merging: {e}"
                    )
                    # Continue with provided info

            # Sanitize connection info (remove sensitive data from logs)
            safe_conn_info = self._sanitize_connection_info(
                final_connection_info, for_logging=True
            )
            logger.debug(
                f"Testing connection to {db_type} with params: {safe_conn_info}"
            )

            # Delegate to enhanced ConnectionManager with retries
            return await ConnectionManager.test_connection(
                db_type, final_connection_info, timeout=self.DEFAULT_CONN_TIMEOUT
            )

        except Exception as e:
            logger.error(f"Connection test error for {db_type}: {e!s}")
            return False, f"Connection error: {e!s}", None

    @transactional
    async def execute_query(
        self,
        datasource_id: uuid.UUID,
        sql: str,
        timeout: int = None,
        max_rows: int = None,
        parameters: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Execute SQL query using the optimized ConnectionManager with retries.

        Args:
            datasource_id: ID of the datasource to query
            sql: SQL query to execute
            timeout: Query timeout in seconds
            max_rows: Maximum rows to return
            parameters: Optional query parameters

        Returns:
            Query results with metadata

        Raises:
            NotFoundError: If datasource not found
            BadRequestError: For invalid queries
            DatabaseError: For database-related errors
        """
        repo = self.repo

        timeout = timeout or self.DEFAULT_QUERY_TIMEOUT
        max_rows = max_rows or self.DEFAULT_MAX_ROWS
        start_time = datetime.utcnow()
        query_id = uuid.uuid4()
        error = None
        row_count = 0

        # Check if QueryHistory uses execution_time_ms or duration_ms
        qh_has_execution_time_ms = hasattr(QueryHistory, "execution_time_ms")
        time_field_name = (
            "execution_time_ms" if qh_has_execution_time_ms else "duration_ms"
        )

        try:
            # Get datasource using repository
            datasource = await repo.get_by_id_or_error(datasource_id)

            if datasource.status != DataSourceStatus.ACTIVE:
                raise BadRequestError(
                    message=f"Datasource '{datasource.name}' is not active"
                )

            # Check which field contains connection info: connection_info or config
            model_has_connection_info = hasattr(datasource, "connection_info")
            connection_field_name = (
                "connection_info" if model_has_connection_info else "config"
            )

            # Get connection info from appropriate field
            connection_data = getattr(datasource, connection_field_name, {})

            # Execute query using enhanced ConnectionManager
            db_type = DatabaseType(datasource.type)

            # Execute with correct parameter ordering - pass dict directly
            result = await ConnectionManager.execute_query(
                db_type=db_type,
                connection_info=connection_data,
                query=sql,
                timeout=timeout,
                max_rows=max_rows,
                params=parameters,
                datasource_id=datasource_id,
            )

            # Update last_used_at timestamp using repository
            repo.update_datasource_last_used(datasource_id)

            # Calculate execution time
            execution_time_ms = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )
            row_count = len(result.get("rows", []))

            # Record successful query
            query_kwargs = {
                "id": query_id,
                "datasource_id": datasource_id,
                "sql": sql,
                "row_count": row_count,
                "executed_at": start_time,
                time_field_name: execution_time_ms,
            }

            # Add status field if present in the model
            if hasattr(QueryHistory, "status"):
                query_kwargs["status"] = "success"

            # Create query history using repository
            repo.create_query_history(query_kwargs)

            # Return results with query metadata
            return {
                "query_id": str(query_id),
                "sql": sql,
                "columns": result.get("columns", []),
                "rows": result.get("rows", []),
                "truncated": result.get("truncated", False),
                "row_count": row_count,
                "status": "success",
                "duration_ms": execution_time_ms,
            }

        except (NotFoundError, BadRequestError):
            raise

        except Exception as e:
            # Calculate execution time even for errors
            execution_time_ms = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )
            error = str(e)

            # Record failed query if we have a datasource_id
            try:
                if "datasource" in locals() and datasource:
                    # Create query history kwargs with appropriate field names
                    query_kwargs = {
                        "id": query_id,
                        "datasource_id": datasource_id,
                        "sql": sql,
                        "row_count": 0,
                        "error": error[:500],  # Limit error message length
                        "executed_at": start_time,
                        time_field_name: execution_time_ms,
                    }

                    # Add status field if present in the model
                    if hasattr(QueryHistory, "status"):
                        query_kwargs["status"] = "error"

                    # Create query history using repository
                    repo.create_query_history(query_kwargs)

            except Exception as record_error:
                logger.error(f"Failed to record query history: {record_error!s}")

            error_type = "syntax" if "syntax" in str(e).lower() else "execution"
            logger.error(f"Query error ({error_type}): {e!s}")

            return {
                "query_id": str(query_id),
                "sql": sql,
                "error": str(e),
                "error_type": error_type,
                "status": "error",
                "duration_ms": execution_time_ms,
            }

    @transactional
    async def get_schema_metadata(self, datasource_id: uuid.UUID) -> dict[str, Any]:
        """
        Get schema metadata with enhanced caching support.

        Uses the repository pattern and optimized ConnectionManager with
        improved error handling and performance.

        Args:
            db: Database session
            datasource_id: ID of the datasource

        Returns:
            Schema metadata (tables, views, etc.)

        Raises:
            NotFoundError: If datasource not found
            DatabaseError: For database-related errors
        """
        repo = self.repo

        try:
            # Get datasource using repository
            datasource = await repo.get_by_id_or_error(datasource_id)

            # Check which field contains connection info: connection_info or config
            model_has_connection_info = hasattr(datasource, "connection_info")
            connection_field_name = (
                "connection_info" if model_has_connection_info else "config"
            )

            # Get connection info from appropriate field
            connection_data = getattr(datasource, connection_field_name, {})

            # Get schema metadata using ConnectionManager with retries
            db_type = DatabaseType(datasource.type)

            # Use the more efficient schema metadata retrieval - pass dict directly
            metadata = await ConnectionManager.get_schema_metadata(
                db_type=db_type,
                connection_info=connection_data,
                datasource_id=datasource_id,
            )

            # Update last used timestamp using repository
            repo.update_datasource_last_used(datasource_id)

            return metadata

        except (NotFoundError, BadRequestError):
            raise

        except Exception as e:
            logger.error(f"Schema discovery error: {e!s}")
            raise DatabaseError(detail=f"Error fetching schema: {e!s}")

    def _sanitize_connection_info(
        self, connection_info: dict[str, Any], for_logging: bool = False
    ) -> dict[str, Any]:
        """
        Remove or mask sensitive information from connection_info.

        Args:
            connection_info: Original connection info
            for_logging: If True, mask sensitive values for logging

        Returns:
            Sanitized connection info
        """
        if not connection_info:
            return {}

        # Make a copy to avoid modifying the original
        sanitized = connection_info.copy()

        # Sensitive fields to handle
        sensitive_fields = [
            "password",
            "pwd",
            "secret",
            "token",
            "key",
            "api_key",
            "apikey",
            "credentials",
            "auth",
            "access_key",
            "secret_key",
            "certificate",
            "private_key",
        ]

        for field in sensitive_fields:
            if field in sanitized:
                if for_logging:
                    sanitized[field] = "********"  # Mask value for logs
                else:
                    # Store intact for database but don't modify
                    pass

        return sanitized

    def mask_connection_info(self, connection_info: dict[str, Any]) -> dict[str, Any]:
        """
        Mask sensitive information in connection_info for API responses.
        
        Args:
            connection_info: Original connection info
            
        Returns:
            Connection info with sensitive fields masked
        """
        if not connection_info:
            return {}
        
        # Make a copy to avoid modifying the original
        masked = connection_info.copy()
        
        # Sensitive fields to mask
        sensitive_fields = [
            "password",
            "pwd",
            "secret",
            "token",
            "key",
            "api_key",
            "apikey",
            "credentials",
            "auth",
            "access_key",
            "secret_key",
            "certificate",
            "private_key",
        ]
        
        for field in sensitive_fields:
            if field in masked and masked[field]:
                # Mask with asterisks, keeping first and last char if long enough
                value = str(masked[field])
                if len(value) > 4:
                    masked[field] = value[0] + "****" + value[-1]
                else:
                    masked[field] = "****"
        
        return masked
