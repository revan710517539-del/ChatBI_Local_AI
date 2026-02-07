"""
Session Context Management

Manages conversation sessions and context for multi-turn dialogues.

Features:
- Store conversation history
- Track session state
- Provide context for follow-up questions
- Session timeout management
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID

from loguru import logger


class SessionContext:
    """Session context data"""

    def __init__(
        self,
        session_id: str,
        user_id: str,
        project_id: str,
        messages: List[Dict[str, Any]] = None,
        created_at: datetime = None,
        last_active_at: datetime = None,
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.project_id = project_id
        self.messages = messages or []
        self.created_at = created_at or datetime.now()
        self.last_active_at = last_active_at or datetime.now()

    def add_message(
        self,
        question: str,
        query_data: Dict[str, Any],
        result: Dict[str, Any],
        chart_config: Dict[str, Any],
    ):
        """Add a message to session"""
        self.messages.append(
            {
                "timestamp": datetime.now().isoformat(),
                "question": question,
                "query_data": query_data,
                "result_summary": f"Found {result.get('row_count', 0)} rows",
                "chart_type": chart_config.get("chartType", "table"),
            }
        )
        self.last_active_at = datetime.now()

    def get_context_summary(self, max_messages: int = 5) -> str:
        """Get context summary for LLM"""
        if not self.messages:
            return ""

        recent_messages = self.messages[-max_messages:]

        lines = ["### Conversation History ###\n"]

        for idx, msg in enumerate(recent_messages, 1):
            lines.append(f"\n**Message {idx}**:")
            lines.append(f"- Question: {msg['question']}")
            lines.append(f"- Result: {msg['result_summary']}")
            lines.append(f"- Chart: {msg['chart_type']}")

        return "\n".join(lines)

    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if session has expired"""
        return (
            datetime.now() - self.last_active_at
        ).total_seconds() > timeout_minutes * 60


class SessionContextManager:
    """Manages session contexts"""

    def __init__(self, timeout_minutes: int = 30):
        """
        Initialize Session Context Manager

        Args:
            timeout_minutes: Session timeout in minutes
        """
        self.sessions: Dict[str, SessionContext] = {}
        self.timeout_minutes = timeout_minutes
        logger.info(
            f"SessionContextManager initialized (timeout: {timeout_minutes}min)"
        )

    def get_or_create_session(
        self, session_id: str, user_id: str, project_id: str
    ) -> SessionContext:
        """
        Get existing session or create new one

        Args:
            session_id: Session ID
            user_id: User ID
            project_id: Project ID

        Returns:
            SessionContext
        """
        # Check if session exists and is not expired
        if session_id in self.sessions:
            session = self.sessions[session_id]
            if not session.is_expired(self.timeout_minutes):
                logger.info(f"Retrieved existing session: {session_id}")
                return session
            else:
                logger.info(f"Session expired, creating new: {session_id}")
                del self.sessions[session_id]

        # Create new session
        session = SessionContext(
            session_id=session_id,
            user_id=user_id,
            project_id=project_id,
        )
        self.sessions[session_id] = session
        logger.info(f"Created new session: {session_id}")

        return session

    def add_message_to_session(
        self,
        session_id: str,
        question: str,
        query_data: Dict[str, Any],
        result: Dict[str, Any],
        chart_config: Dict[str, Any],
    ):
        """Add message to session"""
        if session_id in self.sessions:
            self.sessions[session_id].add_message(
                question=question,
                query_data=query_data,
                result=result,
                chart_config=chart_config,
            )
            logger.info(f"Added message to session: {session_id}")

    def get_context(
        self, session_id: str, max_messages: int = 5
    ) -> Optional[str]:
        """
        Get context summary for session

        Args:
            session_id: Session ID
            max_messages: Max messages to include

        Returns:
            Context string or None
        """
        if session_id in self.sessions:
            return self.sessions[session_id].get_context_summary(max_messages)
        return None

    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        expired = [
            sid
            for sid, session in self.sessions.items()
            if session.is_expired(self.timeout_minutes)
        ]

        for sid in expired:
            del self.sessions[sid]
            logger.info(f"Cleaned up expired session: {sid}")

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")

    def get_session_count(self) -> int:
        """Get active session count"""
        return len(self.sessions)


# Global session manager instance
_session_manager: Optional[SessionContextManager] = None


def get_session_manager(timeout_minutes: int = 30) -> SessionContextManager:
    """Get or create global session manager"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionContextManager(timeout_minutes=timeout_minutes)
    return _session_manager
