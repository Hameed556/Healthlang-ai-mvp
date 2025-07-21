"""
Main medical query endpoints for HealthLang AI MVP
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, Field, validator
from prometheus_client import Counter, Histogram, Gauge

from app.config import settings
from app.core.pipeline import MedicalQueryPipeline
from app.core.exceptions import HealthLangException, ValidationError
from app.utils.logger import get_logger
from app.utils.metrics import record_query_metrics
from app.utils.validators import validate_language_code

logger = get_logger(__name__)

router = APIRouter()

# Metrics
query_counter = Counter(
    "healthlang_queries_total",
    "Total number of medical queries",
    ["source_language", "target_language", "status"]
)

query_duration = Histogram(
    "healthlang_query_duration_seconds",
    "Query processing duration in seconds",
    ["source_language", "target_language"]
)

query_length = Histogram(
    "healthlang_query_length_chars",
    "Query text length in characters",
    ["source_language"]
)

active_queries = Gauge(
    "healthlang_active_queries",
    "Number of currently active queries"
)


class MedicalQueryRequest(BaseModel):
    """Request model for medical queries"""
    
    text: str = Field(..., min_length=1, max_length=5000, description="Medical question text")
    source_language: str = Field(default="en", description="Source language code (en, yo)")
    target_language: Optional[str] = Field(default=None, description="Target language code (en, yo) - if None, matches source_language")
    translate_response: bool = Field(default=False, description="Whether to translate the response (optional)")
    use_cache: bool = Field(default=True, description="Whether to use response caching")
    include_sources: bool = Field(default=True, description="Whether to include source documents")
    max_tokens: Optional[int] = Field(default=None, ge=1, le=8192, description="Maximum tokens for response")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="Response creativity (0.0-2.0)")
    
    @validator("text")
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()
    
    @validator("source_language")
    def validate_source_language(cls, v):
        if not validate_language_code(v):
            raise ValueError(f"Unsupported language code: {v}")
        return v.lower()
    
    @validator("target_language")
    def validate_target_language(cls, v):
        if v is not None and not validate_language_code(v):
            raise ValueError(f"Unsupported language code: {v}")
        return v.lower() if v is not None else v
    
    @validator("max_tokens")
    def validate_max_tokens(cls, v):
        if v is not None and v > settings.MAX_TOKENS:
            raise ValueError(f"max_tokens cannot exceed {settings.MAX_TOKENS}")
        return v


class MedicalQueryResponse(BaseModel):
    """Response model for medical queries"""
    
    request_id: str
    original_query: str
    source_language: str
    target_language: str
    translated_query: Optional[str]
    response: str
    processing_time: float
    timestamp: str
    metadata: Dict[str, Any]
    sources: Optional[list] = None


# Global pipeline instance
pipeline: Optional[MedicalQueryPipeline] = None


async def get_pipeline() -> MedicalQueryPipeline:
    """Dependency to get the global pipeline instance"""
    global pipeline
    if pipeline is None:
        pipeline = MedicalQueryPipeline()
        await pipeline.initialize()
    return pipeline


@router.post("/query", response_model=MedicalQueryResponse)
async def process_medical_query(
    request: MedicalQueryRequest,
    http_request: Request,
    pipeline: MedicalQueryPipeline = Depends(get_pipeline),
) -> MedicalQueryResponse:
    """
    Process a medical query with translation and RAG
    
    This endpoint accepts medical questions in Yoruba or English and returns
    medically-informed answers with source citations.
    
    Args:
        request: The medical query request
        http_request: The HTTP request object
        pipeline: The medical query pipeline
        
    Returns:
        Medical query response with answer and metadata
        
    Raises:
        HTTPException: If processing fails
    """
    request_id = str(uuid.uuid4())
    start_time = datetime.now()
    
    # Set request ID in request state for logging
    http_request.state.request_id = request_id
    
    # Record query metrics
    query_length.labels(source_language=request.source_language).observe(len(request.text))
    active_queries.inc()
    
    try:
        logger.info(f"Processing medical query (ID: {request_id}): {request.text[:100]}...")
        
        # Process the query through the pipeline
        result = await pipeline.process_query(
            text=request.text,
            source_language=request.source_language,
            target_language=request.target_language,
            request_id=request_id,
            use_cache=request.use_cache,
            translate_response=request.translate_response,
        )
        
        # Record success metrics
        query_counter.labels(
            source_language=request.source_language,
            target_language=request.target_language,
            status="success"
        ).inc()
        
        # Build response
        response = MedicalQueryResponse(
            request_id=result["request_id"],
            original_query=result["original_query"],
            source_language=result["source_language"],
            target_language=result["target_language"],
            translated_query=result["translated_query"],
            response=result["response"],
            processing_time=result["processing_time"],
            timestamp=result["timestamp"],
            metadata=result["metadata"],
            sources=result["sources"] if request.include_sources else None,
        )
        
        logger.info(f"Query processed successfully (ID: {request_id})")
        return response
        
    except HealthLangException as e:
        # Record error metrics
        query_counter.labels(
            source_language=request.source_language,
            target_language=request.target_language,
            status="error"
        ).inc()
        
        logger.error(f"HealthLang error processing query (ID: {request_id}): {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": e.message,
                "error_code": e.error_code,
                "request_id": request_id,
                "details": e.details,
            }
        )
        
    except Exception as e:
        # Record error metrics
        query_counter.labels(
            source_language=request.source_language,
            target_language=request.target_language,
            status="error"
        ).inc()
        
        logger.error(f"Unexpected error processing query (ID: {request_id}): {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "error_code": "INTERNAL_ERROR",
                "request_id": request_id,
            }
        )
        
    finally:
        # Record duration metrics
        duration = (datetime.now() - start_time).total_seconds()
        query_duration.labels(
            source_language=request.source_language,
            target_language=request.target_language
        ).observe(duration)
        
        active_queries.dec()
        
        # Record additional metrics
        await record_query_metrics(
            request_id=request_id,
            source_language=request.source_language,
            target_language=request.target_language,
            duration=duration,
            success=True,  # Will be False if exception was raised
        )


@router.get("/query/{request_id}")
async def get_query_status(
    request_id: str,
    pipeline: MedicalQueryPipeline = Depends(get_pipeline),
) -> Dict[str, Any]:
    """
    Get the status of a previously submitted query
    
    Args:
        request_id: The request ID to check
        pipeline: The medical query pipeline
        
    Returns:
        Query status information
    """
    try:
        # For now, we'll return a simple status
        # In a real implementation, you might store query status in a database
        return {
            "request_id": request_id,
            "status": "completed",  # This would be dynamic in a real implementation
            "timestamp": datetime.now().isoformat(),
            "message": "Query status retrieval not fully implemented in MVP",
        }
    except Exception as e:
        logger.error(f"Error getting query status for {request_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get query status",
                "request_id": request_id,
            }
        )


@router.post("/query/batch")
async def process_batch_queries(
    requests: list[MedicalQueryRequest],
    http_request: Request,
    pipeline: MedicalQueryPipeline = Depends(get_pipeline),
) -> Dict[str, Any]:
    """
    Process multiple medical queries in batch
    
    Args:
        requests: List of medical query requests
        http_request: The HTTP request object
        pipeline: The medical query pipeline
        
    Returns:
        Batch processing results
    """
    if len(requests) > 10:  # Limit batch size
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Batch size too large",
                "max_batch_size": 10,
                "received": len(requests),
            }
        )
    
    batch_id = str(uuid.uuid4())
    http_request.state.request_id = batch_id
    
    logger.info(f"Processing batch of {len(requests)} queries (ID: {batch_id})")
    
    results = []
    errors = []
    
    for i, request in enumerate(requests):
        request_id = f"{batch_id}-{i+1}"
        try:
            result = await pipeline.process_query(
                text=request.text,
                source_language=request.source_language,
                target_language=request.target_language,
                request_id=request_id,
                use_cache=request.use_cache,
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Error processing batch item {i+1} (ID: {request_id}): {e}")
            errors.append({
                "index": i,
                "request_id": request_id,
                "error": str(e),
            })
    
    return {
        "batch_id": batch_id,
        "total_requests": len(requests),
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/supported-languages")
async def get_supported_languages() -> Dict[str, Any]:
    """
    Get list of supported languages
    
    Returns:
        Supported language information
    """
    return {
        "supported_languages": settings.SUPPORTED_LANGUAGES,
        "default_source": settings.DEFAULT_SOURCE_LANGUAGE,
        "default_target": settings.DEFAULT_TARGET_LANGUAGE,
        "language_names": {
            "en": "English",
            "yo": "Yoruba",
        },
    }


@router.get("/query-stats")
async def get_query_statistics() -> Dict[str, Any]:
    """
    Get query processing statistics
    
    Returns:
        Query processing statistics
    """
    # This would typically query a database for real statistics
    # For MVP, we'll return basic metrics
    return {
        "total_queries": 0,  # Would be from database
        "successful_queries": 0,
        "failed_queries": 0,
        "average_processing_time": 0.0,
        "languages_processed": settings.SUPPORTED_LANGUAGES,
        "timestamp": datetime.now().isoformat(),
    } 