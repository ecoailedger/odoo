"""Security-related exceptions."""


class SecurityError(Exception):
    """Base class for security-related errors."""
    pass


class AccessDenied(SecurityError):
    """Raised when access is denied to a resource."""
    pass


class AuthenticationError(SecurityError):
    """Raised when authentication fails."""
    pass


class InvalidCredentials(AuthenticationError):
    """Raised when credentials are invalid."""
    pass


class InvalidToken(AuthenticationError):
    """Raised when a token is invalid or expired."""
    pass


class SessionExpired(AuthenticationError):
    """Raised when a session has expired."""
    pass


class InsufficientPermissions(AccessDenied):
    """Raised when user lacks required permissions."""
    pass


class FieldAccessDenied(AccessDenied):
    """Raised when access to a field is denied."""
    pass


class RecordAccessDenied(AccessDenied):
    """Raised when access to a record is denied."""
    pass
