"""
Main FastAPI application for HealthLang AI MVP
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from app.config import settings
from app.core.exceptions import HealthLangException
from app.utils.logger import setup_logging, get_logger
from app.api.routes import health, query, translation, auth
from app.api.routes import chat as chat_routes
from app.api.middleware.cors import setup_cors
from app.api.middleware.logging import setup_logging_middleware
from app.api.middleware.rate_limiting import setup_rate_limiting
from app.core.workflow import HealthLangWorkflow
from app.utils.metrics import setup_metrics

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Global workflow instance
workflow: HealthLangWorkflow = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global workflow

    logger.info("Starting HealthLang AI MVP application...")

    # Initialize database
    try:
        from app.database import init_db, check_database_connection
        logger.info("Checking database connection...")
        if check_database_connection():
            logger.info("Initializing database tables...")
            init_db()
            logger.info("Database initialized successfully")
        else:
            logger.warning(
                "Database connection failed, continuing without database"
            )
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    try:
        # Initialize workflow (non-fatal; query route lazily creates one)
        try:
            logger.info("Initializing HealthLang workflow...")
            global workflow
            workflow = HealthLangWorkflow()
            await workflow.initialize()
            app.state.workflow = workflow  # Store in app.state for route access
            logger.info("Workflow initialized successfully")
        except Exception as e:
            logger.error(f"Workflow initialization failed (continuing): {e}")

        # Expose services on app.state for health endpoints.
    # Each init is best-effort; failures are logged, startup continues.
        try:
            from app.services.translation.translator import TranslationService
            app.state.translation_service = TranslationService()
            await app.state.translation_service.initialize()
            logger.info("TranslationService initialized")
        except Exception as e:
            logger.error(f"TranslationService initialization failed: {e}")

        try:
            from app.services.medical.llm_client import LLMClient
            app.state.llm_client = LLMClient()
            logger.info("LLMClient initialized")
        except Exception as e:
            logger.error(f"LLMClient initialization failed: {e}")

        try:
            from app.services.rag.vector_store import VectorStore
            app.state.vector_store = VectorStore()
            logger.info("VectorStore initialized")
        except Exception as e:
            logger.error(f"VectorStore initialization failed: {e}")

        yield

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    finally:
        logger.info("Shutting down HealthLang AI MVP application...")

        # Cleanup workflow
        if workflow:
            await workflow.cleanup()
        # Cleanup translation service
        if hasattr(app.state, "translation_service"):
            await app.state.translation_service.cleanup()


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "English-first medical Q&A system with Groq LLMs, MCP tools, "
        "and optional RAG (translate endpoints preserved for future voice "
        "features)"
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",  # Always enable docs
    redoc_url="/redoc",  # Always enable redoc
    openapi_url="/openapi.json",  # Always enable openapi
    lifespan=lifespan,
    # Ensure proper UTF-8 encoding for Yoruba characters
    default_response_class=JSONResponse,
)

# Setup middleware
setup_cors(app)
setup_logging_middleware(app)
setup_rate_limiting(app)

# Setup metrics
if settings.PROMETHEUS_ENABLED:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    setup_metrics()


# Global exception handler
@app.exception_handler(HealthLangException)
async def healthlang_exception_handler(
    request: Request,
    exc: HealthLangException,
):
    """Handle custom HealthLang exceptions"""
    logger.error(
        f"HealthLang exception: {exc.message}",
        extra={"request_id": request.state.request_id},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "error_code": exc.error_code,
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    request_id = getattr(request.state, "request_id", None)
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={"request_id": request_id},
    )
    # In development, expose the exception message to help debugging
    content = {
        "error": (
            str(exc)
            if (settings.DEBUG or settings.ENVIRONMENT == "development")
            else "Internal server error"
        ),
        "error_code": "INTERNAL_ERROR",
        "request_id": request_id,
    }
    return JSONResponse(status_code=500, content=content)


# Include routers
app.include_router(health.router)
app.include_router(query.router, prefix="/api/v1", tags=["query"])
app.include_router(
    translation.router,
    prefix="/api/v1/translate",
    tags=["translation"],
)
app.include_router(
    auth.router,
    prefix="/api/v1",
    tags=["authentication"],
)
app.include_router(
    chat_routes.router,
    prefix="/api/v1",
    tags=["chat"],
)


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint"""
    return {
        "message": "Welcome to HealthLang AI MVP",
        "version": settings.APP_VERSION,
        "status": "healthy",
        "docs": "/docs" if settings.DEBUG else None,
    }


@app.get("/info")
async def info() -> Dict[str, Any]:
    """Application information endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "supported_languages": ["en"],
        "rag_enabled": settings.RAG_ENABLED,
        "medical_model": settings.MEDICAL_MODEL_NAME,
        "vector_db_type": settings.VECTOR_DB_TYPE,
    }


def main():
    """Main entry point for the application"""
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS if not settings.RELOAD else 1,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
