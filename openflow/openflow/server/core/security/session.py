"""Session management for tracking user sessions."""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class Session:
    """Represents a user session.

    Attributes:
        session_id: Unique session identifier
        user_id: ID of the authenticated user
        created_at: When the session was created
        last_activity: Last activity timestamp
        expires_at: When the session expires
        ip_address: Client IP address
        user_agent: Client user agent string
        data: Additional session data
    """
    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if the session has expired."""
        return datetime.utcnow() > self.expires_at

    def is_active(self, timeout_minutes: int = 30) -> bool:
        """Check if the session is still active.

        Args:
            timeout_minutes: Inactivity timeout in minutes

        Returns:
            True if session had activity within timeout period
        """
        if self.is_expired():
            return False

        timeout = timedelta(minutes=timeout_minutes)
        return datetime.utcnow() - self.last_activity < timeout

    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """Create session from dictionary."""
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_activity=datetime.fromisoformat(data["last_activity"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            data=data.get("data", {}),
        )


class SessionManager:
    """In-memory session manager.

    In production, this should be backed by Redis or a database.
    This is a simple implementation for demonstration.
    """

    def __init__(self):
        self._sessions: Dict[str, Session] = {}

    def create_session(
        self,
        user_id: str,
        expires_in_hours: int = 24,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        **extra_data
    ) -> Session:
        """Create a new session for a user.

        Args:
            user_id: The user ID
            expires_in_hours: Session lifetime in hours
            ip_address: Client IP address
            user_agent: Client user agent
            **extra_data: Additional session data

        Returns:
            The created session

        Example:
            >>> manager = SessionManager()
            >>> session = manager.create_session(
            ...     user_id="123",
            ...     ip_address="192.168.1.1"
            ... )
        """
        session_id = secrets.token_urlsafe(32)
        now = datetime.utcnow()

        session = Session(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            last_activity=now,
            expires_at=now + timedelta(hours=expires_in_hours),
            ip_address=ip_address,
            user_agent=user_agent,
            data=extra_data,
        )

        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID.

        Args:
            session_id: The session ID

        Returns:
            The session if found and valid, None otherwise
        """
        session = self._sessions.get(session_id)

        if session and not session.is_expired():
            session.update_activity()
            return session

        # Clean up expired session
        if session:
            self.delete_session(session_id)

        return None

    def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: The session ID to delete

        Returns:
            True if session was deleted, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user.

        Args:
            user_id: The user ID

        Returns:
            Number of sessions deleted
        """
        sessions_to_delete = [
            sid for sid, session in self._sessions.items()
            if session.user_id == user_id
        ]

        for sid in sessions_to_delete:
            del self._sessions[sid]

        return len(sessions_to_delete)

    def cleanup_expired(self) -> int:
        """Remove all expired sessions.

        Returns:
            Number of sessions removed
        """
        expired = [
            sid for sid, session in self._sessions.items()
            if session.is_expired()
        ]

        for sid in expired:
            del self._sessions[sid]

        return len(expired)

    def get_user_sessions(self, user_id: str) -> list[Session]:
        """Get all active sessions for a user.

        Args:
            user_id: The user ID

        Returns:
            List of active sessions
        """
        return [
            session for session in self._sessions.values()
            if session.user_id == user_id and not session.is_expired()
        ]


# Global session manager instance
session_manager = SessionManager()
