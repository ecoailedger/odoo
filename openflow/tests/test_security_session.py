"""
Tests for session management
"""
import pytest
from datetime import datetime, timedelta
from openflow.server.core.security import (
    Session,
    SessionManager,
    session_manager,
)


class TestSession:
    """Test Session class"""

    def test_session_creation(self):
        """Test creating a session"""
        now = datetime.utcnow()
        expires = now + timedelta(hours=24)

        session = Session(
            session_id="sess_123",
            user_id="user_456",
            created_at=now,
            last_activity=now,
            expires_at=expires,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )

        assert session.session_id == "sess_123"
        assert session.user_id == "user_456"
        assert session.ip_address == "192.168.1.1"

    def test_session_is_expired_false(self):
        """Test session not expired"""
        now = datetime.utcnow()
        expires = now + timedelta(hours=1)  # Expires in future

        session = Session(
            session_id="sess_123",
            user_id="user_456",
            created_at=now,
            last_activity=now,
            expires_at=expires
        )

        assert session.is_expired() is False

    def test_session_is_expired_true(self):
        """Test session is expired"""
        now = datetime.utcnow()
        expires = now - timedelta(hours=1)  # Expired 1 hour ago

        session = Session(
            session_id="sess_123",
            user_id="user_456",
            created_at=now - timedelta(hours=2),
            last_activity=now - timedelta(hours=1),
            expires_at=expires
        )

        assert session.is_expired() is True

    def test_session_is_active_true(self):
        """Test session is active"""
        now = datetime.utcnow()
        expires = now + timedelta(hours=1)

        session = Session(
            session_id="sess_123",
            user_id="user_456",
            created_at=now,
            last_activity=now,
            expires_at=expires
        )

        assert session.is_active() is True

    def test_session_is_active_expired(self):
        """Test session not active when expired"""
        now = datetime.utcnow()
        expires = now - timedelta(hours=1)

        session = Session(
            session_id="sess_123",
            user_id="user_456",
            created_at=now - timedelta(hours=2),
            last_activity=now - timedelta(hours=1),
            expires_at=expires
        )

        assert session.is_active() is False

    def test_session_is_active_timeout(self):
        """Test session not active due to inactivity timeout"""
        now = datetime.utcnow()
        expires = now + timedelta(hours=1)

        session = Session(
            session_id="sess_123",
            user_id="user_456",
            created_at=now - timedelta(hours=1),
            last_activity=now - timedelta(minutes=31),  # 31 mins ago
            expires_at=expires
        )

        # Should not be active with 30 minute timeout
        assert session.is_active(timeout_minutes=30) is False

    def test_session_update_activity(self):
        """Test updating session activity"""
        now = datetime.utcnow()
        old_time = now - timedelta(minutes=5)

        session = Session(
            session_id="sess_123",
            user_id="user_456",
            created_at=now,
            last_activity=old_time,
            expires_at=now + timedelta(hours=1)
        )

        session.update_activity()

        # Last activity should be updated to now (within 1 second tolerance)
        time_diff = (datetime.utcnow() - session.last_activity).total_seconds()
        assert time_diff < 1

    def test_session_to_dict(self):
        """Test converting session to dict"""
        now = datetime.utcnow()
        expires = now + timedelta(hours=1)

        session = Session(
            session_id="sess_123",
            user_id="user_456",
            created_at=now,
            last_activity=now,
            expires_at=expires,
            ip_address="10.0.0.1",
            data={"extra": "info"}
        )

        session_dict = session.to_dict()

        assert session_dict["session_id"] == "sess_123"
        assert session_dict["user_id"] == "user_456"
        assert session_dict["ip_address"] == "10.0.0.1"
        assert session_dict["data"]["extra"] == "info"

    def test_session_from_dict(self):
        """Test creating session from dict"""
        now = datetime.utcnow()
        session_dict = {
            "session_id": "sess_789",
            "user_id": "user_999",
            "created_at": now.isoformat(),
            "last_activity": now.isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
            "ip_address": "172.16.0.1",
            "user_agent": "Chrome",
            "data": {"key": "value"}
        }

        session = Session.from_dict(session_dict)

        assert session.session_id == "sess_789"
        assert session.user_id == "user_999"
        assert session.ip_address == "172.16.0.1"
        assert session.data["key"] == "value"


class TestSessionManager:
    """Test SessionManager class"""

    def test_create_session(self):
        """Test creating a session"""
        manager = SessionManager()

        session = manager.create_session(
            user_id="user_123",
            ip_address="192.168.1.1"
        )

        assert session is not None
        assert session.user_id == "user_123"
        assert session.ip_address == "192.168.1.1"
        assert len(session.session_id) > 0

    def test_create_session_unique_ids(self):
        """Test that session IDs are unique"""
        manager = SessionManager()

        session1 = manager.create_session(user_id="user_1")
        session2 = manager.create_session(user_id="user_1")

        assert session1.session_id != session2.session_id

    def test_get_session_valid(self):
        """Test getting a valid session"""
        manager = SessionManager()

        created = manager.create_session(user_id="user_456")
        retrieved = manager.get_session(created.session_id)

        assert retrieved is not None
        assert retrieved.session_id == created.session_id
        assert retrieved.user_id == "user_456"

    def test_get_session_not_found(self):
        """Test getting non-existent session"""
        manager = SessionManager()

        retrieved = manager.get_session("nonexistent_session_id")

        assert retrieved is None

    def test_get_session_expired(self):
        """Test getting expired session returns None"""
        manager = SessionManager()

        # Create expired session
        session = manager.create_session(
            user_id="user_789",
            expires_in_hours=-1  # Already expired
        )

        # Try to get it
        retrieved = manager.get_session(session.session_id)

        # Should return None and clean up
        assert retrieved is None

    def test_delete_session(self):
        """Test deleting a session"""
        manager = SessionManager()

        session = manager.create_session(user_id="user_delete")
        session_id = session.session_id

        # Delete session
        result = manager.delete_session(session_id)

        assert result is True

        # Should not be able to get it anymore
        retrieved = manager.get_session(session_id)
        assert retrieved is None

    def test_delete_session_not_found(self):
        """Test deleting non-existent session"""
        manager = SessionManager()

        result = manager.delete_session("nonexistent_id")

        assert result is False

    def test_delete_user_sessions(self):
        """Test deleting all sessions for a user"""
        manager = SessionManager()

        # Create multiple sessions for same user
        session1 = manager.create_session(user_id="user_multi")
        session2 = manager.create_session(user_id="user_multi")
        session3 = manager.create_session(user_id="user_other")

        # Delete sessions for user_multi
        count = manager.delete_user_sessions("user_multi")

        assert count == 2

        # user_multi sessions should be gone
        assert manager.get_session(session1.session_id) is None
        assert manager.get_session(session2.session_id) is None

        # user_other session should still exist
        assert manager.get_session(session3.session_id) is not None

    def test_cleanup_expired(self):
        """Test cleaning up expired sessions"""
        manager = SessionManager()

        # Create mix of valid and expired sessions
        valid1 = manager.create_session(user_id="user_1", expires_in_hours=1)
        expired1 = manager.create_session(user_id="user_2", expires_in_hours=-1)
        expired2 = manager.create_session(user_id="user_3", expires_in_hours=-2)

        # Clean up expired
        count = manager.cleanup_expired()

        assert count == 2

        # Valid session should still exist
        assert manager.get_session(valid1.session_id) is not None

        # Expired sessions should be gone
        assert manager.get_session(expired1.session_id) is None
        assert manager.get_session(expired2.session_id) is None

    def test_get_user_sessions(self):
        """Test getting all sessions for a user"""
        manager = SessionManager()

        # Create sessions for different users
        session1 = manager.create_session(user_id="user_target")
        session2 = manager.create_session(user_id="user_target")
        session3 = manager.create_session(user_id="user_other")

        # Get sessions for user_target
        sessions = manager.get_user_sessions("user_target")

        assert len(sessions) == 2
        session_ids = [s.session_id for s in sessions]
        assert session1.session_id in session_ids
        assert session2.session_id in session_ids
        assert session3.session_id not in session_ids

    def test_get_user_sessions_excludes_expired(self):
        """Test get_user_sessions excludes expired sessions"""
        manager = SessionManager()

        # Create valid and expired sessions for same user
        valid = manager.create_session(user_id="user_test", expires_in_hours=1)
        expired = manager.create_session(user_id="user_test", expires_in_hours=-1)

        # Get sessions
        sessions = manager.get_user_sessions("user_test")

        # Should only return valid session
        assert len(sessions) == 1
        assert sessions[0].session_id == valid.session_id

    def test_session_extra_data(self):
        """Test storing extra data in session"""
        manager = SessionManager()

        session = manager.create_session(
            user_id="user_data",
            custom_field="custom_value",
            another_field=123
        )

        assert session.data["custom_field"] == "custom_value"
        assert session.data["another_field"] == 123

    def test_global_session_manager(self):
        """Test global session_manager instance"""
        # Should be able to use global instance
        session = session_manager.create_session(user_id="global_user")

        assert session is not None
        assert session.user_id == "global_user"

        # Clean up
        session_manager.delete_session(session.session_id)
