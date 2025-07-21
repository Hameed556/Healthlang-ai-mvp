"""
Response Models

Pydantic models for API response validation.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from app.services.medical.medical_analyzer import SafetyLevel


class ResponseStatus(str, Enum):
    """Response status codes."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class HealthStatus(str, Enum):
    """Health status values."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class MedicalQueryResponse(BaseModel):
    """Medical query response model."""
    query: str = Field(..., description="Original query")
    analysis: str = Field(..., description="Medical analysis")
    recommendations: List[str] = Field(default_factory=list, description="Medical recommendations")
    safety_level: SafetyLevel = Field(..., description="Safety assessment level")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Analysis confidence")
    query_type: str = Field(..., description="Type of medical query")
    disclaimers: List[str] = Field(default_factory=list, description="Medical disclaimers")
    follow_up_questions: List[str] = Field(default_factory=list, description="Follow-up questions")
    emergency_indicators: List[str] = Field(default_factory=list, description="Emergency indicators")
    sources: List[str] = Field(default_factory=list, description="Source references")
    language: str = Field(..., description="Response language")
    processing_time: float = Field(..., description="Processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[str] = Field(default=None, description="Request identifier")


class TranslationResponse(BaseModel):
    """Translation response model."""
    original_text: str = Field(..., description="Original text")
    translated_text: str = Field(..., description="Translated text")
    source_language: str = Field(..., description="Source language")
    target_language: str = Field(..., description="Target language")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Translation confidence")
    processing_time: float = Field(..., description="Processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[str] = Field(default=None, description="Request identifier")


class BatchQueryResponse(BaseModel):
    """Batch query response model."""
    batch_id: str = Field(..., description="Batch identifier")
    total_queries: int = Field(..., description="Total number of queries")
    successful_queries: int = Field(..., description="Number of successful queries")
    failed_queries: int = Field(..., description="Number of failed queries")
    results: List[MedicalQueryResponse] = Field(..., description="Query results")
    processing_time: float = Field(..., description="Total processing time")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class RAGQueryResponse(BaseModel):
    """RAG query response model."""
    query: str = Field(..., description="Original query")
    documents: List[Dict[str, Any]] = Field(..., description="Retrieved documents")
    total_results: int = Field(..., description="Total number of results")
    retrieval_time: float = Field(..., description="Retrieval time in seconds")
    strategy: str = Field(..., description="Retrieval strategy used")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: HealthStatus = Field(..., description="Overall health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    version: str = Field(..., description="Application version")
    uptime: float = Field(..., description="Application uptime in seconds")
    services: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Service health status")
    metrics: Optional[Dict[str, Any]] = Field(default=None, description="Performance metrics")
    errors: List[str] = Field(default_factory=list, description="Health check errors")


class ErrorResponse(BaseModel):
    """Error response model."""
    status: ResponseStatus = Field(default=ResponseStatus.ERROR, description="Response status")
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(default=None, description="Request identifier")


class SuccessResponse(BaseModel):
    """Success response model."""
    status: ResponseStatus = Field(default=ResponseStatus.SUCCESS, description="Response status")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[str] = Field(default=None, description="Request identifier")


class UserResponse(BaseModel):
    """User response model."""
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: Optional[str] = Field(default=None, description="Full name")
    preferred_language: str = Field(..., description="Preferred language")
    is_active: bool = Field(..., description="Account active status")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class AuthenticationResponse(BaseModel):
    """Authentication response model."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    refresh_token: Optional[str] = Field(default=None, description="Refresh token")
    user: UserResponse = Field(..., description="User information")


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class StatisticsResponse(BaseModel):
    """Statistics response model."""
    total_queries: int = Field(..., description="Total number of queries")
    total_translations: int = Field(..., description="Total number of translations")
    total_users: int = Field(..., description="Total number of users")
    average_response_time: float = Field(..., description="Average response time")
    success_rate: float = Field(..., description="Success rate percentage")
    top_languages: List[Dict[str, Any]] = Field(..., description="Top used languages")
    top_query_types: List[Dict[str, Any]] = Field(..., description="Top query types")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Statistics timestamp")


class CollectionStatsResponse(BaseModel):
    """Collection statistics response model."""
    collection_name: str = Field(..., description="Collection name")
    document_count: int = Field(..., description="Number of documents")
    embedding_model: str = Field(..., description="Embedding model used")
    vector_store_type: str = Field(..., description="Vector store type")
    last_updated: datetime = Field(..., description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ServiceHealthResponse(BaseModel):
    """Service health response model."""
    service_name: str = Field(..., description="Service name")
    status: HealthStatus = Field(..., description="Service health status")
    response_time: float = Field(..., description="Service response time")
    error_count: int = Field(..., description="Number of errors")
    last_check: datetime = Field(..., description="Last health check timestamp")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Service details")


class APIInfoResponse(BaseModel):
    """API information response model."""
    name: str = Field(..., description="API name")
    version: str = Field(..., description="API version")
    description: str = Field(..., description="API description")
    endpoints: List[Dict[str, Any]] = Field(..., description="Available endpoints")
    supported_languages: List[str] = Field(..., description="Supported languages")
    supported_formats: List[str] = Field(..., description="Supported output formats")
    rate_limits: Dict[str, Any] = Field(..., description="Rate limiting information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp") 