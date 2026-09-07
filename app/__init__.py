"""
LogPulse - AI-Powered Real-Time Analytics Backend.

Main application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi

from app.api.v1 import api_router
from app.core.bootstrap import ensure_admin_user
from app.core.config import settings
from app.db import init_db, close_db
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events."""
    # Startup
    try:
        logger.info(f"Initializing {settings.APP_NAME}")
        await init_db()
        logger.info("Database initialized successfully")
        await ensure_admin_user()
    except Exception as exc:
        logger.error(f"Failed to initialize database: {exc}", exc_info=True)
        raise

    yield

    # Shutdown
    try:
        logger.info("Shutting down application")
        await close_db()
        logger.info("Application shutdown complete")
    except Exception as exc:
        logger.error(f"Error during shutdown: {exc}", exc_info=True)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="Real-time log analytics with AI-powered insights",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Add security scheme for Swagger UI
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=settings.APP_NAME,
            version="0.1.0",
            description="Real-time log analytics with AI-powered insights",
            routes=app.routes,
        )
        openapi_schema["components"]["securitySchemes"] = {
            "bearer": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token obtained from /api/v1/auth/login endpoint"
            }
        }
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # Security and CORS middleware
    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    # Endpoints
    @app.get("/health", tags=["health"])
    async def health_check() -> dict:
        """Health check endpoint."""
        return {"status": "healthy", "version": "0.1.0"}

    @app.get("/", tags=["root"])
    async def root() -> dict:
        """Root endpoint."""
        return {
            "name": settings.APP_NAME,
            "version": "0.1.0",
            "docs_url": "/docs",
        }

    # Exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors."""
        logger.warning(f"Validation error for {request.url.path}: {len(exc.errors())} errors")
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unhandled exceptions."""
        logger.error(
            f"Unhandled exception {type(exc).__name__} for {request.method} {request.url.path}: {exc}",
            exc_info=True,
        )
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    logger.info(f"Application factory created for {settings.APP_NAME}")
    return app


# Application instance
app = create_app()

__all__ = ["app", "create_app"]
