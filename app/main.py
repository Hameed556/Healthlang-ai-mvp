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
from app.api.routes import health, query, translation
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
    
    try:
        # Initialize workflow
        logger.info("Initializing HealthLang workflow...")
        workflow = HealthLangWorkflow()
        await workflow.initialize()
        
        logger.info("Workflow initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    finally:
        logger.info("Shutting down HealthLang AI MVP application...")
        
        # Cleanup workflow
        if workflow:
            await workflow.cleanup()


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Bilingual (Yoruba-English) medical Q&A system with Groq-accelerated LLMs and RAG",
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
async def healthlang_exception_handler(request: Request, exc: HealthLangException):
    """Handle custom HealthLang exceptions"""
    logger.error(f"HealthLang exception: {exc.message}", extra={"request_id": request.state.request_id})
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
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True, extra={"request_id": request.state.request_id})
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(query.router, prefix="/api/v1", tags=["query"])
app.include_router(translation.router, prefix="/api/v1/translate", tags=["translation"])


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
        "supported_languages": ["en", "yo"],
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