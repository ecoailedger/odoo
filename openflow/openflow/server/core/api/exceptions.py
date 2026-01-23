"""
API Exception Classes
"""

from typing import Any, Optional, Dict
from fastapi import HTTPException, status


class APIException(HTTPException):
    """Base exception for API errors"""

    def __init__(
        self,
        status_code: int,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}

        super().__init__(
            status_code=status_code,
            detail={
                'error': {
                    'code': self.code,
                    'message': self.message,
                    'details': self.details,
                }
            }
        )


class ValidationError(APIException):
    """Validation error (400)"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            code='ValidationError',
            details=details,
        )


class AuthenticationError(APIException):
    """Authentication error (401)"""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            code='AuthenticationError',
        )


class AccessDeniedError(APIException):
    """Access denied error (403)"""

    def __init__(self, message: str = "Access denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            code='AccessDenied',
        )


class NotFoundError(APIException):
    """Not found error (404)"""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            code='NotFound',
        )


class MethodNotAllowedError(APIException):
    """Method not allowed (405)"""

    def __init__(self, message: str = "Method not allowed"):
        super().__init__(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            message=message,
            code='MethodNotAllowed',
        )


class ConflictError(APIException):
    """Conflict error (409)"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            code='Conflict',
            details=details,
        )


class InternalServerError(APIException):
    """Internal server error (500)"""

    def __init__(self, message: str = "Internal server error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            code='InternalError',
            details=details,
        )
