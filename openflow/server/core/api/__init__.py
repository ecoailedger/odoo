"""
API Layer for OpenFlow
Provides JSON-RPC and REST endpoints for model access
"""

from .exceptions import APIException, ValidationError, AccessDeniedError, NotFoundError
from .dependencies import get_env, get_current_user, require_auth
from .serializers import serialize_record, serialize_recordset
from .router import create_model_router
from .jsonrpc import jsonrpc_router
from .rest import rest_router

__all__ = [
    'APIException',
    'ValidationError',
    'AccessDeniedError',
    'NotFoundError',
    'get_env',
    'get_current_user',
    'require_auth',
    'serialize_record',
    'serialize_recordset',
    'create_model_router',
    'jsonrpc_router',
    'rest_router',
]
