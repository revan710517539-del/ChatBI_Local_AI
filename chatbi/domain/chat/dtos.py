"""
Chat Data Transfer Objects (DTOs).

This module contains DTOs used for communication between the API and service layers.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


class ChatDTO(BaseModel):
    """
    Data Transfer Object for chat requests.
    """

    id: Optional[str] = None
    text: Optional[str] = None
    question: str
    table_schema: Optional[str] = None
    visualize: bool = True


class GenerateSqlRequest(BaseModel):
    """
    Request model for generating SQL.
    """

    id: Optional[str] = None
    question: str
    table_schema: Optional[str] = None


class RunSqlRequest(BaseModel):
    """
    Request model for executing SQL.
    """

    id: str
    sql: str
    timeout: Optional[int] = 30
    max_rows: Optional[int] = 1000

from chatbi.domain.diagnosis.dtos import InsightSummary

class RunSqlData(BaseModel):
    """
    Result model for SQL execution, used internally.
    """

    data: str  # JSON string of records
    should_visualize: bool
    executed_sql: Optional[str] = None
    insight: Optional[InsightSummary] = None


class RunSqlResponse(BaseModel):
    """
    Response model for SQL execution results.
    """

    data: list[dict[str, Any]]
    should_visualize: bool
    executed_sql: Optional[str] = None
    insight: Optional[InsightSummary] = None


class CommonResponse(BaseModel):
    """
    Common response format for chat operations.
    """

    status: str
    answer: Union[str, dict[str, Any], list[dict[str, Any]]]
    message: Optional[str] = None


# New response models for chat endpoints


class CacheResponse(BaseModel):
    """
    Response model for cache operations.
    """

    id: str = Field(..., description="Cache key identifier")
    value: Any = Field(..., description="Cached value")


class Message(BaseModel):
    """
    Model for a chat message.
    """

    id: str = Field(..., description="Message identifier")
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    created_at: datetime = Field(..., description="Message creation timestamp")


class Conversation(BaseModel):
    """
    Model for a conversation, including metadata and messages.
    """

    id: str = Field(..., description="Conversation identifier")
    title: str = Field(..., description="Conversation title")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    messages: list[Message] = Field(
        default_factory=list, description="Conversation messages"
    )
    metadata: Optional[dict[str, Any]] = Field(
        None, description="Additional conversation metadata"
    )


class ConversationResponse(BaseModel):
    """
    Response model for conversation operations.
    """

    conversation: Conversation = Field(..., description="Conversation data")


class AnalysisResult(BaseModel):
    """
    Model for analysis results.
    """

    intent: str = Field(..., description="Detected user intent")
    entities: list[dict[str, Any]] = Field(
        default_factory=list, description="Extracted entities"
    )
    suggestions: Optional[list[str]] = Field(
        None, description="Suggested follow-up questions"
    )
    sentiment: Optional[str] = Field(None, description="Detected sentiment")
    confidence: float = Field(..., description="Confidence score for the analysis")
    response: str = Field(..., description="Generated response")
    context: Optional[dict[str, Any]] = Field(None, description="Context information")


class SqlResultResponse(BaseModel):
    """
    Response model for SQL execution results.
    """

    data: list[dict[str, Any]] = Field(..., description="SQL query result data")
    should_visualize: bool = Field(
        ..., description="Whether visualization is recommended"
    )

class ChatAnalysisResponse(BaseModel):
    """
    Response model for chat analysis.
    """
    table_schema: Optional[List[Dict[str, Any]]] = None
    sql: Optional[str] = None
    data: Optional[str] = None
    should_visualize: Optional[bool] = False
    visualize_config: Optional[Dict[str, Any]] = None
    executed_sql: Optional[str] = None
    insight: Optional[InsightSummary] = None
    intent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
