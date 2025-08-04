"""
Logging utilities for HealthLang AI MVP
"""

import logging
import sys
from typing import Optional
from datetime import datetime
import json

from loguru import logger
from app.config import settings


class InterceptHandler(logging.Handler):
    """Intercept standard logging and redirect to loguru"""
    
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    """Setup application logging configuration"""
    
    # Remove default loguru handler
    logger.remove()
    
    # Configure loguru with human-readable format (simpler for now)
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Add console handler
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # Add file handler if log file is specified
    if settings.LOG_FILE:
        logger.add(
            settings.LOG_FILE,
            format=log_format,
            level=settings.LOG_LEVEL,
            rotation="10 MB",
            retention="7 days",
            compression="gz",
            backtrace=True,
            diagnose=True,
        )
    
    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Set loguru as the default logger for third-party libraries
    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True


def get_logger(name: Optional[str] = None) -> logger:
    """Get a logger instance with the given name"""
    if name is None:
        # Get the calling module name
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    return logger.bind(module=name)


class RequestLogger:
    """Request-specific logger for tracking request flow"""
    
    def __init__(self, request_id: str, module: str = "request"):
        self.request_id = request_id
        self.logger = logger.bind(request_id=request_id, module=module)
    
    def info(self, message: str, **kwargs):
        """Log info message with request context"""
        self.logger.info(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with request context"""
        self.logger.error(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with request context"""
        self.logger.debug(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with request context"""
        self.logger.warning(message, **kwargs)


class PerformanceLogger:
    """Logger for performance metrics"""
    
    def __init__(self, operation: str):
        self.operation = operation
        self.start_time = None
        self.logger = logger.bind(operation=operation)
    
    def start(self):
        """Start timing an operation"""
        self.start_time = datetime.now()
        self.logger.info(f"Starting {self.operation}")
    
    def end(self, success: bool = True, **kwargs):
        """End timing an operation and log results"""
        if self.start_time is None:
            self.logger.warning(f"End called without start for {self.operation}")
            return
        
        duration = (datetime.now() - self.start_time).total_seconds()
        status = "success" if success else "error"
        
        self.logger.info(
            f"Completed {self.operation}",
            duration=duration,
            status=status,
            **kwargs
        )
        
        self.start_time = None


class StructuredLogger:
    """Logger for structured data"""
    
    def __init__(self, module: str = "structured"):
        self.logger = logger.bind(module=module)
    
    def log_event(self, event_type: str, data: dict, level: str = "info"):
        """Log a structured event"""
        log_data = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }
        
        if level == "info":
            self.logger.info("Structured event", **log_data)
        elif level == "error":
            self.logger.error("Structured event", **log_data)
        elif level == "warning":
            self.logger.warning("Structured event", **log_data)
        elif level == "debug":
            self.logger.debug("Structured event", **log_data)
    
    def log_metric(self, metric_name: str, value: float, tags: dict = None):
        """Log a metric"""
        metric_data = {
            "metric_name": metric_name,
            "value": value,
            "tags": tags or {},
            "timestamp": datetime.now().isoformat(),
        }
        
        self.logger.info("Metric", **metric_data)
    
    def log_error(self, error: Exception, context: dict = None):
        """Log an error with context"""
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
        }
        
        self.logger.error("Error occurred", **error_data)


# Initialize logging on module import
setup_logging() 