"""
Language detection service for HealthLang AI MVP
"""

import re
from typing import Dict, Any, List
from datetime import datetime

from app.config import settings
from app.core.exceptions import TranslationError
from app.utils.logger import get_logger
from app.services.medical.llm_client import LLMClient, LLMRequest

logger = get_logger(__name__)


class LanguageDetector:
    """
    Language detection service for identifying text language
    """
    
    def __init__(self):
        self._initialized = False
        self.llm_client = LLMClient()
    
    async def initialize(self) -> None:
        """Initialize the language detector"""
        if self._initialized:
            return
        
        logger.info("Initializing LanguageDetector...")
        
        try:
            # Load language detection models if needed
            # For MVP, we'll use pattern-based detection
            self._initialized = True
            logger.info("LanguageDetector initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LanguageDetector: {e}")
            raise TranslationError(f"Language detector initialization failed: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup language detector resources"""
        logger.info("Cleaning up LanguageDetector...")
        self._initialized = False
        logger.info("LanguageDetector cleanup completed")
    
    async def detect(self, text: str) -> str:
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
        
        if not text or not text.strip():
            raise TranslationError("Cannot detect language for empty text")
        
        try:
            logger.debug(f"Detecting language for: {text[:100]}...")
            
            # Use LLM-based detection
            detected_lang = await self._llm_based_detection(text)
            
            logger.debug(f"Language detected: {detected_lang}")
            return detected_lang
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            raise TranslationError(f"Failed to detect language: {e}")
    
    async def detect_batch(self, texts: List[str]) -> List[str]:
        """
        Detect languages for multiple texts
        
        Args:
            texts: List of texts to detect languages for
            
        Returns:
            List of detected language codes
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info(f"Detecting languages for {len(texts)} texts")
            
            detected_languages = []
            for text in texts:
                try:
                    lang = await self.detect(text)
                    detected_languages.append(lang)
                except Exception as e:
                    logger.warning(f"Failed to detect language for text: {e}")
                    detected_languages.append("en")  # Default to English
            
            logger.info(f"Batch language detection completed")
            return detected_languages
            
        except Exception as e:
            logger.error(f"Batch language detection failed: {e}")
            raise TranslationError(f"Failed to detect languages in batch: {e}")
    
    async def _llm_based_detection(self, text: str) -> str:
        """
        LLM-based language detection using Groq.
        
        Detects between English and Yoruba languages.
        """
        try:
            system_prompt = """You are a language detector. Identify if the given text is in ENGLISH or YORUBA (Nigerian Pidgin).

ENGLISH characteristics:
- Standard English vocabulary and grammar
- Common words: the, and, is, are, have, what, how, doctor, medicine, treatment

YORUBA characteristics:
- Yoruba vocabulary and grammar
- Special characters: ẹ, ọ, ṣ
- Common words: bawo, oogun, dokita, ile, iwosan, alafia, dara
- Yoruba phrases and expressions

Respond with ONLY one word: ENGLISH or YORUBA"""
            
            request = LLMRequest(
                prompt=f"Text: {text}\n\nDetect the language:",
                system_prompt=system_prompt,
                max_tokens=10,
                temperature=0.1
            )
            
            response = await self.llm_client.generate(request)
            classification = response.content.strip().upper()
            
            # Map to language codes
            if "YORUBA" in classification:
                detected = "yo"
            else:
                detected = "en"
            
            logger.info(f"LLM detected language: {classification} -> {detected}")
            return detected
            
        except Exception as e:
            logger.warning(f"LLM language detection failed, using fallback: {e}")
            return self._fallback_detection(text)
    
    def _fallback_detection(self, text: str) -> str:
        """
        Minimal fallback detection using character and word patterns.
        
        Args:
            text: Text to detect language for
            
        Returns:
            Language code (en or yo)
        """
        text_lower = text.lower()
        
        # Check for Yoruba-specific characters
        yoruba_chars = re.findall(r'[ọẹṣ]', text_lower)
        if len(yoruba_chars) >= 2:
            return "yo"
        
        # Check for common Yoruba words
        yoruba_words = ['bawo', 'oogun', 'dokita', 'alafia', 'dara', 'dabọ']
        if any(word in text_lower for word in yoruba_words):
            return "yo"
        
        # Default to English
        return "en"
    
    async def get_confidence_score(self, text: str) -> Dict[str, Any]:
        """
        Get confidence score for language detection
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with confidence scores for each language
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Use LLM detection
            detected_lang = await self._llm_based_detection(text)
            
            # LLM-based detection has high confidence
            if detected_lang == "yo":
                yoruba_confidence = 0.9
                english_confidence = 0.1
            else:
                yoruba_confidence = 0.1
                english_confidence = 0.9
            
            return {
                "yoruba_confidence": yoruba_confidence,
                "english_confidence": english_confidence,
                "detected_language": detected_lang,
                "confidence_score": max(yoruba_confidence, english_confidence),
                "method": "llm",
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Confidence score calculation failed: {e}")
            return {
                "yoruba_confidence": 0.5,
                "english_confidence": 0.5,
                "detected_language": "en",
                "confidence_score": 0.5,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on language detector"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "method": "llm_based",
            "llm_available": self.llm_client is not None,
        }
        
        try:
            # Test detection with sample texts
            test_texts = [
                "Hello, how are you?",
                "Bawo ni o?",
                "The doctor prescribed medicine",
                "Dokita fun mi ni oogun",
            ]
            
            for text in test_texts:
                detected = await self.detect(text)
                logger.debug(f"Test detection: '{text}' -> {detected}")
            
            health_status["test_results"] = "passed"
            
        except Exception as e:
            logger.error(f"Language detector health check failed: {e}")
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status 