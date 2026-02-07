"""
Chat router with improved database dependency injection.

This module provides FastAPI routes for handling chat functionality with standardized responses.
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from chatbi.dependencies import PostgresSessionDep, RepositoryDependency
from chatbi.domain.chat.dtos import (
    AnalysisResult,
    CacheResponse,
    ChatDTO,
    CommonResponse,
    ConversationResponse,
    RunSqlData,
    RunSqlRequest,
    SqlResultResponse,
    ChatAnalysisResponse,
)
from chatbi.domain.chat.repository import ChatRepository
from chatbi.domain.chat.service import ChatService
from chatbi.domain.datasource.repository import DatasourceRepository
from chatbi.middleware.standard_response import StandardResponse

# Create unified dependency provider for repository
# By default, use synchronous session for backward compatibility
ChatRepoDep = RepositoryDependency(ChatRepository)
# Use async session for datasource repo compatibility with ConnectionManager
DatasourceRepoDep = RepositoryDependency(DatasourceRepository, use_async_session=True)

# Create router instance
router = APIRouter(
    prefix="/api/v1/chat",
    tags=["Chat"],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Resource not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "An unexpected error occurred", "code": 500}
                }
            },
        },
    },
)


@router.post(
    "/test",
    response_model=StandardResponse,
    summary="Test chat endpoint",
    description="Simple test endpoint for chat functionality verification",
)
async def test_chat(request: Request, dto: ChatDTO) -> StandardResponse:
    """
    Test endpoint for chat functionality.

    Args:
        request: FastAPI request object
        dto: Chat data

    Returns:
        Standardized response with test data
    """
    return StandardResponse(
        status="success",
        message="Chat test successful",
        data={"request": dto.model_dump()},
    )


@router.get(
    "/cache/set",
    response_model=StandardResponse[CacheResponse],
    summary="Set cache value",
    description="Set a test value in the cache system",
)
async def set_cache(request: Request) -> StandardResponse[CacheResponse]:
    """
    Set a test value in cache.

    Args:
        request: FastAPI request object

    Returns:
        Standardized response with cache result
    """
    id = request.query_params.get("id", "test-id")
    value = request.query_params.get("value", "test-value")

    # Create chat service with repository
    repo = ChatRepository(request.state.db)  # Use db from middleware
    chat_service = ChatService(repo)
    result = chat_service.set_cache(id, value)

    return StandardResponse(
        status="success",
        message="Cache value set successfully",
        data=CacheResponse(id=id, value=result),
    )


@router.get(
    "/cache/get",
    response_model=StandardResponse[CacheResponse],
    summary="Get cached value",
    description="Retrieve a test value from the cache system",
)
async def get_cache(
    request: Request, repo: ChatRepository = Depends(ChatRepoDep)
) -> StandardResponse[CacheResponse]:
    """
    Get a test value from cache.

    Args:
        request: FastAPI request object

    Returns:
        Standardized response with cached value
    """
    id = request.query_params.get("id", "test-id")

    # Use chat service to get cache
    chat_service = ChatService(repo=repo)
    result = chat_service.get_cache(request, id)

    return StandardResponse(
        status="success",
        message="Cache value retrieved successfully",
        data=CacheResponse(id=id, value=result),
    )


@router.get(
    "/{id}",
    response_model=StandardResponse[ConversationResponse],
    summary="Get conversation",
    description="Retrieve a conversation by its ID",
)
async def get_session(
    request: Request,
    id: str,
    repo: ChatRepository = Depends(ChatRepoDep),
) -> StandardResponse[ConversationResponse]:
    """
    Get a conversation by ID.

    Args:
        request: FastAPI request object
        id: Conversation ID
        repo: Repository instance from dependency

    Returns:
        Standardized response with conversation data
    """
    chat_service = ChatService(repo=repo)
    chat_session = chat_service.get_ChatSession(id)

    return StandardResponse(
        status="success",
        message="Conversation retrieved successfully",
        data=ConversationResponse(session=chat_session),
    )


@router.post(
    "/init",
    response_model=StandardResponse[ConversationResponse],
    summary="Initialize conversation",
    description="Create a new conversation session",
)
async def init_conversation(
    request: Request,
    dto: ChatDTO,
    repo: ChatRepository = Depends(ChatRepoDep),
) -> StandardResponse[ConversationResponse]:
    """
    Initialize a new conversation.

    Args:
        request: FastAPI request object
        dto: Chat data
        db: Database session from dependency
        repo: Repository instance from dependency

    Returns:
        Standardized response with new conversation data
    """
    chat_service = ChatService(repo=repo)
    conversation = chat_service.init_conversation(dto)

    return StandardResponse(
        status="success",
        message="Conversation initialized successfully",
        data=ConversationResponse(conversation=conversation),
    )


@router.post(
    "/",
    response_model=StandardResponse[ChatAnalysisResponse],
    summary="Analyze chat message",
    description="Process a chat message and generate insights",
)
async def analyze(
    request: Request,
    dto: ChatDTO,
    repo: ChatRepository = Depends(ChatRepoDep),
    datasource_repo: DatasourceRepository = Depends(DatasourceRepoDep),
) -> StandardResponse[ChatAnalysisResponse]:
    """
    Analyze a chat request and generate insights.

    Args:
        request: FastAPI request object
        dto: Chat data
        repo: Repository instance from dependency
        datasource_repo: Datasource repository instance

    Returns:
        Standardized response with analysis results
    """
    chat_service = ChatService(repo=repo, datasource_repo=datasource_repo)
    result = await chat_service.analysis(request, dto)

    return StandardResponse(
        status="success", message="Analysis completed successfully", data=result
    )


@router.post(
    "/generate_sql",
    response_model=StandardResponse[CommonResponse],
    summary="Generate SQL",
    description="Convert natural language question to SQL query",
)
async def generate_sql(
    request: Request,
    dto: ChatDTO,
    repo: ChatRepository = Depends(ChatRepoDep),
    datasource_repo: DatasourceRepository = Depends(DatasourceRepoDep),
) -> StandardResponse[CommonResponse]:
    """
    Generate SQL from natural language question.

    Args:
        request: FastAPI request object
        dto: Chat data
        repo: Repository instance from dependency
        datasource_repo: Datasource repository instance

    Returns:
        Standardized response with generated SQL
    """
    chat_service = ChatService(repo=repo, datasource_repo=datasource_repo)
    result = await chat_service.generate_sql(request, dto.id, dto.question)

    # Convert AgentMessage to CommonResponse
    response_data = CommonResponse(
        status="success",
        answer=result.answer if hasattr(result, 'answer') else str(result),
        message=result.reason if hasattr(result, 'reason') else None
    )

    return StandardResponse(
        status="success", message="SQL generated successfully", data=response_data
    )


@router.post(
    "/run_sql",
    response_model=StandardResponse[SqlResultResponse],
    summary="Execute SQL",
    description="Run SQL query and return results",
)
async def run_sql(
    request: Request,
    dto: RunSqlRequest,
    repo: ChatRepository = Depends(ChatRepoDep),
    datasource_repo: DatasourceRepository = Depends(DatasourceRepoDep),
) -> StandardResponse[SqlResultResponse]:
    """
    Execute SQL query and return results.

    Args:
        request: FastAPI request object
        dto: Run SQL request data
        repo: Repository instance from dependency
        datasource_repo: Datasource repository instance

    Returns:
        Standardized response with query results
    """
    chat_service = ChatService(repo=repo, datasource_repo=datasource_repo)
    result = await chat_service.run_sql(request, dto.id, dto.sql, dto.timeout, dto.max_rows)

    # Parse JSON string to list
    import json
    data_list = json.loads(result.data) if isinstance(result.data, str) else result.data

    return StandardResponse(
        status="success",
        message="SQL query executed successfully",
        data=SqlResultResponse(
            data=data_list, 
            should_visualize=result.should_visualize,
            executed_sql=result.executed_sql,
            insight=result.insight
        ),
    )


@router.post(
    "/generate_visualize",
    response_model=StandardResponse[CommonResponse],
    summary="Generate visualization",
    description="Create visualization configuration for query results",
)
async def generate_visualize(
    request: Request,
    dto: ChatDTO,
    repo: ChatRepository = Depends(ChatRepoDep),
) -> StandardResponse[CommonResponse]:
    """
    Generate visualization configuration for query results.

    Args:
        request: FastAPI request object
        dto: Chat data
        repo: Repository instance from dependency

    Returns:
        Standardized response with visualization configuration
    """
    chat_service = ChatService(repo=repo)
    result = chat_service.generate_visualize(request=request, id=dto.id, sql=dto.text)

    return StandardResponse(
        status="success", message="Visualization generated successfully", data=result
    )
