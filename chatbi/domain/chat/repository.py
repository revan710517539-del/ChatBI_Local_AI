"""
Chat repository implementation.

This module provides the repository pattern implementation for accessing
and managing chat conversations in the database.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from sqlalchemy import desc, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from chatbi.domain.chat.entities import ChatHistory, ChatMessage, ChatSession
from chatbi.domain.common.repository import AsyncBaseRepository, BaseRepository
from chatbi.exceptions import BadRequestError, DatabaseError, NotFoundError


class ChatRepository(BaseRepository[ChatSession]):
    """
    Repository for chat operations using synchronous database access.

    Provides methods for managing chat sessions, messages, history and statistics
    with proper error handling.
    """

    model_class = ChatSession

    def get_chat_session_by_id(self, id: str) -> Optional[ChatSession]:
        """
        Get chat session by ID.

        Args:
            id: Chat session ID

        Returns:
            Chat session if found, None otherwise
        """
        try:
            return (
                self.db.query(self.model_class)
                .filter(self.model_class.id == id)
                .first()
            )
        except Exception as e:
            logger.error(f"Error retrieving chat session: {e!s}")
            raise DatabaseError(f"Failed to retrieve chat session: {e!s}")

    def get_chat_messages_by_session_id(self, session_id: str) -> list[ChatMessage]:
        """
        Get chat messages by session ID.

        Args:
            session_id: Chat session ID

        Returns:
            List of chat messages
        """
        try:
            return (
                self.db.query(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.timestamp.asc())
                .all()
            )
        except Exception as e:
            logger.error(f"Error retrieving chat messages: {e!s}")
            raise DatabaseError(f"Failed to retrieve chat messages: {e!s}")

    def create_chat_session(self, session_data: dict[str, Any]) -> ChatSession:
        """
        Create a new chat session.

        Args:
            session_data: Dictionary containing session attributes

        Returns:
            Created chat session
        """
        try:
            session = ChatSession(**session_data)
            self.db.add(session)
            self.db.flush()
            self.db.refresh(session)
            return session
        except Exception as e:
            logger.error(f"Error creating chat session: {e!s}")
            raise DatabaseError(f"Failed to create chat session: {e!s}")

    def add_chat_message(self, message_data: dict[str, Any]) -> ChatMessage:
        """
        Add a new chat message.

        Args:
            message_data: Dictionary containing message attributes

        Returns:
            Created chat message
        """
        try:
            message = ChatMessage(**message_data)
            self.db.add(message)
            self.db.flush()
            self.db.refresh(message)

            # Update session's last_active timestamp
            session = self.get_chat_session_by_id(message.session_id)
            if session:
                session.last_active = datetime.utcnow()
                self.db.flush()

            return message
        except Exception as e:
            logger.error(f"Error adding chat message: {e!s}")
            raise DatabaseError(f"Failed to add chat message: {e!s}")

    def update_chat_session(
        self, id: str, update_data: dict[str, Any]
    ) -> Optional[ChatSession]:
        """
        Update an existing chat session.

        Args:
            id: Session ID
            update_data: Dictionary containing fields to update

        Returns:
            Updated session if found and updated, None otherwise
        """
        try:
            session = self.get_chat_session_by_id(id)
            if not session:
                return None

            for key, value in update_data.items():
                if hasattr(session, key):
                    setattr(session, key, value)

            self.db.flush()
            self.db.refresh(session)
            return session
        except Exception as e:
            logger.error(f"Error updating chat session: {e!s}")
            raise DatabaseError(f"Failed to update chat session: {e!s}")

    async def save_chat_history(self, history_data: dict[str, Any]) -> Optional[ChatHistory]:
        """
        Save a chat history record.

        Args:
            history_data: Dictionary containing history record attributes

        Returns:
            Created history record
        """
        try:
            history = ChatHistory(**history_data)
            self.db.add(history)
            
            if self.is_async:
                await self.db.flush()
                await self.db.refresh(history)
            else:
                self.db.flush()
                self.db.refresh(history)
                
            return history
        except Exception as e:
            logger.error(f"Error saving chat history: {e!s}")
            # Don't raise - history recording should not interrupt the main flow
            return None

    def get_chat_sessions_by_user_id(
        self, user_id: str, limit: int = 50
    ) -> list[ChatSession]:
        """
        Get chat sessions for a specific user.

        Args:
            user_id: User identifier
            limit: Maximum number of sessions to return

        Returns:
            List of chat sessions for the user, ordered by last_active desc
        """
        try:
            return (
                self.db.query(ChatSession)
                .filter(ChatSession.user_id == user_id)
                .order_by(desc(ChatSession.last_active))
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"Error retrieving chat sessions by user: {e!s}")
            raise DatabaseError(f"Failed to retrieve chat sessions by user: {e!s}")

    def get_recent_chat_sessions(self, limit: int = 10) -> list[ChatSession]:
        """
        Get most recent chat sessions across all users.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of most recent chat sessions
        """
        try:
            return (
                self.db.query(ChatSession)
                .order_by(desc(ChatSession.last_active))
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"Error retrieving recent chat sessions: {e!s}")
            raise DatabaseError(f"Failed to retrieve recent chat sessions: {e!s}")

    def search_chat_messages(self, query: str, limit: int = 20) -> list[ChatMessage]:
        """
        Search chat messages by content.

        Args:
            query: Search text to look for in message content
            limit: Maximum number of messages to return

        Returns:
            List of matching messages
        """
        try:
            # This uses SQL LIKE for case-insensitive search
            search_term = f"%{query}%"

            return (
                self.db.query(ChatMessage)
                .filter(ChatMessage.content.ilike(search_term))
                .order_by(desc(ChatMessage.timestamp))
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"Error searching chat messages: {e!s}")
            raise DatabaseError(f"Failed to search chat messages: {e!s}")

    def get_chat_stats(self) -> dict[str, Any]:
        """
        Get chat statistics.

        Returns:
            Dictionary of statistics about chats
        """
        try:
            # Get total count of chat sessions
            session_count = self.db.query(func.count(ChatSession.id)).scalar() or 0

            # Get count of chat messages
            message_count = self.db.query(func.count(ChatMessage.id)).scalar() or 0

            # Get user count
            user_count = (
                self.db.query(func.count(func.distinct(ChatSession.user_id))).scalar()
                or 0
            )

            # Get success rate from chat history
            total_history = self.db.query(func.count(ChatHistory.id)).scalar() or 0
            success_history = (
                self.db.query(func.count(ChatHistory.id))
                .filter(ChatHistory.success == True)
                .scalar()
                or 0
            )
            success_rate = success_history / total_history if total_history > 0 else 0

            return {
                "total_sessions": session_count,
                "total_messages": message_count,
                "unique_users": user_count,
                "success_rate": success_rate,
                "total_history_records": total_history,
            }
        except Exception as e:
            logger.error(f"Error retrieving chat stats: {e!s}")
            raise DatabaseError(f"Failed to retrieve chat stats: {e!s}")


class AsyncChatRepository(AsyncBaseRepository[ChatSession]):
    """
    Repository for chat operations using asynchronous database access.

    Provides asynchronous methods for managing chat sessions, messages, history and statistics
    with proper error handling.
    """

    model_class = ChatSession

    async def get_chat_session_by_id(self, id: str) -> Optional[ChatSession]:
        """
        Get chat session by ID asynchronously.

        Args:
            id: Chat session ID

        Returns:
            Chat session if found, None otherwise
        """
        try:
            result = await self.db.execute(
                select(self.model_class).filter(self.model_class.id == id)
            )
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error retrieving chat session: {e!s}")
            raise DatabaseError(f"Failed to retrieve chat session: {e!s}")

    async def get_chat_messages_by_session_id(
        self, session_id: str
    ) -> list[ChatMessage]:
        """
        Get chat messages by session ID asynchronously.

        Args:
            session_id: Chat session ID

        Returns:
            List of chat messages
        """
        try:
            result = await self.db.execute(
                select(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.timestamp.asc())
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error retrieving chat messages: {e!s}")
            raise DatabaseError(f"Failed to retrieve chat messages: {e!s}")

    async def create_chat_session(self, session_data: dict[str, Any]) -> ChatSession:
        """
        Create a new chat session asynchronously.

        Args:
            session_data: Dictionary containing session attributes

        Returns:
            Created chat session
        """
        try:
            session = ChatSession(**session_data)
            self.db.add(session)
            await self.db.flush()
            await self.db.refresh(session)
            return session
        except Exception as e:
            logger.error(f"Error creating chat session: {e!s}")
            raise DatabaseError(f"Failed to create chat session: {e!s}")

    async def add_chat_message(self, message_data: dict[str, Any]) -> ChatMessage:
        """
        Add a new chat message asynchronously.

        Args:
            message_data: Dictionary containing message attributes

        Returns:
            Created chat message
        """
        try:
            message = ChatMessage(**message_data)
            self.db.add(message)
            await self.db.flush()
            await self.db.refresh(message)

            # Update session's last_active timestamp
            session = await self.get_chat_session_by_id(message.session_id)
            if session:
                session.last_active = datetime.utcnow()
                await self.db.flush()

            return message
        except Exception as e:
            logger.error(f"Error adding chat message: {e!s}")
            raise DatabaseError(f"Failed to add chat message: {e!s}")

    async def update_chat_session(
        self, id: str, update_data: dict[str, Any]
    ) -> Optional[ChatSession]:
        """
        Update an existing chat session asynchronously.

        Args:
            id: Session ID
            update_data: Dictionary containing fields to update

        Returns:
            Updated session if found and updated, None otherwise
        """
        try:
            session = await self.get_chat_session_by_id(id)
            if not session:
                return None

            for key, value in update_data.items():
                if hasattr(session, key):
                    setattr(session, key, value)

            await self.db.flush()
            await self.db.refresh(session)
            return session
        except Exception as e:
            logger.error(f"Error updating chat session: {e!s}")
            raise DatabaseError(f"Failed to update chat session: {e!s}")

    async def save_chat_history(
        self, history_data: dict[str, Any]
    ) -> Optional[ChatHistory]:
        """
        Save a chat history record asynchronously.

        Args:
            history_data: Dictionary containing history record attributes

        Returns:
            Created history record
        """
        try:
            history = ChatHistory(**history_data)
            self.db.add(history)
            await self.db.flush()
            await self.db.refresh(history)
            return history
        except Exception as e:
            logger.error(f"Error saving chat history: {e!s}")
            # Don't raise - history recording should not interrupt the main flow
            return None

    async def get_chat_sessions_by_user_id(
        self, user_id: str, limit: int = 50
    ) -> list[ChatSession]:
        """
        Get chat sessions for a specific user asynchronously.

        Args:
            user_id: User identifier
            limit: Maximum number of sessions to return

        Returns:
            List of chat sessions for the user, ordered by last_active desc
        """
        try:
            result = await self.db.execute(
                select(ChatSession)
                .filter(ChatSession.user_id == user_id)
                .order_by(desc(ChatSession.last_active))
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error retrieving chat sessions by user: {e!s}")
            raise DatabaseError(f"Failed to retrieve chat sessions by user: {e!s}")

    async def get_recent_chat_sessions(self, limit: int = 10) -> list[ChatSession]:
        """
        Get most recent chat sessions across all users asynchronously.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of most recent chat sessions
        """
        try:
            result = await self.db.execute(
                select(ChatSession).order_by(desc(ChatSession.last_active)).limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error retrieving recent chat sessions: {e!s}")
            raise DatabaseError(f"Failed to retrieve recent chat sessions: {e!s}")

    async def search_chat_messages(
        self, query: str, limit: int = 20
    ) -> list[ChatMessage]:
        """
        Search chat messages by content asynchronously.

        Args:
            query: Search text to look for in message content
            limit: Maximum number of messages to return

        Returns:
            List of matching messages
        """
        try:
            # This uses SQL LIKE for case-insensitive search
            search_term = f"%{query}%"

            result = await self.db.execute(
                select(ChatMessage)
                .filter(ChatMessage.content.ilike(search_term))
                .order_by(desc(ChatMessage.timestamp))
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error searching chat messages: {e!s}")
            raise DatabaseError(f"Failed to search chat messages: {e!s}")

    async def get_chat_stats(self) -> dict[str, Any]:
        """
        Get chat statistics asynchronously.

        Returns:
            Dictionary of statistics about chats
        """
        try:
            # Get total count of chat sessions
            session_count_result = await self.db.execute(
                select(func.count()).select_from(ChatSession)
            )
            session_count = session_count_result.scalar_one() or 0

            # Get count of chat messages
            message_count_result = await self.db.execute(
                select(func.count()).select_from(ChatMessage)
            )
            message_count = message_count_result.scalar_one() or 0

            # Get user count
            user_count_result = await self.db.execute(
                select(func.count(func.distinct(ChatSession.user_id))).select_from(
                    ChatSession
                )
            )
            user_count = user_count_result.scalar_one() or 0

            # Get success rate from chat history
            total_history_result = await self.db.execute(
                select(func.count()).select_from(ChatHistory)
            )
            total_history = total_history_result.scalar_one() or 0

            success_history_result = await self.db.execute(
                select(func.count())
                .select_from(ChatHistory)
                .filter(ChatHistory.success == True)
            )
            success_history = success_history_result.scalar_one() or 0

            success_rate = success_history / total_history if total_history > 0 else 0

            return {
                "total_sessions": session_count,
                "total_messages": message_count,
                "unique_users": user_count,
                "success_rate": success_rate,
                "total_history_records": total_history,
            }
        except Exception as e:
            logger.error(f"Error retrieving chat stats: {e!s}")
            raise DatabaseError(f"Failed to retrieve chat stats: {e!s}")
