"""
Rate Limiting Middleware for HealthLang AI MVP
"""

import time
import logging
from typing import Dict, Tuple
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings

logger = logging.getLogger(__name__)


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests"""
    
    def __init__(self, app):
        super().__init__(app)
        self.requests_per_minute: Dict[str, list] = {}
        self.requests_per_hour: Dict[str, list] = {}
    
    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Check rate limits
        if not self._check_rate_limit(client_ip, current_time):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": 60
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(self._get_remaining_requests(client_ip))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        return request.client.host if request.client else "unknown"
    
    def _check_rate_limit(self, client_ip: str, current_time: float) -> bool:
        """Check if request is within rate limits"""
        # Clean old entries
        self._cleanup_old_entries(client_ip, current_time)
        
        # Check minute limit
        minute_requests = self.requests_per_minute.get(client_ip, [])
        if len(minute_requests) >= settings.RATE_LIMIT_PER_MINUTE:
            return False
        
        # Check hour limit
        hour_requests = self.requests_per_hour.get(client_ip, [])
        if len(hour_requests) >= settings.RATE_LIMIT_PER_HOUR:
            return False
        
        # Add current request
        minute_requests.append(current_time)
        hour_requests.append(current_time)
        
        self.requests_per_minute[client_ip] = minute_requests
        self.requests_per_hour[client_ip] = hour_requests
        
        return True
    
    def _cleanup_old_entries(self, client_ip: str, current_time: float):
        """Remove old entries from rate limit tracking"""
        # Clean minute entries (older than 60 seconds)
        minute_requests = self.requests_per_minute.get(client_ip, [])
        minute_requests = [t for t in minute_requests if current_time - t < 60]
        self.requests_per_minute[client_ip] = minute_requests
        
        # Clean hour entries (older than 3600 seconds)
        hour_requests = self.requests_per_hour.get(client_ip, [])
        hour_requests = [t for t in hour_requests if current_time - t < 3600]
        self.requests_per_hour[client_ip] = hour_requests
    
    def _get_remaining_requests(self, client_ip: str) -> int:
        """Get remaining requests for the current minute"""
        minute_requests = self.requests_per_minute.get(client_ip, [])
        return max(0, settings.RATE_LIMIT_PER_MINUTE - len(minute_requests))


def setup_rate_limiting(app):
    """Setup rate limiting middleware"""
    app.add_middleware(RateLimitingMiddleware) 