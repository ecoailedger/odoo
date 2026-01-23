"""
JSON-RPC 2.0 Endpoint
Provides standard JSON-RPC interface for model operations
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field

from openflow.server.core.orm.registry import Environment
from .dependencies import get_env_with_user, get_env_optional_auth
from .exceptions import ValidationError, NotFoundError, InternalServerError
from .serializers import serialize_recordset, serialize_record

router = APIRouter(prefix="/jsonrpc", tags=["JSON-RPC"])


class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 Request"""
    jsonrpc: str = Field(default="2.0", pattern="^2\\.0$")
    method: str
    params: Dict[str, Any] = Field(default_factory=dict)
    id: Optional[int | str] = None


class JSONRPCError(BaseModel):
    """JSON-RPC 2.0 Error"""
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None


class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 Response"""
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None
    id: Optional[int | str] = None


def create_error_response(
    request_id: Optional[int | str],
    code: int,
    message: str,
    data: Optional[Dict[str, Any]] = None,
) -> JSONRPCResponse:
    """Create JSON-RPC error response"""
    return JSONRPCResponse(
        id=request_id,
        error=JSONRPCError(code=code, message=message, data=data)
    )


def create_success_response(
    request_id: Optional[int | str],
    result: Any,
) -> JSONRPCResponse:
    """Create JSON-RPC success response"""
    return JSONRPCResponse(
        id=request_id,
        result=result,
    )


async def execute_call_kw(
    env: Environment,
    model: str,
    method: str,
    args: List[Any],
    kwargs: Dict[str, Any],
) -> Any:
    """
    Execute a model method (call_kw)

    Args:
        env: ORM environment
        model: Model name (e.g., 'res.partner')
        method: Method name (e.g., 'search_read')
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Method result
    """
    if model not in env.registry.models:
        raise NotFoundError(f"Model '{model}' not found")

    model_class = env[model]

    # Check if method exists
    if not hasattr(model_class, method):
        raise ValidationError(f"Method '{method}' not found on model '{model}'")

    # Get the method
    method_func = getattr(model_class, method)

    # Call the method
    try:
        result = await method_func(*args, **kwargs)

        # Serialize RecordSets
        if hasattr(result, '__class__') and hasattr(result.__class__, '_name'):
            # It's a RecordSet
            if method in ['search', 'browse', 'create']:
                fields = kwargs.get('fields')
                return serialize_recordset(result, fields=fields)
            else:
                return serialize_value(result)

        return result

    except Exception as e:
        raise InternalServerError(
            f"Error executing {model}.{method}: {str(e)}",
            details={'model': model, 'method': method}
        )


async def execute_crud_operation(
    env: Environment,
    model: str,
    operation: str,
    args: List[Any],
    kwargs: Dict[str, Any],
) -> Any:
    """
    Execute CRUD operations

    Supported operations:
        - search: Search records
        - search_read: Search and read records
        - read: Read records by IDs
        - create: Create new record
        - write: Update records
        - unlink: Delete records
        - search_count: Count matching records

    Args:
        env: ORM environment
        model: Model name
        operation: Operation name
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Operation result
    """
    if model not in env.registry.models:
        raise NotFoundError(f"Model '{model}' not found")

    model_class = env[model]

    try:
        if operation == 'search':
            domain = args[0] if args else []
            limit = kwargs.get('limit')
            offset = kwargs.get('offset', 0)
            order = kwargs.get('order')

            result = await model_class.search(domain, limit=limit, offset=offset, order=order)
            return [rec.id for rec in result]

        elif operation == 'search_read':
            domain = args[0] if args else []
            fields = kwargs.get('fields')
            limit = kwargs.get('limit')
            offset = kwargs.get('offset', 0)
            order = kwargs.get('order')

            records = await model_class.search(domain, limit=limit, offset=offset, order=order)
            return serialize_recordset(records, fields=fields)

        elif operation == 'read':
            ids = args[0] if args else []
            fields = kwargs.get('fields')

            if not ids:
                return []

            records = await model_class.browse(ids)
            return serialize_recordset(records, fields=fields)

        elif operation == 'create':
            values = args[0] if args else kwargs.get('values', {})

            if isinstance(values, list):
                # Batch create
                records = await model_class.create(values)
                return serialize_recordset(records)
            else:
                # Single create
                record = await model_class.create(values)
                return serialize_record(record)

        elif operation == 'write':
            ids = args[0] if args else []
            values = args[1] if len(args) > 1 else kwargs.get('values', {})

            if not ids:
                raise ValidationError("No IDs provided for write operation")

            records = await model_class.browse(ids)
            await records.write(values)
            return True

        elif operation == 'unlink':
            ids = args[0] if args else []

            if not ids:
                raise ValidationError("No IDs provided for unlink operation")

            records = await model_class.browse(ids)
            await records.unlink()
            return True

        elif operation == 'search_count':
            domain = args[0] if args else []
            result = await model_class.search(domain)
            return len(result)

        else:
            raise ValidationError(f"Unknown operation: {operation}")

    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise InternalServerError(
            f"Error executing {operation} on {model}: {str(e)}",
            details={'model': model, 'operation': operation}
        )


def serialize_value(value: Any) -> Any:
    """Serialize complex values for JSON-RPC response"""
    from .serializers import serialize_value as _serialize_value
    return _serialize_value(value)


@router.post("", response_model=JSONRPCResponse)
async def jsonrpc_endpoint(
    request: JSONRPCRequest,
    env: Environment = Depends(get_env_with_user),
) -> JSONRPCResponse:
    """
    JSON-RPC 2.0 Endpoint

    Supported methods:
        - call: Call any model method
        - execute: Execute CRUD operations

    Example request:
        {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": "res.partner",
                "method": "search_read",
                "args": [[["is_company", "=", true]]],
                "kwargs": {"fields": ["name", "email"], "limit": 10}
            },
            "id": 1
        }
    """
    try:
        method = request.method
        params = request.params

        if method == "call":
            # Call any model method
            model = params.get('model')
            method_name = params.get('method')
            args = params.get('args', [])
            kwargs = params.get('kwargs', {})

            if not model or not method_name:
                return create_error_response(
                    request.id,
                    -32602,
                    "Invalid params: 'model' and 'method' are required"
                )

            result = await execute_call_kw(env, model, method_name, args, kwargs)
            return create_success_response(request.id, result)

        elif method == "execute":
            # Execute CRUD operations
            model = params.get('model')
            operation = params.get('operation')
            args = params.get('args', [])
            kwargs = params.get('kwargs', {})

            if not model or not operation:
                return create_error_response(
                    request.id,
                    -32602,
                    "Invalid params: 'model' and 'operation' are required"
                )

            result = await execute_crud_operation(env, model, operation, args, kwargs)
            return create_success_response(request.id, result)

        else:
            return create_error_response(
                request.id,
                -32601,
                f"Method not found: {method}"
            )

    except ValidationError as e:
        return create_error_response(
            request.id,
            -32602,
            str(e.message),
            e.details
        )
    except NotFoundError as e:
        return create_error_response(
            request.id,
            -32001,
            str(e.message)
        )
    except Exception as e:
        return create_error_response(
            request.id,
            -32603,
            f"Internal error: {str(e)}"
        )


@router.post("/batch", response_model=List[JSONRPCResponse])
async def jsonrpc_batch_endpoint(
    requests: List[JSONRPCRequest],
    env: Environment = Depends(get_env_with_user),
) -> List[JSONRPCResponse]:
    """
    JSON-RPC 2.0 Batch Endpoint
    Processes multiple JSON-RPC requests in a single HTTP request
    """
    responses = []

    for req in requests:
        try:
            # Process each request
            response = await jsonrpc_endpoint(req, env)
            responses.append(response)
        except Exception as e:
            responses.append(
                create_error_response(
                    req.id if hasattr(req, 'id') else None,
                    -32603,
                    f"Internal error: {str(e)}"
                )
            )

    return responses


# Export router
jsonrpc_router = router
