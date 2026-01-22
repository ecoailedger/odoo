"""
Main FastAPI application
"""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import logging

from openflow.server.config.settings import settings
from openflow.server.core.database import init_db, close_db
from openflow.server.core.modules import module_registry

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=settings.log_format,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting OpenFlow application...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # Initialize module system
    try:
        logger.info("Initializing module system...")
        addons_path = Path(__file__).parent / "addons"
        module_registry.initialize([addons_path])
        logger.info(f"Discovered {len(module_registry.modules)} modules")

        # Load auto-install modules (e.g., base)
        auto_install = module_registry.loader.get_auto_install_modules()
        if auto_install:
            logger.info(f"Loading {len(auto_install)} auto-install modules...")
            module_registry.load_modules([m.name for m in auto_install])
            logger.info("Auto-install modules loaded successfully")
    except Exception as e:
        logger.error(f"Failed to initialize modules: {e}")
        # Don't raise - allow app to start even if modules fail to load

    yield

    # Shutdown
    logger.info("Shutting down OpenFlow application...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="An open-source ERP framework inspired by Odoo",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to OpenFlow",
        "version": settings.version,
        "environment": settings.environment,
        "docs": "/docs" if settings.debug else "disabled",
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.version,
    }


# API routes
from openflow.server.core.api import jsonrpc_router, rest_router

# JSON-RPC endpoint
app.include_router(jsonrpc_router)

# REST API endpoints
app.include_router(rest_router)

# Static files
static_path = Path(__file__).parent.parent.parent / "web" / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Web client route
@app.get("/web")
async def web_client():
    """Serve the web client"""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Web client not found"}


# Exception handlers
from openflow.server.core.api.exceptions import APIException


@app.exception_handler(APIException)
async def api_exception_handler(request, exc: APIException):
    """Handle API exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
    )


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"},
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "openflow.server.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.workers,
    )
