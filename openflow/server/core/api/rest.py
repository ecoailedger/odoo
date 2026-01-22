"""
REST API Endpoints
Provides RESTful interface for model operations
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Path, Body, status
from pydantic import BaseModel, Field

from openflow.server.core.orm.registry import Environment
from .dependencies import get_env_with_user, get_env_optional_auth
from .exceptions import ValidationError, NotFoundError
from .serializers import (
    serialize_record,
    serialize_recordset,
    format_success_response,
    parse_domain,
    parse_fields,
)

router = APIRouter(prefix="/api/v1", tags=["REST API"])


class RecordCreateRequest(BaseModel):
    """Request body for creating records"""
    values: Dict[str, Any] = Field(..., description="Field values for the new record")


class RecordUpdateRequest(BaseModel):
    """Request body for updating records"""
    values: Dict[str, Any] = Field(..., description="Field values to update")


class RecordResponse(BaseModel):
    """Response for single record operations"""
    success: bool = True
    data: Dict[str, Any]
    message: Optional[str] = None


class RecordListResponse(BaseModel):
    """Response for list operations"""
    success: bool = True
    data: List[Dict[str, Any]]
    meta: Optional[Dict[str, Any]] = None


class DeleteResponse(BaseModel):
    """Response for delete operations"""
    success: bool = True
    message: str = "Record(s) deleted successfully"


@router.get("/{model}", response_model=RecordListResponse)
async def list_records(
    model: str = Path(..., description="Model name (e.g., 'res.partner')"),
    domain: Optional[str] = Query(None, description="Search domain as JSON string"),
    fields: Optional[str] = Query(None, description="Comma-separated field names or JSON array"),
    limit: Optional[int] = Query(80, ge=1, le=1000, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    order: Optional[str] = Query(None, description="Sort order (e.g., 'name ASC, id DESC')"),
    env: Environment = Depends(get_env_with_user),
) -> RecordListResponse:
    """
    List/search records

    Query parameters:
        - domain: Search criteria as JSON (e.g., [["name", "like", "John"]])
        - fields: Fields to include (e.g., "name,email" or ["name","email"])
        - limit: Maximum records to return (default: 80, max: 1000)
        - offset: Number of records to skip for pagination
        - order: Sort order (e.g., "name ASC, id DESC")

    Example:
        GET /api/v1/res.partner?domain=[["is_company","=",true]]&fields=name,email&limit=10
    """
    # Validate model exists
    if model not in env.registry.models:
        raise NotFoundError(f"Model '{model}' not found")

    model_class = env[model]

    # Parse parameters
    search_domain = parse_domain(domain)
    field_list = parse_fields(fields)

    # Execute search
    records = await model_class.search(
        search_domain,
        limit=limit,
        offset=offset,
        order=order,
    )

    # Serialize results
    data = serialize_recordset(records, fields=field_list)

    # Build response with metadata
    return RecordListResponse(
        data=data,
        meta={
            'total': len(records),
            'limit': limit,
            'offset': offset,
            'count': len(data),
        }
    )


@router.get("/{model}/{record_id}", response_model=RecordResponse)
async def get_record(
    model: str = Path(..., description="Model name"),
    record_id: int = Path(..., description="Record ID", gt=0),
    fields: Optional[str] = Query(None, description="Fields to include"),
    env: Environment = Depends(get_env_with_user),
) -> RecordResponse:
    """
    Get a single record by ID

    Example:
        GET /api/v1/res.partner/42?fields=name,email,phone
    """
    # Validate model exists
    if model not in env.registry.models:
        raise NotFoundError(f"Model '{model}' not found")

    model_class = env[model]
    field_list = parse_fields(fields)

    # Fetch record
    record = await model_class.browse(record_id)

    if not record or not record.id:
        raise NotFoundError(f"Record with ID {record_id} not found in model '{model}'")

    # Serialize record
    data = serialize_record(record, fields=field_list)

    return RecordResponse(data=data)


@router.post("/{model}", response_model=RecordResponse, status_code=status.HTTP_201_CREATED)
async def create_record(
    model: str = Path(..., description="Model name"),
    request: RecordCreateRequest = Body(...),
    env: Environment = Depends(get_env_with_user),
) -> RecordResponse:
    """
    Create a new record

    Request body:
        {
            "values": {
                "name": "John Doe",
                "email": "john@example.com"
            }
        }

    Example:
        POST /api/v1/res.partner
        Body: {"values": {"name": "Acme Corp", "is_company": true}}
    """
    # Validate model exists
    if model not in env.registry.models:
        raise NotFoundError(f"Model '{model}' not found")

    model_class = env[model]

    # Validate values
    if not request.values:
        raise ValidationError("Field 'values' is required and cannot be empty")

    # Create record
    try:
        record = await model_class.create(request.values)
    except Exception as e:
        raise ValidationError(f"Failed to create record: {str(e)}")

    # Serialize created record
    data = serialize_record(record)

    return RecordResponse(
        data=data,
        message="Record created successfully"
    )


@router.put("/{model}/{record_id}", response_model=RecordResponse)
async def update_record(
    model: str = Path(..., description="Model name"),
    record_id: int = Path(..., description="Record ID", gt=0),
    request: RecordUpdateRequest = Body(...),
    env: Environment = Depends(get_env_with_user),
) -> RecordResponse:
    """
    Update an existing record

    Request body:
        {
            "values": {
                "name": "Jane Doe",
                "email": "jane@example.com"
            }
        }

    Example:
        PUT /api/v1/res.partner/42
        Body: {"values": {"name": "Updated Name"}}
    """
    # Validate model exists
    if model not in env.registry.models:
        raise NotFoundError(f"Model '{model}' not found")

    model_class = env[model]

    # Validate values
    if not request.values:
        raise ValidationError("Field 'values' is required and cannot be empty")

    # Fetch record
    record = await model_class.browse(record_id)

    if not record or not record.id:
        raise NotFoundError(f"Record with ID {record_id} not found in model '{model}'")

    # Update record
    try:
        await record.write(request.values)
    except Exception as e:
        raise ValidationError(f"Failed to update record: {str(e)}")

    # Return updated record
    data = serialize_record(record)

    return RecordResponse(
        data=data,
        message="Record updated successfully"
    )


@router.delete("/{model}/{record_id}", response_model=DeleteResponse)
async def delete_record(
    model: str = Path(..., description="Model name"),
    record_id: int = Path(..., description="Record ID", gt=0),
    env: Environment = Depends(get_env_with_user),
) -> DeleteResponse:
    """
    Delete a record

    Example:
        DELETE /api/v1/res.partner/42
    """
    # Validate model exists
    if model not in env.registry.models:
        raise NotFoundError(f"Model '{model}' not found")

    model_class = env[model]

    # Fetch record
    record = await model_class.browse(record_id)

    if not record or not record.id:
        raise NotFoundError(f"Record with ID {record_id} not found in model '{model}'")

    # Delete record
    try:
        await record.unlink()
    except Exception as e:
        raise ValidationError(f"Failed to delete record: {str(e)}")

    return DeleteResponse(message=f"Record {record_id} deleted successfully")


@router.post("/{model}/search", response_model=RecordListResponse)
async def search_records(
    model: str = Path(..., description="Model name"),
    domain: List[Any] = Body(default_factory=list, description="Search domain"),
    fields: Optional[List[str]] = Body(None, description="Fields to include"),
    limit: int = Body(80, ge=1, le=1000, description="Maximum records"),
    offset: int = Body(0, ge=0, description="Records to skip"),
    order: Optional[str] = Body(None, description="Sort order"),
    env: Environment = Depends(get_env_with_user),
) -> RecordListResponse:
    """
    Advanced search with POST body

    Request body:
        {
            "domain": [["name", "like", "John"], ["active", "=", true]],
            "fields": ["name", "email", "phone"],
            "limit": 50,
            "offset": 0,
            "order": "name ASC"
        }

    Example:
        POST /api/v1/res.partner/search
        Body: {"domain": [["is_company", "=", true]], "fields": ["name", "email"]}
    """
    # Validate model exists
    if model not in env.registry.models:
        raise NotFoundError(f"Model '{model}' not found")

    model_class = env[model]

    # Execute search
    records = await model_class.search(
        domain,
        limit=limit,
        offset=offset,
        order=order,
    )

    # Serialize results
    data = serialize_recordset(records, fields=fields)

    return RecordListResponse(
        data=data,
        meta={
            'total': len(records),
            'limit': limit,
            'offset': offset,
            'count': len(data),
        }
    )


@router.get("/{model}/count", response_model=Dict[str, Any])
async def count_records(
    model: str = Path(..., description="Model name"),
    domain: Optional[str] = Query(None, description="Search domain as JSON string"),
    env: Environment = Depends(get_env_with_user),
) -> Dict[str, Any]:
    """
    Count records matching domain

    Example:
        GET /api/v1/res.partner/count?domain=[["is_company","=",true]]
    """
    # Validate model exists
    if model not in env.registry.models:
        raise NotFoundError(f"Model '{model}' not found")

    model_class = env[model]

    # Parse domain
    search_domain = parse_domain(domain)

    # Execute search and count
    records = await model_class.search(search_domain)
    count = len(records)

    return format_success_response(
        data={'count': count},
        meta={'domain': search_domain}
    )


# Export router
rest_router = router
