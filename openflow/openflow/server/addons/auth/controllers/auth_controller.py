"""
Authentication Controllers

FastAPI endpoints for authentication operations including login, logout,
token refresh, and API key authentication.
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr

from openflow.server.core.security import (
    create_token_pair,
    decode_token,
    extract_user_id,
    session_manager,
    InvalidToken,
    InvalidCredentials,
    AuthenticationError,
)


router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()


# Request/Response Models
class LoginRequest(BaseModel):
    """Login request body"""
    login: str
    password: str


class LoginResponse(BaseModel):
    """Login response body"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict
    session_id: str


class RefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ApiKeyRequest(BaseModel):
    """API key creation request"""
    name: str
    expires_in_days: Optional[int] = None
    scopes: Optional[str] = None
    description: Optional[str] = None


class ApiKeyResponse(BaseModel):
    """API key creation response"""
    api_key: str
    key_id: int
    name: str
    expires_at: Optional[datetime] = None


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str


# Helper functions
async def get_user_by_login(login: str):
    """
    Get user by login

    In a real implementation, this would query the database.
    For now, it's a placeholder.
    """
    # TODO: Implement actual database query
    # from openflow.server.core.orm.registry import get_env
    # env = get_env()
    # users = await env['res.users'].search([('login', '=', login)])
    # if users:
    #     return users[0]
    return None


async def get_user_by_id(user_id: str):
    """
    Get user by ID

    In a real implementation, this would query the database.
    """
    # TODO: Implement actual database query
    return None


async def log_auth_event(event_type: str, **kwargs):
    """
    Log authentication event

    In a real implementation, this would create an auth.log record.
    """
    # TODO: Implement actual logging
    print(f"[AUTH EVENT] {event_type}: {kwargs}")


# Authentication endpoints
@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, req: Request):
    """
    Authenticate user and create session

    Args:
        request: Login credentials
        req: FastAPI request for IP/user agent

    Returns:
        JWT tokens and session information

    Raises:
        HTTPException: If credentials are invalid
    """
    try:
        # Get user
        user = await get_user_by_login(request.login)

        if not user:
            await log_auth_event(
                'login_fail',
                login=request.login,
                ip_address=req.client.host,
                failure_reason='User not found'
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Verify password
        if not user.authenticate(request.password):
            await log_auth_event(
                'login_fail',
                login=request.login,
                user_id=user.id,
                ip_address=req.client.host,
                failure_reason='Invalid password'
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Check if user is active
        if not user.active:
            await log_auth_event(
                'login_fail',
                login=request.login,
                user_id=user.id,
                ip_address=req.client.host,
                failure_reason='User inactive'
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        # Create JWT tokens
        tokens = create_token_pair(
            user_id=str(user.id),
            login=user.login,
            email=user.email
        )

        # Create session
        session = session_manager.create_session(
            user_id=str(user.id),
            ip_address=req.client.host,
            user_agent=req.headers.get('user-agent'),
            expires_in_hours=24
        )

        # Update last login date
        user.update_login_date()

        # Log successful login
        await log_auth_event(
            'login_success',
            login=user.login,
            user_id=user.id,
            ip_address=req.client.host,
            session_id=session.session_id
        )

        return LoginResponse(
            access_token=tokens['access_token'],
            refresh_token=tokens['refresh_token'],
            token_type=tokens['token_type'],
            user={
                'id': user.id,
                'login': user.login,
                'name': user.name,
                'email': user.email,
            },
            session_id=session.session_id
        )

    except HTTPException:
        raise
    except Exception as e:
        await log_auth_event(
            'login_fail',
            login=request.login,
            ip_address=req.client.host,
            failure_reason=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    req: Request = None
):
    """
    Logout user and invalidate session

    Args:
        credentials: Bearer token
        req: FastAPI request

    Returns:
        Success message
    """
    try:
        # Extract user ID from token
        token = credentials.credentials
        user_id = extract_user_id(token)

        # Get session ID from token payload
        payload = decode_token(token)
        session_id = payload.get('session_id')

        # Invalidate session
        if session_id:
            session = session_manager.get_session(session_id)
            if session:
                session_manager.delete_session(session_id)

        # Log logout
        await log_auth_event(
            'logout',
            user_id=user_id,
            ip_address=req.client.host if req else None,
            session_id=session_id
        )

        return MessageResponse(message="Logged out successfully")

    except InvalidToken:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest):
    """
    Refresh access token using refresh token

    Args:
        request: Refresh token

    Returns:
        New access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        # Decode and verify refresh token
        payload = decode_token(request.refresh_token)

        # Verify it's a refresh token
        if payload.get('type') != 'refresh':
            raise InvalidToken("Not a refresh token")

        # Extract user ID
        user_id = payload.get('sub')
        if not user_id:
            raise InvalidToken("Invalid token payload")

        # Create new token pair
        tokens = create_token_pair(
            user_id=user_id,
            login=payload.get('login'),
            email=payload.get('email')
        )

        # Log token refresh
        await log_auth_event(
            'token_refresh',
            user_id=user_id
        )

        return TokenResponse(
            access_token=tokens['access_token'],
            refresh_token=tokens['refresh_token'],
            token_type=tokens['token_type']
        )

    except InvalidToken as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.get("/me")
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get current authenticated user information

    Args:
        credentials: Bearer token

    Returns:
        User information

    Raises:
        HTTPException: If token is invalid
    """
    try:
        # Extract user ID from token
        token = credentials.credentials
        user_id = extract_user_id(token)

        # Get user
        user = await get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {
            'id': user.id,
            'login': user.login,
            'name': user.name,
            'email': user.email,
            'active': user.active,
            'company_id': user.company_id.id if user.company_id else None,
        }

    except InvalidToken:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )


@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(
    request: ApiKeyRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new API key for the authenticated user

    Args:
        request: API key parameters
        credentials: Bearer token

    Returns:
        Created API key (plain text, shown only once)

    Raises:
        HTTPException: If creation fails
    """
    try:
        # Extract user ID from token
        token = credentials.credentials
        user_id = extract_user_id(token)

        # Calculate expiration
        expires_at = None
        if request.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)

        # Create API key (this would use the auth.api.key model)
        # For now, return a placeholder
        # TODO: Implement actual API key creation

        return ApiKeyResponse(
            api_key="ak_" + "placeholder_key_here",
            key_id=1,
            name=request.name,
            expires_at=expires_at
        )

    except InvalidToken:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )


@router.post("/validate")
async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Validate a JWT token

    Args:
        credentials: Bearer token

    Returns:
        Token validation result

    Raises:
        HTTPException: If token is invalid
    """
    try:
        token = credentials.credentials
        payload = decode_token(token)

        return {
            'valid': True,
            'user_id': payload.get('sub'),
            'token_type': payload.get('type'),
            'expires_at': payload.get('exp')
        }

    except InvalidToken as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
