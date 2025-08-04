"""
Logging Middleware for HealthLang AI MVP
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.metrics import record_response_time

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(f"Response: {response.status_code} - {duration:.3f}s")
        
        # Record metrics
        await record_response_time(
            endpoint=request.url.path,
            method=request.method,
            duration=duration
        )
        
        return response


def setup_logging_middleware(app):
    """Setup logging middleware"""
    app.add_middleware(LoggingMiddleware) 