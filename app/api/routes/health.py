"""
Health check endpoints for HealthLang AI MVP
"""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Request
from prometheus_client import Counter, Histogram, Gauge

from app.config import settings
from app.utils.logger import get_logger
from app.utils.metrics import get_metrics
from app.services.mcp_client_http import mcp_get
from app.core.exceptions import MCPClientError

logger = get_logger(__name__)

router = APIRouter()


@router.get("/mcp-health")
async def mcp_health_check() -> Dict[str, Any]:
    """Health check for the configured MCP server."""
    try:
        data = await mcp_get("/health")
        return {"status": "ok", "mcp": data}
    except MCPClientError as e:
        return {"status": "error", "error": e.message, "code": e.status_code}
    except Exception as e:
        # Preserve a final safety net but surface a readable message
        return {"status": "error", "error": str(e)}

# Metrics
health_check_counter = Counter(
    "healthlang_health_checks_total",
    "Total number of health checks",
    ["endpoint", "status"]
)

health_check_duration = Histogram(
    "healthlang_health_check_duration_seconds",
    "Health check duration in seconds",
    ["endpoint"]
)

service_status_gauge = Gauge(
    "healthlang_service_status",
    "Service status (1=healthy, 0=unhealthy)",
    ["service"]
)


@router.get("/")
@router.get("/health")
async def health_check(request: Request) -> Dict[str, Any]:
    """
    Basic health check endpoint
    
    Returns:
        Basic health status information
    """
    start_time = datetime.now()
    
    try:
        # Basic health check
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "request_id": getattr(request.state, "request_id", None),
            "services": {},  # Added for test compatibility
        }
        
        # Record metrics
        health_check_counter.labels(endpoint="basic", status="success").inc()
        service_status_gauge.labels(service="api").set(1)
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        health_check_counter.labels(endpoint="basic", status="error").inc()
        service_status_gauge.labels(service="api").set(0)
        
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "request_id": getattr(request.state, "request_id", None),
            "services": {},
        }
    finally:
        duration = (datetime.now() - start_time).total_seconds()
        health_check_duration.labels(endpoint="basic").observe(duration)


@router.get("/detailed")
@router.get("/health/detailed")
async def detailed_health_check(request: Request) -> Dict[str, Any]:
    """
    Detailed health check endpoint
    
    Returns:
        Detailed health status including all services
    """
    start_time = datetime.now()
    
    try:
        # Access global services via FastAPI app state
        app = request.app
        translation_service = getattr(app.state, "translation_service", None)
        llm_client = getattr(app.state, "llm_client", None)
        vector_store = getattr(app.state, "vector_store", None)

        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "request_id": getattr(request.state, "request_id", None),
            "services": {},
            "uptime": 0,  # Placeholder for uptime
        }

        # Check translation service
        if translation_service:
            try:
                translation_health = await translation_service.health_check()
                health_status["services"]["translation"] = translation_health
                service_status_gauge.labels(service="translation").set(
                    1 if translation_health.get("status") == "healthy" else 0
                )
            except Exception as e:
                logger.error(f"Translation service health check failed: {e}")
                health_status["services"]["translation"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                service_status_gauge.labels(service="translation").set(0)
        else:
            health_status["services"]["translation"] = {
                "status": "not_initialized"
            }
            service_status_gauge.labels(service="translation").set(0)

        # Check LLM client
        if llm_client:
            try:
                llm_health = await llm_client.health_check()
                health_status["services"]["llm"] = llm_health
                service_status_gauge.labels(service="llm").set(
                    1 if llm_health.get("status") == "healthy" else 0
                )
            except Exception as e:
                logger.error(f"LLM client health check failed: {e}")
                health_status["services"]["llm"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                service_status_gauge.labels(service="llm").set(0)
        else:
            health_status["services"]["llm"] = {"status": "not_initialized"}
            service_status_gauge.labels(service="llm").set(0)
        
        # Check vector store
        if vector_store:
            try:
                vector_health = await vector_store.health_check()
                health_status["services"]["vector_store"] = vector_health
                service_status_gauge.labels(service="vector_store").set(
                    1 if vector_health.get("status") == "healthy" else 0
                )
            except Exception as e:
                logger.error(f"Vector store health check failed: {e}")
                health_status["services"]["vector_store"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                service_status_gauge.labels(service="vector_store").set(0)
        else:
            health_status["services"]["vector_store"] = {
                "status": "not_initialized"
            }
            service_status_gauge.labels(service="vector_store").set(0)
        
        # Check Redis cache
        try:
            from app.utils.cache import Cache
            cache = Cache()
            await cache.initialize()
            cache_health = await cache.health_check()
            health_status["services"]["cache"] = cache_health
            service_status_gauge.labels(service="cache").set(
                1 if cache_health.get("status") == "healthy" else 0
            )
            await cache.cleanup()
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            health_status["services"]["cache"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            service_status_gauge.labels(service="cache").set(0)
        
        # Determine overall status
        all_healthy = all(
            service.get("status") == "healthy"
            for service in health_status["services"].values()
        )
        
        if not all_healthy:
            health_status["status"] = "degraded"
        
        # Record metrics
        health_check_counter.labels(
            endpoint="detailed",
            status="success",
        ).inc()
        
        return health_status
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        health_check_counter.labels(endpoint="detailed", status="error").inc()
        
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "request_id": getattr(request.state, "request_id", None),
            "services": {},
            "uptime": 0,
        }
    finally:
        duration = (datetime.now() - start_time).total_seconds()
        health_check_duration.labels(endpoint="detailed").observe(duration)


@router.get("/readiness")
@router.get("/health/readiness")
async def readiness_check(request: Request) -> Dict[str, Any]:
    """
    Readiness check endpoint for Kubernetes
    
    Returns:
        Readiness status for the application
    """
    start_time = datetime.now()

    try:
        # Access global services via FastAPI app state
        app = request.app
        translation_service = getattr(app.state, "translation_service", None)
        llm_client = getattr(app.state, "llm_client", None)
        vector_store = getattr(app.state, "vector_store", None)

        ready_services = []
        not_ready_services = []

        # Check translation service
        if translation_service:
            try:
                health = await translation_service.health_check()
                if health.get("status") == "healthy":
                    ready_services.append("translation")
                else:
                    not_ready_services.append("translation")
            except Exception:
                not_ready_services.append("translation")
        else:
            not_ready_services.append("translation")

        # Check LLM client
        if llm_client:
            try:
                health = await llm_client.health_check()
                if health.get("status") == "healthy":
                    ready_services.append("llm")
                else:
                    not_ready_services.append("llm")
            except Exception:
                not_ready_services.append("llm")
        else:
            not_ready_services.append("llm")

        # Check vector store
        if vector_store:
            try:
                health = await vector_store.health_check()
                logger.info(
                    f"[Readiness] Vector store health check result: {health}"
                )
                # Treat dummy backend as ready
                if health.get("status") == "healthy" and (
                    health.get("store_type") in {
                        "dummy",
                        "chroma",
                        "ephemeral",
                    }
                ):
                    logger.info(
                        (
                            "[Readiness] Vector store marked as ready "
                            "(dummy/chroma/ephemeral backend)"
                        )
                    )
                    ready_services.append("vector_store")
                elif health.get("status") == "healthy":
                    logger.info(
                        (
                            "[Readiness] Vector store marked as ready "
                            "(other backend)"
                        )
                    )
                    ready_services.append("vector_store")
                else:
                    logger.info("[Readiness] Vector store marked as not ready")
                    not_ready_services.append("vector_store")
            except Exception as e:
                logger.error(
                    ("[Readiness] Exception during vector store health check: "
                     f"{e}")
                )
                not_ready_services.append("vector_store")
        else:
            logger.info(
                "[Readiness] Vector store not initialized, marked as not ready"
            )
            not_ready_services.append("vector_store")

        # Determine readiness
        is_ready = len(not_ready_services) == 0
        status_str = "ready" if is_ready else "not_ready"

        readiness_status = {
            "status": status_str,
            "timestamp": datetime.now().isoformat(),
            "ready_services": ready_services,
            "not_ready_services": not_ready_services,
            "request_id": getattr(request.state, "request_id", None),
        }

        # Record metrics
        health_check_counter.labels(
            endpoint="readiness",
            status=status_str,
        ).inc()

        return readiness_status

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        health_check_counter.labels(endpoint="readiness", status="error").inc()

        return {
            "status": "not_ready",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "ready_services": [],
            "not_ready_services": [],
            "request_id": getattr(request.state, "request_id", None),
        }
    finally:
        duration = (datetime.now() - start_time).total_seconds()
        health_check_duration.labels(endpoint="readiness").observe(duration)


@router.get("/liveness")
@router.get("/health/liveness")
async def liveness_check(request: Request) -> Dict[str, Any]:
    """
    Liveness check endpoint for Kubernetes
    
    Returns:
        Liveness status for the application
    """
    start_time = datetime.now()
    
    try:
        # Simple liveness check - just verify the application is running
        liveness_status = {
            "status": "alive",
            "timestamp": datetime.now().isoformat(),
            "request_id": getattr(request.state, "request_id", None),
        }
        
        # Record metrics
        health_check_counter.labels(endpoint="liveness", status="alive").inc()
        
        return liveness_status
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        health_check_counter.labels(endpoint="liveness", status="dead").inc()
        
        return {
            "status": "dead",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "request_id": getattr(request.state, "request_id", None),
        }
    finally:
        duration = (datetime.now() - start_time).total_seconds()
        health_check_duration.labels(endpoint="liveness").observe(duration)


# NOTE: Prometheus is mounted at `/metrics` in app.main. Expose a JSON summary
# under a different path to avoid conflicting with Prometheus text format.
@router.get("/metrics/summary")
async def metrics_summary_endpoint() -> Dict[str, Any]:
    """
    Application metrics endpoint
    
    Returns:
        Current application metrics
    """
    try:
        metrics = get_metrics()
        return {
            "metrics": metrics,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
