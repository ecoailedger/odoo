"""
Generic Model Router Factory
Creates FastAPI routers for models with automatic CRUD endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends

from openflow.server.core.orm.registry import Environment
from .dependencies import get_env_with_user


def create_model_router(
    model_name: str,
    prefix: Optional[str] = None,
    tags: Optional[list] = None,
) -> APIRouter:
    """
    Create a FastAPI router for a specific model with CRUD operations

    This is useful for creating dedicated routers for important models
    with custom endpoints beyond the generic REST API.

    Args:
        model_name: Name of the model (e.g., 'res.partner')
        prefix: URL prefix (default: /api/v1/{model_name})
        tags: OpenAPI tags (default: [model_name])

    Returns:
        Configured APIRouter instance

    Example:
        ```python
        from openflow.server.core.api import create_model_router

        # Create dedicated router for partners
        partner_router = create_model_router('res.partner')

        # Add custom endpoints
        @partner_router.get('/customers')
        async def get_customers(env = Depends(get_env_with_user)):
            partners = await env['res.partner'].search([('customer', '=', True)])
            return serialize_recordset(partners)

        # Register in main app
        app.include_router(partner_router)
        ```
    """
    if prefix is None:
        prefix = f"/api/v1/{model_name.replace('.', '/')}"

    if tags is None:
        tags = [model_name]

    router = APIRouter(prefix=prefix, tags=tags)

    # Router is ready for custom endpoint registration
    # The generic CRUD operations are already provided by rest.py
    # This factory is for adding model-specific custom endpoints

    return router
