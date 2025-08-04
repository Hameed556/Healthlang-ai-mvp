"""
Custom exceptions for HealthLang AI MVP
"""

from typing import Optional, Dict, Any


class HealthLangException(Exception):
    """Base exception for HealthLang AI MVP"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class TranslationError(HealthLangException):
    """Exception raised for translation-related errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="TRANSLATION_ERROR",
            status_code=422,
            details=details,
        )


class LanguageNotSupportedError(TranslationError):
    """Exception raised when a language is not supported"""
    
    def __init__(self, language: str):
        super().__init__(
            message=f"Language '{language}' is not supported",
            details={"supported_languages": ["en", "yo"]},
        )


class MedicalAnalysisError(HealthLangException):
    """Exception raised for medical analysis errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="MEDICAL_ANALYSIS_ERROR",
            status_code=500,
            details=details,
        )


class SafetyCheckError(HealthLangException):
    """Exception raised for safety check failures"""
    
    def __init__(self, message: str, check_type: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="SAFETY_CHECK_ERROR",
            status_code=400,
            details={"check_type": check_type, **(details or {})},
        )


class FormattingError(HealthLangException):
    """Exception raised for response formatting errors"""
    
    def __init__(self, message: str, format_type: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="FORMATTING_ERROR",
            status_code=500,
            details={"format_type": format_type, **(details or {})},
        )


class LLMServiceError(MedicalAnalysisError):
    """Exception raised for LLM service errors"""
    
    def __init__(self, message: str, provider: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            details={"provider": provider, **(details or {})},
        )


class RAGError(HealthLangException):
    """Exception raised for RAG-related errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="RAG_ERROR",
            status_code=500,
            details=details,
        )


class VectorStoreError(RAGError):
    """Exception raised for vector store errors"""
    
    def __init__(self, message: str, store_type: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            details={"store_type": store_type, **(details or {})},
        )


class RetrievalError(RAGError):
    """Exception raised for retrieval errors"""
    
    def __init__(self, message: str, query: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            details={"query": query, **(details or {})},
        )


class EmbeddingError(RAGError):
    """Exception raised for embedding generation errors"""
    
    def __init__(self, message: str, model: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            details={"model": model, **(details or {})},
        )


class ConfigurationError(HealthLangException):
    """Exception raised for configuration errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=500,
            details=details,
        )


class ValidationError(HealthLangException):
    """Exception raised for validation errors"""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details={"field": field, **(details or {})},
        )


class RateLimitError(HealthLangException):
    """Exception raised for rate limiting errors"""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            status_code=429,
            details={"retry_after": retry_after},
        )


class AuthenticationError(HealthLangException):
    """Exception raised for authentication errors"""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,
        )


class AuthorizationError(HealthLangException):
    """Exception raised for authorization errors"""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403,
        )


class ResourceNotFoundError(HealthLangException):
    """Exception raised when a resource is not found"""
    
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} with id '{resource_id}' not found",
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class ServiceUnavailableError(HealthLangException):
    """Exception raised when a service is unavailable"""
    
    def __init__(self, service_name: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Service '{service_name}' is currently unavailable",
            error_code="SERVICE_UNAVAILABLE",
            status_code=503,
            details={"service_name": service_name},
        )


class DataProcessingError(HealthLangException):
    """Exception raised for data processing errors"""
    
    def __init__(self, message: str, data_type: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DATA_PROCESSING_ERROR",
            status_code=422,
            details={"data_type": data_type, **(details or {})},
        )


class DocumentProcessingError(HealthLangException):
    """Exception raised for document processing errors"""
    
    def __init__(self, message: str, document_type: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DOCUMENT_PROCESSING_ERROR",
            status_code=422,
            details={"document_type": document_type, **(details or {})},
        )


class CacheError(HealthLangException):
    """Exception raised for cache-related errors"""
    
    def __init__(self, message: str, cache_type: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            status_code=500,
            details={"cache_type": cache_type, **(details or {})},
        )


# Error code mappings for easy lookup
ERROR_CODES = {
    "TRANSLATION_ERROR": TranslationError,
    "LANGUAGE_NOT_SUPPORTED": LanguageNotSupportedError,
    "MEDICAL_ANALYSIS_ERROR": MedicalAnalysisError,
    "SAFETY_CHECK_ERROR": SafetyCheckError,
    "FORMATTING_ERROR": FormattingError,
    "LLM_SERVICE_ERROR": LLMServiceError,
    "RAG_ERROR": RAGError,
    "VECTOR_STORE_ERROR": VectorStoreError,
    "RETRIEVAL_ERROR": RetrievalError,
    "EMBEDDING_ERROR": EmbeddingError,
    "CONFIGURATION_ERROR": ConfigurationError,
    "VALIDATION_ERROR": ValidationError,
    "RATE_LIMIT_ERROR": RateLimitError,
    "AUTHENTICATION_ERROR": AuthenticationError,
    "AUTHORIZATION_ERROR": AuthorizationError,
    "RESOURCE_NOT_FOUND": ResourceNotFoundError,
    "SERVICE_UNAVAILABLE": ServiceUnavailableError,
    "DATA_PROCESSING_ERROR": DataProcessingError,
    "DOCUMENT_PROCESSING_ERROR": DocumentProcessingError,
    "CACHE_ERROR": CacheError,
} 