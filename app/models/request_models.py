"""
Request Models

Pydantic models for API request validation.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum

from app.services.medical.medical_analyzer import MedicalQueryType
from app.services.rag.retriever import RetrievalStrategy


class LanguageCode(str, Enum):
    """Supported language codes."""
    ENGLISH = "en"
    YORUBA = "yo"


class OutputFormat(str, Enum):
    """Supported output formats."""
    JSON = "json"
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"


class MedicalQueryRequest(BaseModel):
    """Medical query request model."""
    query: str = Field(..., min_length=1, max_length=2000, description="Medical query text")
    language: LanguageCode = Field(default=LanguageCode.ENGLISH, description="Query language")
    query_type: Optional[MedicalQueryType] = Field(default=None, description="Type of medical query")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    user_age: Optional[int] = Field(default=None, ge=0, le=120, description="User age")
    user_gender: Optional[str] = Field(default=None, description="User gender")
    existing_conditions: Optional[List[str]] = Field(default=None, description="Existing medical conditions")
    medications: Optional[List[str]] = Field(default=None, description="Current medications")
    symptoms_duration: Optional[str] = Field(default=None, description="Duration of symptoms")
    severity_level: Optional[str] = Field(default=None, description="Symptom severity level")
    output_format: OutputFormat = Field(default=OutputFormat.JSON, description="Response format")
    include_sources: bool = Field(default=True, description="Include source references")
    include_disclaimers: bool = Field(default=True, description="Include medical disclaimers")
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()
    
    @field_validator('user_age')
    @classmethod
    def validate_age(cls, v):
        if v is not None and (v < 0 or v > 120):
            raise ValueError("Age must be between 0 and 120")
        return v


class TranslationRequest(BaseModel):
    """Translation request model."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to translate")
    source_language: LanguageCode = Field(default=LanguageCode.ENGLISH, description="Source language")
    target_language: LanguageCode = Field(default=LanguageCode.YORUBA, description="Target language")
    context: Optional[str] = Field(default=None, description="Translation context")
    preserve_formatting: bool = Field(default=True, description="Preserve text formatting")
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()
    
    @field_validator('target_language')
    @classmethod
    def validate_languages(cls, v, info):
        if info.data and 'source_language' in info.data and v == info.data['source_language']:
            raise ValueError("Source and target languages must be different")
        return v


class BatchQueryRequest(BaseModel):
    """Batch medical query request model."""
    queries: List[MedicalQueryRequest] = Field(..., min_items=1, max_items=10, description="List of medical queries")
    batch_id: Optional[str] = Field(default=None, description="Batch identifier")
    
    @field_validator('queries')
    @classmethod
    def validate_queries(cls, v):
        if len(v) == 0:
            raise ValueError("At least one query is required")
        if len(v) > 10:
            raise ValueError("Maximum 10 queries allowed per batch")
        return v


class RAGQueryRequest(BaseModel):
    """RAG query request model."""
    query: str = Field(..., min_length=1, max_length=2000, description="Search query")
    collection_name: str = Field(default="medical_docs", description="Document collection name")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of documents to retrieve")
    similarity_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Similarity threshold")
    strategy: RetrievalStrategy = Field(default=RetrievalStrategy.SEMANTIC, description="Retrieval strategy")
    filter_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadata filters")
    rerank_results: bool = Field(default=False, description="Apply result reranking")
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class DocumentIndexRequest(BaseModel):
    """Document indexing request model."""
    documents: List[Dict[str, Any]] = Field(..., min_items=1, description="Documents to index")
    collection_name: str = Field(default="medical_docs", description="Target collection")
    chunk_size: int = Field(default=1000, ge=100, le=5000, description="Document chunk size")
    chunk_overlap: int = Field(default=200, ge=0, le=1000, description="Chunk overlap size")
    embedding_model: Optional[str] = Field(default=None, description="Embedding model to use")
    
    @field_validator('documents')
    @classmethod
    def validate_documents(cls, v):
        for doc in v:
            if 'content' not in doc or not doc['content']:
                raise ValueError("Each document must have content")
        return v


class HealthCheckRequest(BaseModel):
    """Health check request model."""
    detailed: bool = Field(default=False, description="Include detailed health information")
    include_metrics: bool = Field(default=True, description="Include performance metrics")
    check_external_services: bool = Field(default=False, description="Check external service health")


class UserRegistrationRequest(BaseModel):
    """User registration request model."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password")
    full_name: Optional[str] = Field(default=None, description="Full name")
    preferred_language: LanguageCode = Field(default=LanguageCode.ENGLISH, description="Preferred language")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError("Invalid email format")
        return v.lower()
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("Username can only contain letters, numbers, and underscores")
        return v.lower()


class UserLoginRequest(BaseModel):
    """User login request model."""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")
    remember_me: bool = Field(default=False, description="Remember login session")


class PasswordResetRequest(BaseModel):
    """Password reset request model."""
    email: str = Field(..., description="Email address")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError("Invalid email format")
        return v.lower()


class PasswordChangeRequest(BaseModel):
    """Password change request model."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Confirm new password")
    
    @field_validator('confirm_password')
    @classmethod
    def validate_confirm_password(cls, v, info):
        if info.data and 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError("Passwords do not match")
        return v


class ProfileUpdateRequest(BaseModel):
    """User profile update request model."""
    full_name: Optional[str] = Field(default=None, description="Full name")
    email: Optional[str] = Field(default=None, description="Email address")
    preferred_language: Optional[LanguageCode] = Field(default=None, description="Preferred language")
    timezone: Optional[str] = Field(default=None, description="Timezone")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is not None:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                raise ValueError("Invalid email format")
            return v.lower()
        return v 