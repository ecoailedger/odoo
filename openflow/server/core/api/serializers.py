"""
Record Serialization
Converts ORM records to JSON-compatible dictionaries
"""

from typing import Any, Dict, List, Optional, Set
from datetime import date, datetime
from decimal import Decimal


def serialize_value(value: Any) -> Any:
    """
    Serialize a single field value to JSON-compatible format
    """
    if value is None:
        return None

    # Handle RecordSet (Many2one, One2many, Many2many)
    if hasattr(value, '__class__') and hasattr(value.__class__, '_name'):
        # It's a RecordSet
        if len(value) == 0:
            return False  # Odoo convention for empty Many2one
        elif len(value) == 1 and hasattr(value, 'id'):
            # Many2one: return [id, display_name]
            return [value.id, value.display_name if hasattr(value, 'display_name') else str(value)]
        else:
            # One2many/Many2many: return list of IDs
            return [rec.id for rec in value]

    # Handle date/datetime
    if isinstance(value, (date, datetime)):
        return value.isoformat()

    # Handle Decimal
    if isinstance(value, Decimal):
        return float(value)

    # Handle bytes
    if isinstance(value, bytes):
        import base64
        return base64.b64encode(value).decode('utf-8')

    # Handle sets
    if isinstance(value, set):
        return list(value)

    # Basic types
    return value


def serialize_record(
    record: Any,
    fields: Optional[List[str]] = None,
    include_metadata: bool = False,
) -> Dict[str, Any]:
    """
    Serialize a single record to dictionary

    Args:
        record: ORM record to serialize
        fields: List of field names to include (None = all fields)
        include_metadata: Include _metadata with field types

    Returns:
        Dictionary with field values
    """
    if not record:
        return {}

    result = {}

    # Get fields to serialize
    if fields is None:
        # Get all fields from the model
        fields = list(record._fields.keys())

    # Serialize each field
    for field_name in fields:
        if field_name not in record._fields:
            continue

        try:
            value = getattr(record, field_name, None)
            result[field_name] = serialize_value(value)
        except Exception:
            # Skip fields that can't be read
            result[field_name] = False

    # Add metadata if requested
    if include_metadata:
        result['_metadata'] = {
            'model': record._name,
            'id': record.id if hasattr(record, 'id') else None,
        }

    return result


def serialize_recordset(
    records: Any,
    fields: Optional[List[str]] = None,
    include_metadata: bool = False,
) -> List[Dict[str, Any]]:
    """
    Serialize a recordset to list of dictionaries

    Args:
        records: ORM recordset to serialize
        fields: List of field names to include (None = all fields)
        include_metadata: Include _metadata with field types

    Returns:
        List of dictionaries with field values
    """
    if not records:
        return []

    return [
        serialize_record(record, fields=fields, include_metadata=include_metadata)
        for record in records
    ]


def format_success_response(
    data: Any,
    message: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Format a successful API response

    Args:
        data: Response data
        message: Optional success message
        meta: Optional metadata (pagination, etc.)

    Returns:
        Formatted response dictionary
    """
    response = {
        'success': True,
        'data': data,
    }

    if message:
        response['message'] = message

    if meta:
        response['meta'] = meta

    return response


def format_error_response(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 500,
) -> Dict[str, Any]:
    """
    Format an error API response

    Args:
        code: Error code
        message: Error message
        details: Optional error details
        status_code: HTTP status code

    Returns:
        Formatted error response
    """
    response = {
        'success': False,
        'error': {
            'code': code,
            'message': message,
        }
    }

    if details:
        response['error']['details'] = details

    return response


def parse_domain(domain_str: Optional[str]) -> List[Any]:
    """
    Parse domain string from query parameter
    Supports JSON format: [["field", "=", "value"]]

    Args:
        domain_str: JSON string representing domain

    Returns:
        Parsed domain list
    """
    if not domain_str:
        return []

    try:
        import json
        domain = json.loads(domain_str)
        if not isinstance(domain, list):
            return []
        return domain
    except Exception:
        return []


def parse_fields(fields_str: Optional[str]) -> Optional[List[str]]:
    """
    Parse fields parameter
    Supports comma-separated or JSON array

    Args:
        fields_str: Comma-separated field names or JSON array

    Returns:
        List of field names or None
    """
    if not fields_str:
        return None

    try:
        # Try JSON first
        import json
        fields = json.loads(fields_str)
        if isinstance(fields, list):
            return fields
    except Exception:
        pass

    # Try comma-separated
    if ',' in fields_str:
        return [f.strip() for f in fields_str.split(',') if f.strip()]

    # Single field
    return [fields_str.strip()] if fields_str.strip() else None
