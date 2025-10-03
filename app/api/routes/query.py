"""
Main medical query endpoints for HealthLang AI MVP
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, Field, field_validator
from prometheus_client import Counter, Histogram, Gauge

from app.config import settings
from app.core.workflow import HealthLangWorkflow

from app.utils.logger import get_logger
from app.utils.metrics import record_query_metrics

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
    
    text: str = Field(
        ..., 
        min_length=1, 
        max_length=5000, 
        description="Medical question text"
    )
    use_cache: bool = Field(
        default=True, 
        description="Whether to use response caching"
    )
    include_sources: bool = Field(
        default=True, 
        description="Whether to include source documents"
    )
    
    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()


class MedicalQueryResponse(BaseModel):
    """Response model for medical queries"""
    
    request_id: str
    original_query: str
    response: str
    processing_time: float
    timestamp: str
    metadata: Dict[str, Any]
    success: bool
    error: Optional[str] = None


# Global workflow instance
workflow: Optional[HealthLangWorkflow] = None


async def get_workflow() -> HealthLangWorkflow:
    """Dependency to get the global workflow instance"""
    global workflow
    if workflow is None:
        workflow = HealthLangWorkflow()
    return workflow


@router.post("/query", response_model=MedicalQueryResponse)
async def process_medical_query(
    request: MedicalQueryRequest,
    http_request: Request,
    workflow: HealthLangWorkflow = Depends(get_workflow),
) -> MedicalQueryResponse:
    """
    Process a medical query (English-only chat flow).

    This endpoint now accepts and responds in English only. The chatbot does not
    auto-translate. Translation endpoints remain available under /api/v1/translate/*
    for future TTS/STT features but are not used by the chat flow.
    
    Args:
        request: The medical query request
        http_request: The HTTP request object
        workflow: The LangGraph workflow
        
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
    query_length.labels(source_language="en").observe(len(request.text))
    active_queries.inc()
    
    try:
        logger.info(f"Processing medical query (ID: {request_id}): {request.text[:100]}...")

        # Use workflow to process query (which now uses MCP HTTP client)
        result = await workflow.process_query(request.text)

        query_counter.labels(
            source_language="en",
            target_language="en",
            status="success" if result["success"] else "error"
        ).inc()

        response = MedicalQueryResponse(
            request_id=request_id,
            original_query=request.text,
            response=result["response"],
            processing_time=(datetime.now() - start_time).total_seconds(),
            timestamp=datetime.now().isoformat(),
            metadata=result["metadata"],
            success=result["success"],
            error=result.get("error")
        )

        logger.info(f"Query processed (ID: {request_id}) - Success: {result['success']}")

        from fastapi.responses import JSONResponse
        return JSONResponse(
            content=response.model_dump(),
            headers={"Content-Type": "application/json; charset=utf-8"}
        )

    except Exception as e:
        query_counter.labels(
            source_language="en",
            target_language="en",
            status="error"
        ).inc()
        # Log with traceback in a loguru-friendly way
        logger.exception(
            f"Error processing query (ID: {request_id}): {e}"
        )
        # Return a structured error payload instead of raising to
        # avoid middleware rethrow noise and ensure consistent JSON.
        err_response = MedicalQueryResponse(
            request_id=request_id,
            original_query=request.text,
            response=(
                "Sorry, I hit a snag while processing your question. "
                "Please try again shortly."
            ),
            processing_time=(datetime.now() - start_time).total_seconds(),
            timestamp=datetime.now().isoformat(),
            metadata={
                "original_language": "en",
                "translation_used": False,
            },
            success=False,
            error=str(e),
        )
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content=err_response.model_dump(),
            headers={"Content-Type": "application/json; charset=utf-8"},
            status_code=200,
        )
    finally:
        duration = (datetime.now() - start_time).total_seconds()
        query_duration.labels(
            source_language="en",
            target_language="en"
        ).observe(duration)
        active_queries.dec()
        # Use the success flag from the constructed response if available
        try:
            success_flag = False
            if 'response' in locals() and hasattr(response, 'success'):
                success_flag = bool(response.success)
        except Exception:
            success_flag = False
        await record_query_metrics(
            request_id=request_id,
            source_language="en",
            target_language="en",
            duration=duration,
            success=bool(success_flag),
        )


@router.get("/query/{request_id}")
async def get_query_status(
    request_id: str,
) -> Dict[str, Any]:
    """
    Get the status of a previously submitted query
    
    Args:
        request_id: The request ID to check
        
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
    workflow: HealthLangWorkflow = Depends(get_workflow),
) -> Dict[str, Any]:
    """
    Process multiple medical queries in batch
    
    Args:
        requests: List of medical query requests
        http_request: The HTTP request object
        workflow: The LangGraph workflow
        
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
            result = await workflow.process_query(request.text)
            results.append({
                "request_id": request_id,
                "original_query": request.text,
                "response": result["response"],
                "success": result["success"],
                "error": result.get("error"),
                "metadata": result["metadata"]
            })
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
        "supported_languages": ["en"],
        "language_names": {
            "en": "English"
        },
        "auto_detection": False,
        "translation_workflow": "disabled in chat; translate endpoints reserved for future voice features"
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
        "languages_processed": ["en", "yo"],
        "workflow_type": "LangGraph",
        "timestamp": datetime.now().isoformat(),
    } 