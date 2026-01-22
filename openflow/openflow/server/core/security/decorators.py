"""Security decorators for model methods and API controllers.

This module provides decorators to protect methods and controllers
with authentication and authorization checks.
"""

from functools import wraps
from typing import Callable, Optional, List, Literal, Union
from .access_control import AccessController, OperationType
from .exceptions import (
    AccessDenied,
    AuthenticationError,
    InsufficientPermissions
)


def require_login(func: Callable) -> Callable:
    """Decorator to require user authentication.

    Use this on model methods or controller endpoints that require
    an authenticated user.

    Args:
        func: The function to decorate

    Returns:
        Wrapped function that checks authentication

    Raises:
        AuthenticationError: If no user is authenticated

    Example:
        >>> class MyModel(Model):
        ...     @require_login
        ...     def my_method(self):
        ...         # User is guaranteed to be authenticated here
        ...         return self.env.user.name
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Check if environment has a user
        if not hasattr(self, 'env'):
            raise AuthenticationError("No environment context available")

        if not self.env.user:
            raise AuthenticationError("Authentication required")

        return func(self, *args, **kwargs)

    return wrapper


def check_access(
    operation: OperationType,
    model: Optional[str] = None,
    raise_exception: bool = True
) -> Callable:
    """Decorator to check model access permissions.

    Use this on model methods to verify the user has permission
    to perform the specified operation.

    Args:
        operation: The operation to check ('read', 'write', 'create', 'unlink')
        model: Optional model name (if None, uses the model of the method)
        raise_exception: Whether to raise exception on denied access

    Returns:
        Decorator function

    Raises:
        AccessDenied: If user lacks permission

    Example:
        >>> class ResPartner(Model):
        ...     _name = 'res.partner'
        ...
        ...     @check_access('write')
        ...     def update_credit_limit(self, new_limit):
        ...         # User must have write permission on res.partner
        ...         self.credit_limit = new_limit
        ...
        ...     @check_access('unlink', model='account.move')
        ...     def delete_invoices(self):
        ...         # User must have unlink permission on account.move
        ...         invoices = self.env['account.move'].search([...])
        ...         invoices.unlink()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Determine model name
            model_name = model
            if not model_name and hasattr(self, '_name'):
                model_name = self._name
            if not model_name:
                raise ValueError("Cannot determine model name for access check")

            # Check access
            if hasattr(self, 'env'):
                controller = AccessController(self.env)
                controller.check_model_access(
                    model_name,
                    operation,
                    raise_exception=raise_exception
                )

            return func(self, *args, **kwargs)

        return wrapper
    return decorator


def require_groups(groups: Union[str, List[str]]) -> Callable:
    """Decorator to require user membership in specific groups.

    Args:
        groups: Group external ID(s) required (e.g., 'base.group_user')

    Returns:
        Decorator function

    Raises:
        InsufficientPermissions: If user is not in required groups

    Example:
        >>> class ResUsers(Model):
        ...     @require_groups('base.group_system')
        ...     def reset_all_passwords(self):
        ...         # Only system admins can call this
        ...         pass
        ...
        ...     @require_groups(['base.group_user', 'sales.group_manager'])
        ...     def approve_sale(self):
        ...         # User must be in both groups
        ...         pass
    """
    group_list = [groups] if isinstance(groups, str) else groups

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, 'env') or not self.env.user:
                raise AuthenticationError("Authentication required")

            user = self.env.user

            # Check if user is in all required groups
            for group_ext_id in group_list:
                if not user.has_group(group_ext_id):
                    raise InsufficientPermissions(
                        f"User must be in group: {group_ext_id}"
                    )

            return func(self, *args, **kwargs)

        return wrapper
    return decorator


def api_key_required(func: Callable) -> Callable:
    """Decorator to require API key authentication.

    Use this on controller endpoints that should be accessed
    with an API key instead of session authentication.

    Args:
        func: The function to decorate

    Returns:
        Wrapped function that checks API key

    Raises:
        AuthenticationError: If API key is invalid or missing

    Example:
        >>> from fastapi import APIRouter, Header
        >>> router = APIRouter()
        ...
        >>> @router.get("/api/data")
        >>> @api_key_required
        >>> async def get_data(api_key: str = Header(...)):
        ...     return {"data": "sensitive information"}
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract API key from request
        # This is a placeholder - actual implementation depends on framework

        # Check if API key is in kwargs
        api_key = kwargs.get('api_key') or kwargs.get('x_api_key')

        if not api_key:
            raise AuthenticationError("API key required")

        # TODO: Validate API key against database
        # This would query the auth.api.key model

        # For now, just check if key is not empty
        if not api_key.strip():
            raise AuthenticationError("Invalid API key")

        return await func(*args, **kwargs)

    return wrapper


def superuser_only(func: Callable) -> Callable:
    """Decorator to restrict method to superuser only.

    Args:
        func: The function to decorate

    Returns:
        Wrapped function that checks for superuser

    Raises:
        AccessDenied: If user is not superuser

    Example:
        >>> class IrModel(Model):
        ...     @superuser_only
        ...     def drop_table(self):
        ...         # Only superuser can drop tables
        ...         pass
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, 'env'):
            raise AuthenticationError("No environment context")

        controller = AccessController(self.env)
        if not controller.is_superuser():
            raise AccessDenied("This operation requires superuser privileges")

        return func(self, *args, **kwargs)

    return wrapper


def with_company(company_id: Optional[int] = None) -> Callable:
    """Decorator to execute method in a specific company context.

    Args:
        company_id: Company ID to use (if None, uses user's current company)

    Returns:
        Decorator function

    Example:
        >>> class SaleOrder(Model):
        ...     @with_company(company_id=2)
        ...     def create_invoice(self):
        ...         # This will be created in company 2's context
        ...         invoice = self.env['account.move'].create({...})
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, 'env'):
                return func(self, *args, **kwargs)

            # Get company ID
            cid = company_id
            if cid is None and self.env.user:
                cid = getattr(self.env.user.company_id, 'id', None)

            if cid is None:
                return func(self, *args, **kwargs)

            # Create new environment with company in context
            # TODO: Implement environment.with_context()
            # new_env = self.env.with_context(company_id=cid)

            # For now, just call the function
            return func(self, *args, **kwargs)

        return wrapper
    return decorator


def rate_limit(max_calls: int, period_seconds: int) -> Callable:
    """Decorator to rate limit method calls.

    Args:
        max_calls: Maximum number of calls allowed
        period_seconds: Time period in seconds

    Returns:
        Decorator function

    Example:
        >>> class ResUsers(Model):
        ...     @rate_limit(max_calls=5, period_seconds=60)
        ...     def send_password_reset(self):
        ...         # Limited to 5 calls per minute
        ...         pass
    """
    # Simple in-memory rate limiting
    call_times = {}

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            from datetime import datetime, timedelta

            # Get user ID for rate limiting
            user_id = None
            if hasattr(self, 'env') and self.env.user:
                user_id = getattr(self.env.user, 'id', None)

            if user_id:
                key = f"{func.__name__}:{user_id}"
                now = datetime.utcnow()

                # Clean old entries
                if key in call_times:
                    call_times[key] = [
                        t for t in call_times[key]
                        if now - t < timedelta(seconds=period_seconds)
                    ]

                # Check rate limit
                if key not in call_times:
                    call_times[key] = []

                if len(call_times[key]) >= max_calls:
                    raise AccessDenied(
                        f"Rate limit exceeded: {max_calls} calls per "
                        f"{period_seconds} seconds"
                    )

                call_times[key].append(now)

            return func(self, *args, **kwargs)

        return wrapper
    return decorator
