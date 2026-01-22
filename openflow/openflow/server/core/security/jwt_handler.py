"""JWT token generation and validation for authentication."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt

from openflow.server.config.settings import settings
from .exceptions import InvalidToken


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token.

    Args:
        data: The data to encode in the token (usually user_id, etc.)
        expires_delta: Optional custom expiration time

    Returns:
        The encoded JWT token string

    Example:
        >>> token = create_access_token({"sub": "user_id_123"})
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT refresh token.

    Refresh tokens have a longer lifetime than access tokens
    and are used to obtain new access tokens.

    Args:
        data: The data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        The encoded JWT refresh token string

    Example:
        >>> token = create_refresh_token({"sub": "user_id_123"})
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.refresh_token_expire_days
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token.

    Args:
        token: The JWT token to decode

    Returns:
        The decoded token payload

    Raises:
        InvalidToken: If the token is invalid or expired

    Example:
        >>> token = create_access_token({"sub": "user_123"})
        >>> payload = decode_token(token)
        >>> print(payload["sub"])
        user_123
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError as e:
        raise InvalidToken(f"Invalid or expired token: {str(e)}")


def verify_token_type(payload: Dict[str, Any], expected_type: str) -> None:
    """Verify that a token payload has the expected type.

    Args:
        payload: The decoded token payload
        expected_type: The expected token type ("access" or "refresh")

    Raises:
        InvalidToken: If the token type doesn't match

    Example:
        >>> payload = decode_token(some_token)
        >>> verify_token_type(payload, "access")
    """
    token_type = payload.get("type")
    if token_type != expected_type:
        raise InvalidToken(
            f"Invalid token type. Expected {expected_type}, got {token_type}"
        )


def extract_user_id(token: str, token_type: str = "access") -> str:
    """Extract user ID from a JWT token.

    Args:
        token: The JWT token
        token_type: Expected token type ("access" or "refresh")

    Returns:
        The user ID from the token

    Raises:
        InvalidToken: If token is invalid or doesn't contain user ID

    Example:
        >>> token = create_access_token({"sub": "user_123"})
        >>> user_id = extract_user_id(token)
        >>> print(user_id)
        user_123
    """
    payload = decode_token(token)
    verify_token_type(payload, token_type)

    user_id = payload.get("sub")
    if not user_id:
        raise InvalidToken("Token does not contain user ID")

    return user_id


def create_token_pair(user_id: str, **extra_data) -> Dict[str, str]:
    """Create both access and refresh tokens for a user.

    Args:
        user_id: The user ID to encode in the tokens
        **extra_data: Additional data to include in the tokens

    Returns:
        Dictionary with "access_token" and "refresh_token"

    Example:
        >>> tokens = create_token_pair(
        ...     user_id="123",
        ...     username="john",
        ...     email="john@example.com"
        ... )
        >>> print(tokens["access_token"])
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    data = {"sub": user_id, **extra_data}

    return {
        "access_token": create_access_token(data),
        "refresh_token": create_refresh_token(data),
        "token_type": "bearer"
    }
