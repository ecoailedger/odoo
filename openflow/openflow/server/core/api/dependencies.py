"""
FastAPI Dependencies for API Layer
"""

from typing import Optional, Dict, Any
from fastapi import Depends, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from openflow.server.core.orm.registry import get_env, Environment
from openflow.server.core.security.jwt_handler import decode_token
from openflow.server.core.database import get_db
from .exceptions import AuthenticationError, AccessDeniedError

# Security scheme for JWT Bearer tokens
security = HTTPBearer(auto_error=False)


async def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[Dict[str, Any]]:
    """
    Extract and validate JWT token from Authorization header
    Returns user payload if valid, None if no token provided
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = decode_token(token)
        return payload
    except Exception as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


async def get_current_user_from_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Optional[Dict[str, Any]]:
    """
    Extract user from session cookie
    Returns user info if valid session, None otherwise
    """
    session_id = request.cookies.get('session_id')
    if not session_id:
        return None

    try:
        # Get session from Redis or database
        from openflow.server.core.security.session import SessionManager
        session_manager = SessionManager()
        session_data = await session_manager.get_session(session_id)

        if not session_data:
            return None

        return {
            'user_id': session_data.get('user_id'),
            'login': session_data.get('login'),
            'session_id': session_id,
        }
    except Exception:
        return None


async def get_current_user_from_apikey(
    x_api_key: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> Optional[Dict[str, Any]]:
    """
    Extract and validate API key from X-API-Key header
    Returns user info if valid, None otherwise
    """
    if not x_api_key:
        return None

    try:
        env = get_env(session=db)
        api_key_model = env['auth.api.key']

        # Search for valid API key
        keys = await api_key_model.search([
            ('key', '=', x_api_key),
            ('active', '=', True),
        ])

        if not keys:
            return None

        key = keys[0]
        # Update last used timestamp
        await key.write({'last_used': 'now'})

        return {
            'user_id': key.user_id.id,
            'login': key.user_id.login,
            'api_key': x_api_key,
        }
    except Exception:
        return None


async def get_current_user(
    token_user: Optional[Dict[str, Any]] = Depends(get_current_user_from_token),
    session_user: Optional[Dict[str, Any]] = Depends(get_current_user_from_session),
    apikey_user: Optional[Dict[str, Any]] = Depends(get_current_user_from_apikey),
) -> Optional[Dict[str, Any]]:
    """
    Get current user from any available authentication method
    Priority: JWT Token > Session Cookie > API Key
    """
    return token_user or session_user or apikey_user


async def require_auth(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Dependency that requires authentication
    Raises 401 if no valid authentication is provided
    """
    if not current_user:
        raise AuthenticationError("Authentication required")
    return current_user


async def get_env_with_user(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_auth),
) -> Environment:
    """
    Create ORM environment with authenticated user context
    """
    # Load user record
    env_superuser = get_env(session=db)
    user_model = env_superuser['res.users']
    user = await user_model.browse(current_user['user_id'])

    # Create environment with user context
    env = get_env(session=db, user=user)
    return env


async def get_env_optional_auth(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
) -> Environment:
    """
    Create ORM environment with optional user context
    Uses superuser if no authentication provided
    """
    if current_user:
        env_superuser = get_env(session=db)
        user_model = env_superuser['res.users']
        user = await user_model.browse(current_user['user_id'])
        return get_env(session=db, user=user)
    else:
        return get_env(session=db)
