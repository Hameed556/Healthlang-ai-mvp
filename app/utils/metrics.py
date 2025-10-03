"""
Metrics utilities for HealthLang AI MVP
"""

from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from prometheus_client import Counter, Histogram, Gauge, Summary
from app.utils.logger import get_logger
from app.config import settings

logger = get_logger(__name__)


# Global metrics
pipeline_requests_total = Counter(
    "healthlang_pipeline_requests_total",
    "Total number of pipeline requests",
    ["status", "source_language", "target_language"]
)

pipeline_duration_seconds = Histogram(
    "healthlang_pipeline_duration_seconds",
    "Pipeline processing duration in seconds",
    ["source_language", "target_language"]
)

translation_requests_total = Counter(
    "healthlang_translation_requests_total",
    "Total number of translation requests",
    ["status", "source_language", "target_language"]
)

translation_duration_seconds = Histogram(
    "healthlang_translation_duration_seconds",
    "Translation processing duration in seconds",
    ["source_language", "target_language"]
)

llm_requests_total = Counter(
    "healthlang_llm_requests_total",
    "Total number of LLM requests",
    ["status", "model", "provider"]
)

llm_duration_seconds = Histogram(
    "healthlang_llm_duration_seconds",
    "LLM processing duration in seconds",
    ["model", "provider"]
)

rag_requests_total = Counter(
    "healthlang_rag_requests_total",
    "Total number of RAG requests",
    ["status", "vector_store"]
)

rag_duration_seconds = Histogram(
    "healthlang_rag_duration_seconds",
    "RAG processing duration in seconds",
    ["vector_store"]
)

cache_hits_total = Counter(
    "healthlang_cache_hits_total",
    "Total number of cache hits",
    ["cache_type"]
)

cache_misses_total = Counter(
    "healthlang_cache_misses_total",
    "Total number of cache misses",
    ["cache_type"]
)

active_connections = Gauge(
    "healthlang_active_connections",
    "Number of active connections",
    ["service"]
)

error_rate = Counter(
    "healthlang_errors_total",
    "Total number of errors",
    ["error_type", "service"]
)

response_time_summary = Summary(
    "healthlang_response_time_seconds",
    "Response time summary",
    ["endpoint", "method"]
)


@dataclass
class PipelineMetrics:
    """Metrics data for pipeline processing"""
    request_id: str
    source_language: str
    target_language: str
    duration: float
    success: bool
    translation_duration: Optional[float] = None
    rag_duration: Optional[float] = None
    llm_duration: Optional[float] = None
    cache_hit: bool = False
    documents_retrieved: int = 0
    tokens_used: Optional[int] = None


@dataclass
class QueryMetrics:
    """Metrics data for query processing"""
    request_id: str
    source_language: str
    target_language: str
    duration: float
    success: bool
    query_length: int
    response_length: int


def setup_metrics() -> None:
    """Setup application metrics"""
    logger.info("Setting up application metrics")
    
    # Initialize any additional metrics setup here
    # For now, the metrics are defined as global variables above


async def record_pipeline_metrics(metrics: PipelineMetrics) -> None:
    """Record pipeline processing metrics"""
    try:
        # Record pipeline request
        status = "success" if metrics.success else "error"
        pipeline_requests_total.labels(
            status=status,
            source_language=metrics.source_language,
            target_language=metrics.target_language
        ).inc()
        
        # Record pipeline duration
        pipeline_duration_seconds.labels(
            source_language=metrics.source_language,
            target_language=metrics.target_language
        ).observe(metrics.duration)
        
        # Record translation metrics if available
        if metrics.translation_duration is not None:
            translation_requests_total.labels(
                status=status,
                source_language=metrics.source_language,
                target_language=metrics.target_language
            ).inc()
            
            translation_duration_seconds.labels(
                source_language=metrics.source_language,
                target_language=metrics.target_language
            ).observe(metrics.translation_duration)
        
        # Record RAG metrics if available
        if metrics.rag_duration is not None:
            rag_requests_total.labels(
                status=status,
                vector_store="chroma"  # Default for now
            ).inc()
            
            rag_duration_seconds.labels(
                vector_store="chroma"
            ).observe(metrics.rag_duration)
        
        # Record LLM metrics if available
        if metrics.llm_duration is not None:
            llm_requests_total.labels(
                status=status,
                model=(
                    settings.GROQ_MODEL
                    if getattr(
                        settings,
                        "MEDICAL_MODEL_PROVIDER",
                        "groq",
                    ).lower()
                    == "groq"
                    else settings.MEDICAL_MODEL_NAME
                ),
                provider="groq"
            ).inc()
            
            llm_duration_seconds.labels(
                model=(
                    settings.GROQ_MODEL
                    if getattr(
                        settings,
                        "MEDICAL_MODEL_PROVIDER",
                        "groq",
                    ).lower()
                    == "groq"
                    else settings.MEDICAL_MODEL_NAME
                ),
                provider="groq"
            ).observe(metrics.llm_duration)
        
        # Record cache metrics
        if metrics.cache_hit:
            cache_hits_total.labels(cache_type="redis").inc()
        else:
            cache_misses_total.labels(cache_type="redis").inc()
        
        logger.debug(
            "Recorded pipeline metrics for request %s",
            metrics.request_id,
        )
        
    except Exception as e:
        logger.error(f"Failed to record pipeline metrics: {e}")


async def record_query_metrics(
    request_id: str,
    source_language: str,
    target_language: str,
    duration: float,
    success: bool,
    query_length: Optional[int] = None,
    response_length: Optional[int] = None,
) -> None:
    """Record query processing metrics"""
    try:
        # Record query metrics
        
        # Record error if not successful
        if not success:
            error_rate.labels(
                error_type="query_processing",
                service="api"
            ).inc()
        
        logger.debug(
            "Recorded query metrics for request %s",
            request_id,
        )
        
    except Exception as e:
        logger.error(f"Failed to record query metrics: {e}")


async def record_translation_metrics(
    request_id: str,
    source_language: str,
    target_language: str,
    duration: float,
    success: bool,
    text_length: int,
) -> None:
    """Record translation metrics"""
    try:
        status = "success" if success else "error"
        
        translation_requests_total.labels(
            status=status,
            source_language=source_language,
            target_language=target_language
        ).inc()
        
        translation_duration_seconds.labels(
            source_language=source_language,
            target_language=target_language
        ).observe(duration)
        
        if not success:
            error_rate.labels(
                error_type="translation",
                service="translation"
            ).inc()
        
        logger.debug(f"Recorded translation metrics for request {request_id}")
        
    except Exception as e:
        logger.error(f"Failed to record translation metrics: {e}")


async def record_llm_metrics(
    request_id: str,
    model: str,
    provider: str,
    duration: float,
    success: bool,
    tokens_used: Optional[int] = None,
) -> None:
    """Record LLM metrics"""
    try:
        status = "success" if success else "error"
        
        llm_requests_total.labels(
            status=status,
            model=model,
            provider=provider
        ).inc()
        
        llm_duration_seconds.labels(
            model=model,
            provider=provider
        ).observe(duration)
        
        if not success:
            error_rate.labels(
                error_type="llm",
                service="medical"
            ).inc()
        
        logger.debug(f"Recorded LLM metrics for request {request_id}")
        
    except Exception as e:
        logger.error(f"Failed to record LLM metrics: {e}")


async def record_rag_metrics(
    request_id: str,
    vector_store: str,
    duration: float,
    success: bool,
    documents_retrieved: int,
) -> None:
    """Record RAG metrics"""
    try:
        status = "success" if success else "error"
        
        rag_requests_total.labels(
            status=status,
            vector_store=vector_store
        ).inc()
        
        rag_duration_seconds.labels(
            vector_store=vector_store
        ).observe(duration)
        
        if not success:
            error_rate.labels(
                error_type="rag",
                service="rag"
            ).inc()
        
        logger.debug(f"Recorded RAG metrics for request {request_id}")
        
    except Exception as e:
        logger.error(f"Failed to record RAG metrics: {e}")


async def record_cache_metrics(
    cache_type: str,
    hit: bool,
    duration: Optional[float] = None,
) -> None:
    """Record cache metrics"""
    try:
        if hit:
            cache_hits_total.labels(cache_type=cache_type).inc()
        else:
            cache_misses_total.labels(cache_type=cache_type).inc()
        
        logger.debug(f"Recorded cache metrics: {cache_type}, hit={hit}")
        
    except Exception as e:
        logger.error(f"Failed to record cache metrics: {e}")


async def record_connection_metrics(
    service: str,
    connected: bool,
) -> None:
    """Record connection metrics"""
    try:
        if connected:
            active_connections.labels(service=service).inc()
        else:
            active_connections.labels(service=service).dec()
        
        logger.debug(
            "Recorded connection metrics: %s, connected=%s",
            service,
            connected,
        )
        
    except Exception as e:
        logger.error(f"Failed to record connection metrics: {e}")


async def record_response_time(
    endpoint: str,
    method: str,
    duration: float,
) -> None:
    """Record response time metrics"""
    try:
        response_time_summary.labels(
            endpoint=endpoint,
            method=method
        ).observe(duration)
        
        logger.debug(
            "Recorded response time: %s %s, %ss",
            endpoint,
            method,
            duration,
        )
        
    except Exception as e:
        logger.error(f"Failed to record response time: {e}")


def get_metrics() -> Dict[str, Any]:
    """Get current application metrics"""
    try:
        # This would typically return metrics from Prometheus
        # For MVP, we'll return a basic structure
        return {
            "pipeline_requests": {
                "total": 0,  # Would be from Prometheus
                "success": 0,
                "error": 0,
            },
            "translation_requests": {
                "total": 0,
                "success": 0,
                "error": 0,
            },
            "llm_requests": {
                "total": 0,
                "success": 0,
                "error": 0,
            },
            "rag_requests": {
                "total": 0,
                "success": 0,
                "error": 0,
            },
            "cache": {
                "hits": 0,
                "misses": 0,
                "hit_rate": 0.0,
            },
            "connections": {
                "active": 0,
            },
            "errors": {
                "total": 0,
                "by_type": {},
            },
            "response_times": {
                "average": 0.0,
                "p95": 0.0,
                "p99": 0.0,
            },
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


class MetricsCollector:
    """Metrics collector for batch operations"""
    
    def __init__(self):
        self.metrics_buffer = []
    
    async def add_metric(self, metric_type: str, data: Dict[str, Any]) -> None:
        """Add a metric to the buffer"""
        self.metrics_buffer.append({
            "type": metric_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        })
    
    async def flush_metrics(self) -> None:
        """Flush all buffered metrics"""
        try:
            for metric in self.metrics_buffer:
                metric_type = metric["type"]
                data = metric["data"]
                
                if metric_type == "pipeline":
                    await record_pipeline_metrics(PipelineMetrics(**data))
                elif metric_type == "query":
                    await record_query_metrics(**data)
                elif metric_type == "translation":
                    await record_translation_metrics(**data)
                elif metric_type == "llm":
                    await record_llm_metrics(**data)
                elif metric_type == "rag":
                    await record_rag_metrics(**data)
                elif metric_type == "cache":
                    await record_cache_metrics(**data)
            
            # Clear buffer
            self.metrics_buffer.clear()
            
            logger.info(f"Flushed {len(self.metrics_buffer)} metrics")
            
        except Exception as e:
            logger.error(f"Failed to flush metrics: {e}")
    
    def get_buffer_size(self) -> int:
        """Get current buffer size"""
        return len(self.metrics_buffer)


async def record_medical_analysis(
    request_id: str,
    analysis_type: str,
    duration: float,
    success: bool,
    error_type: Optional[str] = None,
) -> None:
    """Record medical analysis metrics"""
    try:
        status = "success" if success else "error"
        
        # This would use actual Prometheus metrics if they were defined
        # For now, just log the metrics
        logger.info(
            "Medical analysis metrics: %s, %s, %.2fs",
            analysis_type,
            status,
            duration,
        )
        
        if not success and error_type:
            logger.error(f"Medical analysis error: {error_type}")
        
        logger.debug(
            "Recorded medical analysis metrics for request %s",
            request_id,
        )
        
    except Exception as e:
        logger.error(f"Failed to record medical analysis metrics: {e}")


async def record_safety_check(
    request_id: str,
    check_type: str,
    passed: bool,
    duration: float,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Record safety check metrics"""
    try:
        status = "passed" if passed else "failed"
        
        # This would use actual Prometheus metrics if they were defined
        # For now, just log the metrics
        logger.info(
            "Safety check metrics: %s, %s, %.2fs",
            check_type,
            status,
            duration,
        )
        
        if not passed and details:
            logger.warning(f"Safety check failed: {details}")
        
        logger.debug(f"Recorded safety check metrics for request {request_id}")
        
    except Exception as e:
        logger.error(f"Failed to record safety check metrics: {e}")


async def record_response_formatting(
    request_id: str,
    format_type: str,
    duration: float,
    success: bool,
    error_type: Optional[str] = None,
) -> None:
    """Record response formatting metrics"""
    try:
        status = "success" if success else "error"
        
        # This would use actual Prometheus metrics if they were defined
        # For now, just log the metrics
        logger.info(
            "Response formatting metrics: %s, %s, %.2fs",
            format_type,
            status,
            duration,
        )
        
        if not success and error_type:
            logger.error(f"Response formatting error: {error_type}")
        
        logger.debug(
            "Recorded response formatting metrics for request %s",
            request_id,
        )
        
    except Exception as e:
        logger.error(f"Failed to record response formatting metrics: {e}")


async def record_embedding_generation(
    request_id: str,
    model: str,
    text_length: int,
    duration: float,
    success: bool,
    error_type: Optional[str] = None,
) -> None:
    """Record embedding generation metrics"""
    try:
        status = "success" if success else "error"
        
        # This would use actual Prometheus metrics if they were defined
        # For now, just log the metrics
        logger.info(
            "Embedding generation metrics: %s, %s, %.2fs",
            model,
            status,
            duration,
        )
        
        if not success and error_type:
            logger.error(f"Embedding generation error: {error_type}")
        
        logger.debug(
            "Recorded embedding generation metrics for request %s",
            request_id,
        )
        
    except Exception as e:
        logger.error(f"Failed to record embedding generation metrics: {e}")


async def record_embedding_batch(
    request_id: str,
    model: str,
    batch_size: int,
    duration: float,
    success: bool,
    error_type: Optional[str] = None,
) -> None:
    """Record embedding batch processing metrics"""
    try:
        status = "success" if success else "error"
        
        # This would use actual Prometheus metrics if they were defined
        # For now, just log the metrics
        logger.info(
            "Embedding batch metrics: %s, %s items, %s, %.2fs",
            model,
            batch_size,
            status,
            duration,
        )
        
        if not success and error_type:
            logger.error(f"Embedding batch error: {error_type}")
        
        logger.debug(
            "Recorded embedding batch metrics for request %s",
            request_id,
        )
        
    except Exception as e:
        logger.error(f"Failed to record embedding batch metrics: {e}")


async def record_vector_search(
    request_id: str,
    vector_store: str,
    query_length: int,
    results_count: int,
    duration: float,
    success: bool,
    error_type: Optional[str] = None,
) -> None:
    """Record vector search metrics"""
    try:
        status = "success" if success else "error"
        
        # This would use actual Prometheus metrics if they were defined
        # For now, just log the metrics
        logger.info(
            "Vector search metrics: %s, %s results, %s, %.2fs",
            vector_store,
            results_count,
            status,
            duration,
        )
        
        if not success and error_type:
            logger.error(f"Vector search error: {error_type}")
        
        logger.debug(
            "Recorded vector search metrics for request %s",
            request_id,
        )
        
    except Exception as e:
        logger.error(f"Failed to record vector search metrics: {e}")


async def record_vector_insert(
    request_id: str,
    vector_store: str,
    documents_count: int,
    duration: float,
    success: bool,
    error_type: Optional[str] = None,
) -> None:
    """Record vector insert metrics"""
    try:
        status = "success" if success else "error"
        
        # This would use actual Prometheus metrics if they were defined
        # For now, just log the metrics
        logger.info(
            "Vector insert metrics: %s, %s docs, %s, %.2fs",
            vector_store,
            documents_count,
            status,
            duration,
        )
        
        if not success and error_type:
            logger.error(f"Vector insert error: {error_type}")
        
        logger.debug(
            "Recorded vector insert metrics for request %s",
            request_id,
        )
        
    except Exception as e:
        logger.error(f"Failed to record vector insert metrics: {e}")


async def record_document_processing(
    request_id: str,
    document_type: str,
    file_size: int,
    chunks_created: int,
    duration: float,
    success: bool,
    error_type: Optional[str] = None,
) -> None:
    """Record document processing metrics"""
    try:
        status = "success" if success else "error"
        
        # This would use actual Prometheus metrics if they were defined
        # For now, just log the metrics
        logger.info(
            "Document processing metrics: %s, %s chunks, %s, %.2fs",
            document_type,
            chunks_created,
            status,
            duration,
        )
        
        if not success and error_type:
            logger.error(f"Document processing error: {error_type}")
        
        logger.debug(
            "Recorded document processing metrics for request %s",
            request_id,
        )
        
    except Exception as e:
        logger.error(f"Failed to record document processing metrics: {e}")


async def record_rag_retrieval(
    request_id: str,
    query_length: int,
    documents_retrieved: int,
    duration: float,
    success: bool,
    error_type: Optional[str] = None,
) -> None:
    """Record RAG retrieval metrics"""
    try:
        status = "success" if success else "error"
        
        # This would use actual Prometheus metrics if they were defined
        # For now, just log the metrics
        logger.info(
            "RAG retrieval metrics: %s docs, %s, %.2fs",
            documents_retrieved,
            status,
            duration,
        )
        
        if not success and error_type:
            logger.error(f"RAG retrieval error: {error_type}")
        
        logger.debug(
            "Recorded RAG retrieval metrics for request %s",
            request_id,
        )
        
    except Exception as e:
        logger.error(f"Failed to record RAG retrieval metrics: {e}")


async def record_rag_indexing(
    request_id: str,
    documents_indexed: int,
    duration: float,
    success: bool,
    error_type: Optional[str] = None,
) -> None:
    """Record RAG indexing metrics"""
    try:
        status = "success" if success else "error"
        
        # This would use actual Prometheus metrics if they were defined
        # For now, just log the metrics
        logger.info(
            "RAG indexing metrics: %s docs, %s, %.2fs",
            documents_indexed,
            status,
            duration,
        )
        
        if not success and error_type:
            logger.error("RAG indexing error: %s", error_type)
        
        logger.debug(
            "Recorded RAG indexing metrics for request %s",
            request_id,
        )
        
    except Exception as e:
        logger.error("Failed to record RAG indexing metrics: %s", e)
