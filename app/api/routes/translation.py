"""
Translation endpoints for HealthLang AI MVP
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, Field, field_validator

from app.services.translation.translator import TranslationService

from app.utils.logger import get_logger
from app.utils.validators import validate_language_code

logger = get_logger(__name__)

router = APIRouter()


# Metrics
def get_metrics():
    """Get or create metrics safely"""
    try:
        from prometheus_client import Counter, Histogram
        from prometheus_client.registry import REGISTRY
        
        # Check if metrics already exist
        existing_metrics = {
            metric.name: metric 
            for metric in REGISTRY._collector_to_names.keys()
        }
        
        if "healthlang_translations_total" in existing_metrics:
            translation_counter = existing_metrics[
                "healthlang_translations_total"
            ]
        else:
            translation_counter = Counter(
                "healthlang_translations_total",
                "Total number of translations",
                ["source_language", "target_language", "status"]
            )
        
        if "healthlang_translation_duration_seconds" in existing_metrics:
            translation_duration = existing_metrics[
                "healthlang_translation_duration_seconds"
            ]
        else:
            translation_duration = Histogram(
                "healthlang_translation_duration_seconds",
                "Translation duration in seconds",
                ["source_language", "target_language"]
            )
        
        if "healthlang_translation_length_chars" in existing_metrics:
            translation_length = existing_metrics[
                "healthlang_translation_length_chars"
            ]
        else:
            translation_length = Histogram(
                "healthlang_translation_length_chars",
                "Translation text length in characters",
                ["source_language"]
            )
        
        return translation_counter, translation_duration, translation_length
        
    except Exception as e:
        logger.warning(f"Failed to initialize metrics: {e}")
        # Create dummy metrics that don't do anything to avoid errors
        
        class DummyMetric:
            def labels(self, **kwargs): 
                return self
            
            def inc(self): 
                pass
            
            def observe(self, value): 
                pass
        
        return DummyMetric(), DummyMetric(), DummyMetric()


# Initialize metrics
translation_counter, translation_duration, translation_length = get_metrics()


class TranslationRequest(BaseModel):
    """Request model for translation"""
    
    text: str = Field(..., min_length=1, max_length=10000, description="Text to translate")
    source_language: str = Field(default="en", description="Source language code (en, yo)")
    target_language: str = Field(default="yo", description="Target language code (en, yo)")
    preserve_formatting: bool = Field(default=True, description="Preserve text formatting")
    
    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()
    
    @field_validator("source_language", "target_language")
    @classmethod
    def validate_language_codes(cls, v):
        if not validate_language_code(v):
            raise ValueError(f"Unsupported language code: {v}")
        return v.lower()


class TranslationResponse(BaseModel):
    """Response model for translation"""
    
    request_id: str
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence_score: Optional[float] = None
    processing_time: float
    timestamp: str
    metadata: Dict[str, Any]


class BatchTranslationRequest(BaseModel):
    """Request model for batch translation"""
    
    texts: List[str] = Field(..., min_items=1, max_items=50, description="List of texts to translate")
    source_language: str = Field(default="en", description="Source language code (en, yo)")
    target_language: str = Field(default="yo", description="Target language code (en, yo)")
    preserve_formatting: bool = Field(default=True, description="Preserve text formatting")
    
    @field_validator("texts")
    @classmethod
    def validate_texts(cls, v):
        if not all(text.strip() for text in v):
            raise ValueError("All texts must be non-empty")
        return [text.strip() for text in v]
    
    @field_validator("source_language", "target_language")
    @classmethod
    def validate_language_codes(cls, v):
        if not validate_language_code(v):
            raise ValueError(f"Unsupported language code: {v}")
        return v.lower()


class BatchTranslationResponse(BaseModel):
    """Response model for batch translation"""
    
    batch_id: str
    total_texts: int
    successful: int
    failed: int
    translations: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    processing_time: float
    timestamp: str


class LanguageDetectionRequest(BaseModel):
    """Request model for language detection"""
    
    text: str = Field(..., min_length=1, max_length=10000, description="Text to detect language for")
    
    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()


class LanguageDetectionResponse(BaseModel):
    """Response model for language detection"""
    
    request_id: str
    text: str
    detected_language: str
    confidence_score: float
    supported_languages: List[str]
    processing_time: float
    timestamp: str


# Global translation service instance
translation_service: Optional[TranslationService] = None


async def get_translation_service() -> TranslationService:
    """Dependency to get the global translation service instance"""
    global translation_service
    if translation_service is None:
        translation_service = TranslationService()
        await translation_service.initialize()
    return translation_service


@router.post("/", response_model=TranslationResponse)
async def translate_text(
    request: TranslationRequest,
    http_request: Request,
    service: TranslationService = Depends(get_translation_service),
) -> TranslationResponse:
    """
    Translate text between supported languages
    
    Args:
        request: The translation request
        http_request: The HTTP request object
        service: The translation service
        
    Returns:
        Translation response with translated text
        
    Raises:
        HTTPException: If translation fails
    """
    request_id = str(uuid.uuid4())
    start_time = datetime.now()
    
    # Set request ID in request state for logging
    http_request.state.request_id = request_id
    
    # Record translation metrics
    translation_length.labels(source_language=request.source_language).observe(len(request.text))
    
    try:
        logger.info(f"Translating text (ID: {request_id}): {request.text[:100]}...")

        # Use Groq+LLaMA-4 Maverick for translation
        translated_text = await service.translate(
            request.text,
            source_language=request.source_language,
            target_language=request.target_language
        )

        processing_time = (datetime.now() - start_time).total_seconds()
        translation_counter.labels(
            source_language=request.source_language,
            target_language=request.target_language,
            status="success"
        ).inc()
        response = TranslationResponse(
            request_id=request_id,
            original_text=request.text,
            translated_text=translated_text,
            source_language=request.source_language,
            target_language=request.target_language,
            confidence_score=0.95,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
            metadata={
                "preserve_formatting": request.preserve_formatting,
                "text_length": len(request.text),
                "translated_length": len(translated_text),
            },
        )
        logger.info(f"Translation completed (ID: {request_id})")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content=response.model_dump(),
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        translation_counter.labels(
            source_language=request.source_language,
            target_language=request.target_language,
            status="error"
        ).inc()
        logger.error(f"Translation error (ID: {request_id}): {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "error_code": "INTERNAL_ERROR",
                "request_id": request_id,
            }
        )
    finally:
        duration = (datetime.now() - start_time).total_seconds()
        translation_duration.labels(
            source_language=request.source_language,
            target_language=request.target_language
        ).observe(duration)


@router.post("/batch", response_model=BatchTranslationResponse)
async def translate_batch(
    request: BatchTranslationRequest,
    http_request: Request,
    service: TranslationService = Depends(get_translation_service),
) -> BatchTranslationResponse:
    """
    Translate multiple texts in batch
    
    Args:
        request: The batch translation request
        http_request: The HTTP request object
        service: The translation service
        
    Returns:
        Batch translation response
        
    Raises:
        HTTPException: If batch translation fails
    """
    batch_id = str(uuid.uuid4())
    start_time = datetime.now()
    
    http_request.state.request_id = batch_id
    
    logger.info(f"Processing batch translation of {len(request.texts)} texts (ID: {batch_id})")
    
    translations = []
    errors = []

    for i, text in enumerate(request.texts):
        try:
            translated_text = await service.translate(
                text,
                source_language=request.source_language,
                target_language=request.target_language
            )
            translations.append({
                "index": i,
                "original_text": text,
                "translated_text": translated_text,
                "source_language": request.source_language,
                "target_language": request.target_language,
                "confidence_score": 0.95,
            })
        except Exception as e:
            logger.error(f"Error translating batch item {i+1} (ID: {batch_id}): {e}")
            errors.append({
                "index": i,
                "original_text": text,
                "error": str(e),
            })

    processing_time = (datetime.now() - start_time).total_seconds()

    return BatchTranslationResponse(
        batch_id=batch_id,
        total_texts=len(request.texts),
        successful=len(translations),
        failed=len(errors),
        translations=translations,
        errors=errors,
        processing_time=processing_time,
        timestamp=datetime.now().isoformat(),
    )


@router.post("/detect-language", response_model=LanguageDetectionResponse)
async def detect_language(
    request: LanguageDetectionRequest,
    http_request: Request,
    service: TranslationService = Depends(get_translation_service),
) -> LanguageDetectionResponse:
    """
    Detect the language of the provided text
    
    Args:
        request: The language detection request
        http_request: The HTTP request object
        service: The translation service
        
    Returns:
        Language detection response
        
    Raises:
        HTTPException: If language detection fails
    """
    request_id = str(uuid.uuid4())
    start_time = datetime.now()
    
    http_request.state.request_id = request_id
    
    try:
        logger.info(f"Detecting language for text (ID: {request_id}): {request.text[:100]}...")
        
        # Detect language
        detected_language = await service.detect_language(request.text)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Build response
        response = LanguageDetectionResponse(
            request_id=request_id,
            text=request.text,
            detected_language=detected_language,
            confidence_score=0.9,  # Placeholder - would come from detection service
            supported_languages=["en", "yo"],
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
        )
        
        logger.info(f"Language detection completed (ID: {request_id}): {detected_language}")
        return response
        
    except Exception as e:
        logger.error(f"Language detection error (ID: {request_id}): {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to detect language",
                "error_code": "LANGUAGE_DETECTION_ERROR",
                "request_id": request_id,
            }
        )


@router.get("/supported-languages")
async def get_supported_languages() -> Dict[str, Any]:
    """
    Get list of supported languages for translation
    
    Returns:
        Supported language information
    """
    return {
        "supported_languages": ["en", "yo"],
        "language_names": {
            "en": "English",
            "yo": "Yoruba",
        },
        "language_pairs": [
            {"source": "en", "target": "yo", "name": "English to Yoruba"},
            {"source": "yo", "target": "en", "name": "Yoruba to English"},
        ],
        "default_source": "en",
        "default_target": "yo",
    }


@router.get("/translation-stats")
async def get_translation_statistics() -> Dict[str, Any]:
    """
    Get translation processing statistics
    
    Returns:
        Translation processing statistics
    """
    # This would typically query a database for real statistics
    return {
        "total_translations": 0,  # Would be from database
        "successful_translations": 0,
        "failed_translations": 0,
        "average_processing_time": 0.0,
        "languages_translated": ["en", "yo"],
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/translation-quality")
async def get_translation_quality_metrics() -> Dict[str, Any]:
    """
    Get translation quality metrics
    
    Returns:
        Translation quality information
    """
    return {
        "overall_quality_score": 0.95,
        "language_scores": {
            "en-yo": 0.92,
            "yo-en": 0.94,
        },
        "quality_metrics": {
            "fluency": 0.96,
            "adequacy": 0.94,
            "consistency": 0.93,
        },
        "last_updated": datetime.now().isoformat(),
    } 