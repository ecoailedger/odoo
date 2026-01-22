"""
Tests for JWT token generation and validation
"""
import pytest
from datetime import datetime, timedelta
from openflow.server.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
    extract_user_id,
    create_token_pair,
    InvalidToken,
)


class TestJWTTokens:
    """Test JWT token functions"""

    def test_create_access_token(self):
        """Test access token creation"""
        data = {"sub": "user_123", "username": "john"}
        token = create_access_token(data)

        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0

        # Should be able to decode it
        payload = decode_token(token)
        assert payload["sub"] == "user_123"
        assert payload["username"] == "john"
        assert payload["type"] == "access"

    def test_create_refresh_token(self):
        """Test refresh token creation"""
        data = {"sub": "user_456"}
        token = create_refresh_token(data)

        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0

        # Should be able to decode it
        payload = decode_token(token)
        assert payload["sub"] == "user_456"
        assert payload["type"] == "refresh"

    def test_decode_token_valid(self):
        """Test decoding valid token"""
        data = {"sub": "user_789", "email": "user@example.com"}
        token = create_access_token(data)

        payload = decode_token(token)

        assert payload["sub"] == "user_789"
        assert payload["email"] == "user@example.com"
        assert "exp" in payload
        assert "iat" in payload
        assert "type" in payload

    def test_decode_token_invalid(self):
        """Test decoding invalid token"""
        invalid_token = "invalid.token.here"

        with pytest.raises(InvalidToken):
            decode_token(invalid_token)

    def test_decode_token_expired(self):
        """Test decoding expired token"""
        data = {"sub": "user_expired"}
        # Create token with -1 second expiration (already expired)
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))

        # Should raise InvalidToken for expired token
        with pytest.raises(InvalidToken):
            decode_token(token)

    def test_verify_token_type_access(self):
        """Test verifying access token type"""
        data = {"sub": "user_123"}
        token = create_access_token(data)
        payload = decode_token(token)

        # Should not raise for correct type
        verify_token_type(payload, "access")

    def test_verify_token_type_refresh(self):
        """Test verifying refresh token type"""
        data = {"sub": "user_456"}
        token = create_refresh_token(data)
        payload = decode_token(token)

        # Should not raise for correct type
        verify_token_type(payload, "refresh")

    def test_verify_token_type_mismatch(self):
        """Test verifying wrong token type"""
        data = {"sub": "user_789"}
        token = create_access_token(data)
        payload = decode_token(token)

        # Should raise for wrong type
        with pytest.raises(InvalidToken):
            verify_token_type(payload, "refresh")

    def test_extract_user_id_access(self):
        """Test extracting user ID from access token"""
        user_id = "user_abc_123"
        data = {"sub": user_id}
        token = create_access_token(data)

        extracted_id = extract_user_id(token)

        assert extracted_id == user_id

    def test_extract_user_id_refresh(self):
        """Test extracting user ID from refresh token"""
        user_id = "user_xyz_456"
        data = {"sub": user_id}
        token = create_refresh_token(data)

        extracted_id = extract_user_id(token, token_type="refresh")

        assert extracted_id == user_id

    def test_extract_user_id_wrong_type(self):
        """Test extracting user ID from wrong token type"""
        data = {"sub": "user_123"}
        token = create_access_token(data)

        # Should raise when expecting refresh token
        with pytest.raises(InvalidToken):
            extract_user_id(token, token_type="refresh")

    def test_extract_user_id_no_sub(self):
        """Test extracting user ID when 'sub' is missing"""
        # This is a bit contrived since create_access_token
        # requires data, but we can test the function directly
        from openflow.server.core.security.jwt_handler import create_access_token as cat
        from openflow.server.config.settings import settings
        from jose import jwt
        from datetime import datetime, timedelta

        # Create token without 'sub'
        to_encode = {
            "exp": datetime.utcnow() + timedelta(minutes=30),
            "type": "access"
        }
        token = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

        # Should raise InvalidToken when 'sub' is missing
        with pytest.raises(InvalidToken):
            extract_user_id(token)

    def test_create_token_pair(self):
        """Test creating token pair"""
        user_id = "user_pair_123"
        tokens = create_token_pair(
            user_id=user_id,
            username="john",
            email="john@example.com"
        )

        # Should return dict with access_token, refresh_token, token_type
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "token_type" in tokens
        assert tokens["token_type"] == "bearer"

        # Both tokens should be valid
        access_payload = decode_token(tokens["access_token"])
        refresh_payload = decode_token(tokens["refresh_token"])

        assert access_payload["sub"] == user_id
        assert refresh_payload["sub"] == user_id
        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"

    def test_token_expiration_times(self):
        """Test token expiration times are different"""
        user_id = "user_exp_test"
        tokens = create_token_pair(user_id=user_id)

        access_payload = decode_token(tokens["access_token"])
        refresh_payload = decode_token(tokens["refresh_token"])

        access_exp = access_payload["exp"]
        refresh_exp = refresh_payload["exp"]

        # Refresh token should expire later than access token
        assert refresh_exp > access_exp

    def test_custom_expiration(self):
        """Test custom token expiration"""
        data = {"sub": "user_custom"}
        custom_delta = timedelta(minutes=5)
        token = create_access_token(data, expires_delta=custom_delta)

        payload = decode_token(token)
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()

        # Expiration should be approximately 5 minutes from now
        # (allowing 10 second tolerance for test execution time)
        time_diff = (exp_time - now).total_seconds()
        assert 290 <= time_diff <= 310  # 5 minutes ± 10 seconds

    def test_token_includes_issued_at(self):
        """Test token includes 'iat' (issued at) claim"""
        data = {"sub": "user_iat"}
        token = create_access_token(data)

        payload = decode_token(token)

        assert "iat" in payload
        iat_time = datetime.fromtimestamp(payload["iat"])
        now = datetime.utcnow()

        # Should be issued within last 5 seconds
        time_diff = (now - iat_time).total_seconds()
        assert 0 <= time_diff <= 5
