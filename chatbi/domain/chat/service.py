"""
Chat service implementation using repository pattern.

This module provides services for handling chat functionality, including SQL generation,
data querying, and visualization generation with improved database access through
the repository pattern.
"""

import json
from functools import wraps
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import orjson
import pandas as pd
from fastapi import HTTPException, Request, status
from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Session

from chatbi.agent.schema_agent import SchemaAgent
from chatbi.agent.sql_agent import SqlAgent
from chatbi.agent.intent_agent import IntentClassificationAgent
from chatbi.agent.diagnosis_agent import DiagnosisAgent
from chatbi.agent.visualize_agent import VisualizeAgent
from chatbi.cache.base import Cache
from chatbi.cache.memory import MemoryCache
from chatbi.dependencies import transactional
from chatbi.domain.chat import ChatDTO, CommonResponse, RunSqlData
from chatbi.domain.chat.entities import ChatHistory, ChatSession
from chatbi.domain.chat.repository import (
    AsyncChatRepository,
    ChatRepository,
)
from chatbi.domain.datasource.repository import DatasourceRepository
from chatbi.domain.diagnosis.repository import CorrectionLogRepository, DiagnosisRepository
from chatbi.domain.diagnosis.entities import DiagnosisResult
from chatbi.domain.diagnosis.dtos import InsightSummary
# SQLExecutionPipeline imported locally to avoid circular dependency
from chatbi.database.connection_manager import ConnectionManager
from chatbi.domain.datasource import DatabaseType
from chatbi.domain.datasource.dtos import (
    ConnectionInfo,
    PostgresConnectionInfo,
    MySqlConnectionInfo,
    DuckDbConnectionInfo,
    MSSqlConnectionInfo,
    SnowflakeConnectionInfo,
    BigQueryConnectionInfo,
    ClickHouseConnectionInfo,
    TrinoConnectionInfo,
    ConnectionUrl
)
from chatbi.exceptions import BadRequestError, DatabaseError, NotFoundError


def requires_cache(
    required_fields: list[str], optional_fields: list[str] | None = None
):
    """
    Decorator to ensure required cache fields exist before executing a method.

    Args:
        required_fields: List of field names that must exist in the cache
        optional_fields: List of field names that are optional in the cache

    Returns:
        Decorated function that checks cache requirements

    Raises:
        HTTPException: If any required field is missing from the cache
    """
    if optional_fields is None:
        optional_fields = []

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            logger.debug(f"args: {args}")
            logger.debug(f"kwargs: {kwargs}")
            instance: ChatService = args[0]
            cache: Cache = instance.cache

            id = kwargs.get("id")
            logger.debug(f"Get id by request query: {id}")
            if id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ChatSession ID is required",
                )

            # Check for required fields in cache
            for field in required_fields:
                if cache.get(id=id, field=field) is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Missing required context: {field}",
                    )

            # Extract values from cache
            field_values = {
                field: cache.get(id=id, field=field) for field in required_fields
            }

            # Add optional fields if they exist
            for field in optional_fields:
                field_value = cache.get(id=id, field=field)
                if field_value is not None:
                    field_values[field] = field_value

            # Remove duplicates that already exist in kwargs
            field_values = {k: v for k, v in field_values.items() if k not in kwargs}

            logger.debug(f"field_values: {field_values}")
            return f(*args, **field_values, **kwargs)

        return decorated

    return decorator


class ChatService:
    """
    Service for chat functionality, including SQL generation, data querying,
    and visualization generation using the repository pattern.
    """

    _MAX_ROWS_DEFAULT = 1000
    _table_schema = None

    def __init__(self, repo: ChatRepository, datasource_repo: DatasourceRepository = None, cache: Cache = None):
        """
        Initialize the chat service with repository and cache dependencies.

        Args:
            repo: Chat repository for database access (required)
            datasource_repo: Datasource repository for schema access (optional)
            cache: Cache implementation (defaults to MemoryCache)
        """

        if repo is None:
            raise ValueError("ChatRepository is required")

        self.repo = repo
        self.datasource_repo = datasource_repo
        self.cache = cache or MemoryCache()
        self.correction_repo = CorrectionLogRepository(repo.db)
        self.diagnosis_repo = DiagnosisRepository(repo.db)
        self.sql_agent = SqlAgent()
        self.schema_agent = SchemaAgent()
        self.visualize_agent = VisualizeAgent()
        self.diagnosis_agent = DiagnosisAgent()
        self.intent_agent = IntentClassificationAgent()

    def set_cache(self, id: str, value: str = "test") -> str:
        """
        Set a test value in the cache.

        Args:
            id: Cache identifier
            value: Value to store

        Returns:
            The stored value
        """
        self.cache.set(id, "test_field", value)
        return self.cache.get(id, "test_field")

    @requires_cache(["test_field"])
    def get_cache(self, requiest: Request, id: str, test_field: str) -> str:
        """
        Get a test value from the cache.

        Args:
            requiest: FastAPI request object
            id: Cache identifier
            test_field: Field from cache (injected by decorator)

        Returns:
            The cached value
        """
        logger.debug(f"test_field: {test_field}")
        return test_field

    def get_ChatSession(self, id: str) -> Optional[ChatSession]:
        """
        Get a chat session by ID using the repository.

        Args:
            id: Chat session ID

        Returns:
            The chat session if found, None otherwise
        """
        try:
            return self.repo.get_chat_session_by_id(id)
        except Exception as e:
            logger.error(f"Error retrieving chat session: {e!s}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve chat session: {e!s}",
            )

    @transactional
    def init_ChatSession(self, dto: ChatDTO) -> ChatSession:
        """
        Initialize a new chat session using the repository.

        Args:
            dto: Chat data transfer object

        Returns:
            Newly created chat session
        """
        try:
            repo = self.repo

            # Create session data dictionary
            session_id = str(uuid4())
            session_data = {
                "id": session_id,
                "user_id": dto.user_id or "anonymous",
                "title": dto.text[:50] if dto.text else "New ChatSession",
                "status": "active",
            }

            # If data source is provided, associate it
            if dto.datasource_id:
                session_data["datasource_id"] = dto.datasource_id

            # Create session through repository
            chat_session = repo.create_chat_session(session_data)

            # Create an initial message if text is provided
            if dto.text:
                message_data = {
                    "session_id": session_id,
                    "role": "user",
                    "content": dto.text,
                }
                repo.add_chat_message(message_data)

            return chat_session
        except Exception as e:
            logger.error(f"Error initializing chat session: {e!s}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create chat session: {e!s}",
            )

    async def get_table_schema(self, datasource_id: Optional[str] = None) -> Any:
        """
        Get the database schema.

        Args:
            datasource_id: Optional ID of specific datasource to fetch schema from

        Returns:
            Schema sort of as a list of table definitions
        """
        if self._table_schema:
            return self._table_schema

        schemas = []
        if self.datasource_repo:
            try:
                # Fetch specified datasource or all active ones
                datasources = []
                if datasource_id:
                    ds = await self.datasource_repo.get_by_id(datasource_id)
                    if ds:
                        datasources.append(ds)
                else:
                    # Only fetch active datasources
                    datasources = await self.datasource_repo.get_all(status_filter="active")

                logger.debug(f"Found {len(datasources)} datasources to fetch schema from")

                for ds in datasources:
                    try:
                        # Convert config to ConnectionInfo
                        conn_info_dict = getattr(ds, "connection_info", getattr(ds, "config", {}))

                        if not conn_info_dict:
                            continue

                        # Convert all values to string for SecretStr compatibility
                        conn_info_dict = {k: str(v) for k, v in conn_info_dict.items()}

                        conn_info = None
                        ds_type = ds.type.lower() if ds.type else ""

                        if ds_type == 'postgres':
                            conn_info = PostgresConnectionInfo(**conn_info_dict)
                        elif ds_type == 'mysql':
                            conn_info = MySqlConnectionInfo(**conn_info_dict)
                        elif ds_type == 'duckdb':
                            conn_info = DuckDbConnectionInfo(**conn_info_dict)
                        elif ds_type == 'mssql':
                            conn_info = MSSqlConnectionInfo(**conn_info_dict)
                        elif ds_type == 'snowflake':
                            conn_info = SnowflakeConnectionInfo(**conn_info_dict)
                        elif ds_type == 'bigquery':
                            conn_info = BigQueryConnectionInfo(**conn_info_dict)
                        elif ds_type == 'clickhouse':
                            conn_info = ClickHouseConnectionInfo(**conn_info_dict)
                        elif ds_type == 'trino':
                            conn_info = TrinoConnectionInfo(**conn_info_dict)
                        elif 'url' in conn_info_dict or 'connectionUrl' in conn_info_dict:
                            conn_info = ConnectionUrl(**conn_info_dict)
                        
                        if not conn_info:
                            logger.warning(f"Could not create ConnectionInfo for datasource type: {ds.type}")
                            continue

                        db_type = DatabaseType(ds.type)

                        # Fetch schema metadata
                        meta = await ConnectionManager.get_schema_metadata(db_type, conn_info)

                        if meta and "tables" in meta:
                            tables = meta["tables"]
                            logger.debug(f"Fetched {len(tables)} tables from datasource {ds.name}")
                            schemas.extend(tables)
                    except Exception as e:
                        logger.warning(f"Failed to fetch schema for datasource {ds.name}: {e}")

            except Exception as e:
                logger.error(f"Error fetching datasources: {e}")
        else:
            logger.warning("No datasource repository available. Returning empty schema.")

        if not schemas:
            logger.warning("No schemas found from datasources. Using empty schema.")

        self._table_schema = schemas
        logger.debug(f"Table schema: {self._table_schema}")
        return self._table_schema

    @transactional
    async def analysis(
        self,
        request: Request,
        dto: ChatDTO,
    ) -> dict[str, Any]:
        """
        Complete analysis pipeline for a chat request.

        Args:
            request: FastAPI request object
            dto: Chat data transfer object
        Returns:
            Analysis results including SQL, data and visualization

        Raises:
            HTTPException: If analysis fails
        """
        try:
            # Initialize ChatSession ID if needed
            id = dto.id or self.cache.generate_id(question=dto.text)
            question = dto.question
            table_schema = dto.table_schema
            response = {}

            repo = self.repo
            
            # Step 0: Intent Classification
            try:
                intent_msg = await self.intent_agent.replay(question=question)
                intent = intent_msg.intent
                logger.info(f"Detected intent: {intent}")
                response["intent"] = intent
                
                if intent == "clarification":
                    logger.info(f"Ambiguity detected, returning clarification request")
                    response["metadata"] = intent_msg.metadata
                    # We can choose to return immediately or populate fields with defaults
                    # For now, we return, because we can't generate SQL sensibly.
                    # But we maintain the shape of ChatAnalysisResponse
                    return {
                        "intent": "clarification",
                        "answer": intent_msg.content, # This might go into message?
                        # Response structure expected by router/frontend
                        "table_schema": None,
                        "sql": None,
                        "data": None,
                        "should_visualize": False,
                        "visualize_config": None,
                        "metadata": intent_msg.metadata
                    }
            except Exception as e:
                logger.error(f"Intent classification failed: {e}")
                # Fallback to query if failed
                response["intent"] = "query"

            # Step 1: Get table schema if not provided
            if table_schema is None:
                all_table_schema = await self.get_table_schema()
                logger.debug(f"Retrieved all_table_schema type: {type(all_table_schema)}, length: {len(all_table_schema) if isinstance(all_table_schema, (list, str)) else 'N/A'}")

                # Retrieve relevant table schemas using SchemaAgent
                schema_response = self.schema_agent.reply(
                    id=id,
                    question=question,
                    table_schema=all_table_schema,
                )
                table_schema = schema_response.answer
                logger.debug(f"SchemaAgent returned table_schema type: {type(table_schema)}, length: {len(table_schema) if isinstance(table_schema, list) else 'N/A'}")
                
                # Fallback: if SchemaAgent returns empty result, use all tables
                if not table_schema or (isinstance(table_schema, list) and len(table_schema) == 0):
                    logger.warning(f"SchemaAgent returned empty schema, falling back to all tables")
                    table_schema = all_table_schema
                
                # Store the list version for response
                response["table_schema"] = table_schema

            logger.debug(f"Final table schema type: {type(table_schema)}")
            
            # Validate table schema is not completely empty
            is_empty = False
            if table_schema is None:
                is_empty = True
            elif isinstance(table_schema, str) and (table_schema == "" or table_schema == "[]"):
                is_empty = True
            elif isinstance(table_schema, list) and len(table_schema) == 0:
                is_empty = True
            
            if is_empty:
                logger.error("Empty table schema - cannot generate SQL without schema information")
                raise HTTPException(
                    status_code=status.HTTP_424_FAILED_DEPENDENCY,
                    detail="No database schema available. Please ensure a data source is connected and configured properly."
                )
            
            dto.table_schema = table_schema

            # Step 2: Generate SQL from question
            generate_sql_result = await self.generate_sql(
                request=request, id=id, question=question, table_schema=table_schema
            )
            sql = generate_sql_result.answer

            # Additional cleaning in case the agent returned markdown
            if "```" in sql:
                sql = sql.replace("```sql", "").replace("```", "").strip()

            logger.debug(f"Generated SQL: {sql}")
            response["sql"] = sql

            # Validate SQL - reject if it contains failure messages or invalid formats
            sql_stripped = sql.strip()
            sql_upper = sql_stripped.upper()
            
            # Check for failure indicators
            failure_indicators = [
                "无法生成", "UNABLE TO", "CANNOT GENERATE", "INSUFFICIENT",
                "CAN'T GENERATE", "NOT ENOUGH", "MISSING"
            ]
            if any(indicator in sql_upper for indicator in failure_indicators):
                logger.warning(f"SQL agent returned failure message: {sql}")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Unable to generate SQL query. The AI model indicated insufficient context or unclear question. Please provide more details or rephrase your question."
                )
            
            # Remove leading comments and check for valid SQL
            sql_no_comments = sql_stripped
            while sql_no_comments.startswith("--"):
                lines = sql_no_comments.split("\n", 1)
                if len(lines) > 1:
                    sql_no_comments = lines[1].strip()
                else:
                    sql_no_comments = ""
                    break
            
            # Allow common SQL starting keywords
            valid_starters = ("SELECT", "WITH", "SHOW", "DESC", "EXPLAIN", "VALUES", "INSERT", "UPDATE", "DELETE")
            if not sql_no_comments or not sql_no_comments.upper().startswith(valid_starters):
                logger.warning(f"Invalid SQL generated: {sql}")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Failed to generate valid SQL query. Please ensure your question is clear and relates to the available data."
                )
            
            # Use the cleaned SQL without leading comments
            sql = sql_no_comments

            # Step 3: Run the generated SQL (limit to 20 rows for frontend performance)
            run_sql_result = await self.run_sql(request=request, id=id, sql=sql, max_rows=20)
            response["data"] = run_sql_result.data
            response["should_visualize"] = run_sql_result.should_visualize

            # Use executed_sql for visualization if it changed
            if run_sql_result.executed_sql:
                response["executed_sql"] = run_sql_result.executed_sql
                response["insight"] = run_sql_result.insight.model_dump() if run_sql_result.insight else None
                sql = run_sql_result.executed_sql # Update sql variable for visualization step

            # Step 4: Generate visualization if requested
            if dto.visualize:
                data_sample = None
                try:
                    data_list = json.loads(run_sql_result.data)
                    # Use up to 3 records as sample data to help LLM understand data structure
                    if isinstance(data_list, list) and len(data_list) > 0:
                        data_sample = data_list[:3]
                except Exception as e:
                    logger.warning(f"Failed to parse data for visualization sample: {e}")

                visualize_agent_result = self.visualize_agent.reply(
                    id=id, 
                    question=question, 
                    sql=sql, 
                    table_schema=table_schema,
                    data=data_sample
                )
                visualize_config = visualize_agent_result.answer
                
                # Check if visualize_config is a valid dictionary
                if isinstance(visualize_config, dict):
                    response["visualize_config"] = visualize_config
                    logger.debug(f"Generated Chart Config: {visualize_config}")
                    self.cache.set(id, "visualize_config", visualize_config)
                else:
                    logger.warning(f"Visualize agent returned invalid config type: {type(visualize_config)} - {visualize_config}")
                    response["visualize_config"] = None

            # Store data in cache for future use ONLY if analysis was successful
            # Verification logic:
            # 1. SQL was generated (implicit if we are here)
            # 2. If visualization was requested, config must be valid
            should_cache = True
            
            if dto.visualize and response.get("visualize_config") is None:
                should_cache = False
                logger.warning(f"Analysis cache skipped due to invalid visualization config for ID {id}")
            
            if should_cache:
                self.cache.set(id, "question", question)
                self.cache.set(id, "table_schema", table_schema)
                self.cache.set(id, "sql", sql)
            
            # Record analysis metrics and history
            try:
                # Save history record
                history_data = {
                    "conversation_id": id,
                    "question": question,
                    "sql": sql,
                    "success": True,
                    # Add additional metrics here
                }
                repo.save_chat_history(history_data)
            except Exception as e:
                # Just log the error, don't fail the request
                logger.error(f"Failed to record chat history: {e}")

            return response

        except Exception as e:
            logger.error(f"Error in analysis: {e!s}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Analysis failed: {e!s}",
            )

    @transactional
    async def generate_sql(
        self,
        request: Request,
        id: Optional[str],
        question: str,
        table_schema: Optional[Union[str, list]] = None,
    ) -> CommonResponse:
        """
        Generate SQL query from natural language question.

        Args:
            request: FastAPI request object
            id: ChatSession ID (optional)
            question: Natural language question

        Returns:
            Agent response containing SQL

        Raises:
            HTTPException: If SQL generation fails
        """
        try:
            # Generate ChatSession ID if not provided
            if id is None:
                id = self.cache.generate_id(question=question)

            logger.debug(f"Current ChatSession ID: {id}")

            # Get relevant table schema if not provided
            if table_schema is None:
                logger.debug(f"Step 1: Getting all table schema")
                all_table_schema = await self.get_table_schema()
                logger.debug(f"Step 2: all_table_schema = {all_table_schema}, type = {type(all_table_schema)}")
                schema_response = self.schema_agent.reply(
                    id=id,
                    question=question,
                    table_schema=all_table_schema,
                )
                logger.debug(f"Step 3: schema_response = {schema_response}")
                table_schema = schema_response.answer
                logger.debug(f"Step 4: table_schema = {table_schema}, type = {type(table_schema)}")
                # Convert empty list to string to avoid JSON serialization issues
                if isinstance(table_schema, list) and len(table_schema) == 0:
                    table_schema = "[]"
                logger.debug(f"Step 5: Final table_schema = {table_schema}")

            # Generate SQL from question
            # Convert table_schema to JSON string if it's a list for better LLM understanding
            table_schema_str = table_schema
            if isinstance(table_schema, list):
                # Log table names for debugging
                table_names = [t.get('name', 'unknown') for t in table_schema if isinstance(t, dict)]
                logger.info(f"Schema contains {len(table_schema)} tables: {', '.join(table_names)}")
                table_schema_str = json.dumps(table_schema, ensure_ascii=False, indent=2)
            
            logger.debug(f"About to call sql_agent.reply with table_schema type: {type(table_schema_str)}")
            logger.info(f"Table schema being sent to SQL Agent (first 500 chars): {str(table_schema_str)[:500]}")
            response = self.sql_agent.reply(
                id=id,
                question=question,
                table_schema=table_schema_str,
            )
            logger.debug(f"SQL agent response type: {type(response)}, value: {response}")
            sql = response.answer
            # Clean SQL from markdown code blocks if present
            if "```" in sql:
                sql = sql.replace("```sql", "").replace("```", "").strip()
            
            logger.debug(f"Generated SQL: {sql}")

            # Store in cache
            self.cache.set(id, "question", question)
            self.cache.set(id, "table_schema", table_schema)
            self.cache.set(id, "sql", sql)

            repo = self.repo

            # Record SQL generation if successful
            try:
                history_data = {
                    "conversation_id": id,
                    "question": question,
                    "sql": sql,
                    "success": True,
                }
                await repo.save_chat_history(history_data)
            except Exception as e:
                # Just log the error, don't fail the request
                logger.error(f"Failed to record SQL generation history: {e}")

            return response

        except Exception as e:
            logger.error(f"Error in generate_sql: {e!s}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"SQL generation failed: {e!s}",
            )

    async def _execute_sql_core(
        self, 
        sql: str, 
        timeout: int = 30, 
        max_rows: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Internal method to execute SQL, serialize results, and handle basics.
        """
        # Clean SQL from markdown code blocks if present
        if "```" in sql:
            sql = sql.replace("```sql", "").replace("```", "").strip()

        # Ensure queries have a row limit for safety
        if max_rows and "limit" not in sql.lower():
            if sql.endswith(";"):
                sql = f"{sql[:-1]} LIMIT {max_rows};"
            else:
                sql = f"{sql} LIMIT {max_rows};"

        # Get all active datasources
        datasources = await self.datasource_repo.get_all()
        if not datasources or len(datasources) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No datasource found. Please configure a datasource first.",
            )

        # Use the first active datasource
        datasource = datasources[0]
        
        # Execute query using connection manager
        from chatbi.database.connection_manager import connection_manager

        # Convert string type to DatabaseType enum
        try:
            database_type = DatabaseType(datasource.type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported database type: {datasource.type}",
            )

        result = await connection_manager.execute_query(
            db_type=database_type,
            connection_info=datasource.connection_info,
            query=sql,
            timeout=timeout,
            max_rows=max_rows,
        )

        # Convert result to DataFrame format for compatibility
        rows = result.get("rows", [])
        
        # Convert datetime objects to ISO format strings for JSON serialization
        def serialize_datetime(obj):
            """Convert datetime and date objects to ISO format strings"""
            from datetime import datetime, date
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            return obj
        
        # Process each row to convert datetime objects
        serialized_rows = []
        for row in rows:
            if isinstance(row, dict):
                serialized_row = {k: serialize_datetime(v) for k, v in row.items()}
                serialized_rows.append(serialized_row)
            else:
                serialized_rows.append(row)
                
        return serialized_rows

    async def run_sql(
        self,
        request: Request,
        id: str,
        sql: str,
        timeout: Optional[int] = 30,
        max_rows: Optional[int] = 20,
    ) -> RunSqlData:
        """
        Run SQL query and return results.

        Args:
            request: FastAPI request object
            id: ChatSession ID
            sql: SQL query to execute
            timeout: Query timeout in seconds
            max_rows: Maximum number of rows to return

        Returns:
            Query results and visualization flag

        Raises:
            HTTPException: If query execution fails
        """
        try:
            logger.debug(f"Execute SQL: {sql}")
            
            # Retrieve context from cache for retry logic
            question = self.cache.get(id, "question") or "Unknown Question"
            table_schema = self.cache.get(id, "table_schema") or "[]"
            if isinstance(table_schema, list):
                table_schema = json.dumps(table_schema, ensure_ascii=False)

            # Define execution function for the pipeline
            async def execute_func(query_sql: str):
                return await self._execute_sql_core(
                    sql=query_sql, 
                    timeout=timeout or 30, 
                    max_rows=max_rows or 1000
                )

            # Local import to avoid circular dependency
            from chatbi.pipelines.execution.execution_pipeline import SQLExecutionPipeline

            # Initialize pipeline
            pipeline = SQLExecutionPipeline(
                sql_agent=self.sql_agent,
                correction_repo=self.correction_repo,
                execute_sql_func=execute_func,
                max_retries=3
            )

            # Run pipeline
            final_sql, serialized_rows = await pipeline.run(
                query_id=id,
                initial_sql=sql,
                question=question,
                table_schema=table_schema if isinstance(table_schema, str) else str(table_schema)
            )

            logger.debug(f"Query returned {len(serialized_rows)} rows")

            # Record SQL execution statistics (for the successful run)
            try:
                history_data = {
                    "conversation_id": id,
                    "sql": final_sql,
                    "row_count": len(serialized_rows),
                    "success": True,
                    "error_message": None,
                }
                if self.repo.is_async:
                    await self.repo.save_chat_history(history_data)
                else:
                    self.repo.save_chat_history(history_data)
            except Exception as e:
                # Just log the error, don't fail the request
                logger.error(f"Failed to record SQL execution history: {e}")

            # Determine if visualization should be generated
            should_visualize = len(serialized_rows) > 1 if serialized_rows else False

            # Generate insights
            insight = None
            if len(serialized_rows) > 0:
                try:
                    # Use sample data for insight generation
                    sample_rows = serialized_rows[:20]
                    data_sample = json.dumps(sample_rows, ensure_ascii=False)
                    
                    logger.debug("Requesting data diagnosis...")
                    agent_resp = self.diagnosis_agent.reply(
                        id=id, 
                        question=question, 
                        sql=final_sql, 
                        data_sample=data_sample
                    )
                    
                    insight_data = agent_resp.answer
                    if isinstance(insight_data, dict):
                        # Save to database
                        diagnosis_result = DiagnosisResult(
                            query_id=id,
                            summary=insight_data.get("summary", ""),
                            key_points=insight_data.get("key_points", [])
                        )
                        await self.diagnosis_repo.create(diagnosis_result)
                        
                        insight = InsightSummary(**insight_data)
                except Exception as e:
                    logger.warning(f"Failed to generate insight: {e}")

            return RunSqlData(
                data=json.dumps(serialized_rows),
                should_visualize=should_visualize,
                executed_sql=final_sql,
                insight=insight,
            )

        except Exception as e:
            logger.error(f"Error executing SQL: {e!s}")

            # Record SQL execution error
            try:
                history_data = {
                    "conversation_id": id,
                    "sql": sql,
                    "success": False,
                    "error_message": str(e),
                }
                self.repo.save_chat_history(history_data)
            except Exception as log_e:
                logger.error(f"Failed to record SQL execution error: {log_e}")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Query execution failed: {e!s}",
            )

    @requires_cache(["question", "sql", "table_schema"])
    def generate_visualize(
        self,
        request: Request,
        id: str,
        question: str,
        sql: str,
        table_schema: str,
    ) -> CommonResponse:
        """
        Generate visualization configuration for query results.

        Args:
            request: FastAPI request object
            id: ChatSession ID
            data: Query result data
            question: Natural language question (injected by decorator)
            sql: SQL query (injected by decorator)
            table_schema: Table schema (injected by decorator)

        Returns:
            Visualization configuration

        Raises:
            HTTPException: If visualization generation fails
        """
        try:
            response = self.visualize_agent.reply(
                id=id, question=question, sql=sql, table_schema=table_schema
            )

            # Cache the visualization config
            self.cache.set(id, "visualize_config", response.answer)
            logger.debug(f"Visualization config: {response.answer}")

            return response

        except Exception as e:
            logger.error(f"Error generating visualization: {e!s}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Visualization generation failed: {e!s}",
            )

    def should_visualize(self, df: pd.DataFrame) -> bool:
        """
        Determine if data is suitable for visualization.

        Args:
            df: DataFrame with query results

        Returns:
            True if visualization should be generated
        """
        # Check if there's enough data and numerical columns for visualization
        return bool(len(df) > 1 and df.select_dtypes(include=["number"]).shape[1] > 0)
