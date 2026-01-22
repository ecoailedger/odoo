"""
OpenFlow Security Module

This module provides comprehensive security features including:
- Authentication (sessions, JWT tokens, API keys)
- Authorization (model access, record rules, field security)
- Multi-company security
- Password hashing and validation
"""

# Exceptions
from .exceptions import (
    SecurityError,
    AccessDenied,
    AuthenticationError,
    InvalidCredentials,
    InvalidToken,
    SessionExpired,
    InsufficientPermissions,
    FieldAccessDenied,
    RecordAccessDenied,
)

# Password hashing
from .password import (
    hash_password,
    verify_password,
    needs_update,
    verify_and_update,
)

# JWT tokens
from .jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
    extract_user_id,
    create_token_pair,
)

# Session management
from .session import (
    Session,
    SessionManager,
    session_manager,
)

# Access control
from .access_control import (
    AccessController,
    SUPERUSER_ID,
    OperationType,
)

# Decorators
from .decorators import (
    require_login,
    check_access,
    require_groups,
    api_key_required,
    superuser_only,
    with_company,
    rate_limit,
)


__all__ = [
    # Exceptions
    "SecurityError",
    "AccessDenied",
    "AuthenticationError",
    "InvalidCredentials",
    "InvalidToken",
    "SessionExpired",
    "InsufficientPermissions",
    "FieldAccessDenied",
    "RecordAccessDenied",

    # Password
    "hash_password",
    "verify_password",
    "needs_update",
    "verify_and_update",

    # JWT
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_token_type",
    "extract_user_id",
    "create_token_pair",

    # Session
    "Session",
    "SessionManager",
    "session_manager",

    # Access Control
    "AccessController",
    "SUPERUSER_ID",
    "OperationType",

    # Decorators
    "require_login",
    "check_access",
    "require_groups",
    "api_key_required",
    "superuser_only",
    "with_company",
    "rate_limit",
]
