"""
Chat domain models and business logic.

This module contains all domain entities and DTOs for chat functionality.
"""

from chatbi.domain.chat.dtos import (
    AnalysisResult,
    CacheResponse,
    ChatDTO,
    CommonResponse,
    Conversation,
    ConversationResponse,
    GenerateSqlRequest,
    Message,
    RunSqlData,
    RunSqlRequest,
    RunSqlResponse,
    SqlResultResponse,
    ChatAnalysisResponse,
)
from chatbi.domain.chat.entities import (
    ChatHistory,
    ChatMessage,
    ChatMessageEntity,
    SavedQuery,
    Visualization,
)
from chatbi.domain.chat.entities import (
    ChatSession as ChatSessionEntity,
)
from chatbi.domain.chat.entities import (
    ChatSessionEntity as ChatSessionDomainEntity,
)
from chatbi.domain.chat.models import (
    ChatSession,
    ConversationContext,
    MessageRole,
)
from chatbi.domain.chat.models import (
    Message as DomainMessage,
)
from chatbi.domain.chat.repository import (
    ChatRepository,
)
from chatbi.domain.chat.router import router as ChatRouter
from chatbi.domain.chat.service import (
    ChatService,
)

__all__ = [
    # Domain router
    "ChatRouter",
    # Domain repository
    "ChatRepository",
    # Domain Service
    "ChatService",
    # ------------------------------------------------------------
    # Database entities
    "ChatSessionEntity",
    "ChatMessage",
    "Visualization",
    "SavedQuery",
    "ChatHistory",
    # Domain entities
    "ChatSessionDomainEntity",
    "ChatMessageEntity",
    # Domain models
    "ChatSession",
    "DomainMessage",
    "MessageRole",
    "ConversationContext",
    # DTOs
    "ChatDTO",
    "GenerateSqlRequest",
    "RunSqlRequest",
    "RunSqlResponse",
    "RunSqlData",
    "CommonResponse",
    # New response models
    "CacheResponse",
    "Message",
    "Conversation",
    "ConversationResponse",
    "AnalysisResult",
    "SqlResultResponse",
]
