"""
Core domain models for chat functionality.

This module defines the key business entities and value objects for chat functionality,
independent of their persistence mechanism or API representation.
"""

from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, validator


class MessageRole(str, Enum):
    """Roles for message participants in a chat conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message:
    """
    Represents a single message in a conversation.

    This is a pure domain entity representing a message in a chat.
    """

    def __init__(
        self,
        role: MessageRole,
        content: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.utcnow()
        self.metadata = metadata or {}


class ConversationContext:
    """
    Represents the context maintained for a conversation.

    This includes things like the current schema, generated SQL,
    and other state that needs to be maintained across messages.
    """

    def __init__(
        self,
        table_schema: Optional[str] = None,
        sql: Optional[str] = None,
        question: Optional[str] = None,
        visualize_config: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        self.table_schema = table_schema
        self.sql = sql
        self.question = question
        self.visualize_config = visualize_config
        self.metadata = metadata or {}


class ChatSession:
    """
    Represents a chat session consisting of multiple messages.
    """

    def __init__(
        self,
        id: str,
        title: Optional[str] = None,
        messages: Optional[list[Message]] = None,
        context: Optional[ConversationContext] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.title = title
        self.messages = messages or []
        self.context = context or ConversationContext()
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or self.created_at

class ClarificationOption(BaseModel):
    """Option for user clarification."""
    label: str
    value: str
    description: Optional[str] = None

class ClarificationRequest(BaseModel):
    """Request for user clarification when intent is ambiguous."""
    question: str
    options: List[ClarificationOption] = Field(default_factory=list)
    ambiguity_type: str
