"""
Main translation service for HealthLang AI MVP
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from app.config import settings
from app.core.exceptions import TranslationError, LanguageNotSupportedError
from app.utils.logger import get_logger
from app.services.medical.llm_client import LLMClient, LLMRequest
from .language_detector import LanguageDetector
from .yoruba_processor import YorubaProcessor

logger = get_logger(__name__)


class TranslationService:
    """
    Main translation service for handling Yoruba-English translations
    """
    
    def __init__(self):
        self.language_detector: Optional[LanguageDetector] = None
        self.yoruba_processor: Optional[YorubaProcessor] = None
        self.llm_client: Optional[LLMClient] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the translation service"""
        if self._initialized:
            return
        
        logger.info("Initializing TranslationService...")
        
        try:
            # Initialize LLM client for translation
            self.llm_client = LLMClient()
            logger.info("LLM client initialized for translation")
            
            # Initialize language detector
            self.language_detector = LanguageDetector()
            await self.language_detector.initialize()
            
            # Initialize Yoruba processor
            self.yoruba_processor = YorubaProcessor()
            await self.yoruba_processor.initialize()
            
            self._initialized = True
            logger.info("TranslationService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize TranslationService: {e}")
            raise TranslationError(f"Translation service initialization failed: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup translation service resources"""
        logger.info("Cleaning up TranslationService...")
        
        cleanup_tasks = []
        
        if self.language_detector:
            cleanup_tasks.append(self.language_detector.cleanup())
        if self.yoruba_processor:
            cleanup_tasks.append(self.yoruba_processor.cleanup())
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        self._initialized = False
        logger.info("TranslationService cleanup completed")
    
    async def translate(
        self,
        text: str,
        source_language: str = "en",
        target_language: str = "yo",
    ) -> str:
        """
        Translate text between supported languages
        
        Args:
            text: Text to translate
            source_language: Source language code (en, yo)
            target_language: Target language code (en, yo)
            
        Returns:
            Translated text
            
        Raises:
            LanguageNotSupportedError: If language is not supported
            TranslationError: If translation fails
        """
        if not self._initialized:
            await self.initialize()
        
        # Validate languages
        if not self._is_language_supported(source_language):
            raise LanguageNotSupportedError(source_language)
        
        if not self._is_language_supported(target_language):
            raise LanguageNotSupportedError(target_language)
        
        # Normalize language codes
        source_lang = source_language.lower()
        target_lang = target_language.lower()
        
        # If source and target are the same, return original text
        if source_lang == target_lang:
            return text
        
        try:
            logger.debug(f"Translating from {source_lang} to {target_lang}: {text[:100]}...")
            
            # Handle Yoruba-specific processing
            if source_lang == "yo" or target_lang == "yo":
                return await self._translate_with_yoruba(text, source_lang, target_lang)
            
            # For now, use a simple placeholder translation
            # In a real implementation, this would use a proper translation model
            translated_text = await self._simple_translate(text, source_lang, target_lang)
            
            logger.debug(f"Translation completed: {translated_text[:100]}...")
            return translated_text
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise TranslationError(f"Failed to translate text: {e}")
    
    async def detect_language(self, text: str) -> str:
        """
        Detect the language of the provided text
        
        Args:
            text: Text to detect language for
            
        Returns:
            Detected language code (en, yo)
            
        Raises:
            TranslationError: If language detection fails
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.debug(f"Detecting language for: {text[:100]}...")
            
            detected_lang = await self.language_detector.detect(text)
            
            logger.debug(f"Language detected: {detected_lang}")
            return detected_lang
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            raise TranslationError(f"Failed to detect language: {e}")
    
    async def translate_batch(
        self,
        texts: list[str],
        source_language: str = "en",
        target_language: str = "yo",
    ) -> list[str]:
        """
        Translate multiple texts in batch
        
        Args:
            texts: List of texts to translate
            source_language: Source language code (en, yo)
            target_language: Target language code (en, yo)
            
        Returns:
            List of translated texts
            
        Raises:
            TranslationError: If batch translation fails
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info(f"Translating batch of {len(texts)} texts")
            
            # Process translations concurrently
            tasks = [
                self.translate(text, source_language, target_language)
                for text in texts
            ]
            
            translated_texts = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any exceptions
            results = []
            for i, result in enumerate(translated_texts):
                if isinstance(result, Exception):
                    logger.error(f"Translation failed for text {i}: {result}")
                    raise TranslationError(f"Batch translation failed: {result}")
                results.append(result)
            
            logger.info(f"Batch translation completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Batch translation failed: {e}")
            raise TranslationError(f"Failed to translate batch: {e}")
    
    async def _translate_with_yoruba(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """Handle translations involving Yoruba using LLaMA-4 Maverick"""
        try:
            # Preprocess text if needed
            if source_lang == "yo":
                text = await self.yoruba_processor.preprocess(text)
            
            # Perform translation using LLaMA-4 Maverick
            translated_text = await self._simple_translate(text, source_lang, target_lang)
            
            # Postprocess text if needed
            if target_lang == "yo":
                translated_text = await self.yoruba_processor.postprocess(translated_text)
            
            return translated_text
            
        except Exception as e:
            logger.error(f"Yoruba translation failed: {e}")
            raise TranslationError(f"Yoruba translation failed: {e}")
    
    async def _simple_translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """
        Translate using LLM client (Groq/LLaMA-4 Maverick)
        """
        try:
            # Prepare translation prompt
            if source_lang == "yo" and target_lang == "en":
                system_prompt = """You are a professional translator specializing in Yoruba to English translation. 
Provide accurate, natural translations that preserve the meaning and context.
Provide ONLY the English translation without explanations or additional text."""
                prompt = f"Translate this Yoruba text to English:\n\n{text}"
            else:
                system_prompt = """You are a professional translator specializing in English to Yoruba translation.
Provide accurate, natural translations that preserve the meaning and context.
Provide ONLY the Yoruba translation without explanations or additional text."""
                prompt = f"Translate this English text to Yoruba:\n\n{text}"
            
            # Use LLMClient for translation
            request = LLMRequest(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=1000,
                temperature=0.1  # Low temperature for consistent translations
            )
            
            response = await self.llm_client.generate(request)
            translated_text = response.content.strip()
            
            logger.debug(f"Translation completed: {translated_text[:100]}...")
            return translated_text
                    
        except Exception as e:
            logger.error(f"Translation service error: {e}")
            # Fallback to simple dictionary for basic words
            return await self._fallback_translate(text, source_lang, target_lang)
    
    async def _fallback_translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """
        Fallback translation using simple dictionary
        """
        # Basic translations for fallback
        translations = {
            ("en", "yo"): {
                "hello": "bawo",
                "how are you": "bawo ni o",
                "thank you": "o se",
                "goodbye": "o dabọ",
                "medicine": "oogun",
                "doctor": "dokita",
                "hospital": "ile iwosan",
                "pain": "iro",
                "fever": "iba",
                "headache": "ori fifo",
            },
            ("yo", "en"): {
                "bawo": "hello",
                "bawo ni o": "how are you",
                "o se": "thank you",
                "o dabọ": "goodbye",
                "oogun": "medicine",
                "dokita": "doctor",
                "ile iwosan": "hospital",
                "iro": "pain",
                "iba": "fever",
                "ori fifo": "headache",
            }
        }
        
        translation_dict = translations.get((source_lang, target_lang), {})
        
        # Simple word-by-word translation (very basic)
        words = text.lower().split()
        translated_words = []
        
        for word in words:
            # Clean word (remove punctuation)
            clean_word = ''.join(c for c in word if c.isalnum())
            translated_word = translation_dict.get(clean_word, word)
            translated_words.append(translated_word)
        
        translated_text = ' '.join(translated_words)
        
        # If no translation found, return original text with a note
        if translated_text == text.lower():
            logger.warning(f"No translation found for: {text}")
            return f"[Translation not available] {text}"
        
        return translated_text
    
    def _is_language_supported(self, language: str) -> bool:
        """Check if language is supported"""
        supported_languages = ["en", "yo"]
        return language.lower() in supported_languages
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on translation service"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "llm_client_available": self.llm_client is not None,
            "components": {},
        }
        
        try:
            # Check language detector
            if self.language_detector:
                detector_health = await self.language_detector.health_check()
                health_status["components"]["language_detector"] = detector_health
            else:
                health_status["components"]["language_detector"] = {"status": "not_initialized"}
            
            # Check Yoruba processor
            if self.yoruba_processor:
                processor_health = await self.yoruba_processor.health_check()
                health_status["components"]["yoruba_processor"] = processor_health
            else:
                health_status["components"]["yoruba_processor"] = {"status": "not_initialized"}
            
            # Overall status
            all_healthy = all(
                comp.get("status") == "healthy" 
                for comp in health_status["components"].values()
            )
            
            if not all_healthy:
                health_status["status"] = "degraded"
            
        except Exception as e:
            logger.error(f"Translation service health check failed: {e}")
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status
    
    async def get_translation_quality(
        self,
        source_text: str,
        translated_text: str,
        source_language: str,
        target_language: str,
    ) -> Dict[str, Any]:
        """
        Get translation quality metrics
        
        Args:
            source_text: Original text
            translated_text: Translated text
            source_language: Source language
            target_language: Target language
            
        Returns:
            Quality metrics dictionary
        """
        # Placeholder implementation
        # In a real system, this would use BLEU scores, human evaluation, etc.
        
        return {
            "fluency_score": 0.85,
            "adequacy_score": 0.82,
            "overall_score": 0.84,
            "confidence": 0.78,
            "metrics": {
                "length_ratio": len(translated_text) / len(source_text) if source_text else 1.0,
                "word_count": len(translated_text.split()),
                "character_count": len(translated_text),
            },
            "timestamp": datetime.now().isoformat(),
        } 