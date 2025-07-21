"""
Language detection service for HealthLang AI MVP
"""

import re
from typing import Dict, Any, List
from datetime import datetime

from app.config import settings
from app.core.exceptions import TranslationError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LanguageDetector:
    """
    Language detection service for identifying text language
    """
    
    def __init__(self):
        self._initialized = False
        self.yoruba_patterns = self._load_yoruba_patterns()
        self.english_patterns = self._load_english_patterns()
    
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
            
            # Use pattern-based detection for MVP
            detected_lang = self._pattern_based_detection(text)
            
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
    
    def _pattern_based_detection(self, text: str) -> str:
        """
        Pattern-based language detection
        
        This is a simple implementation for MVP. In production, you would use:
        - langdetect library
        - Polyglot library
        - Custom trained models
        - API services like Google Translate API
        """
        text_lower = text.lower()
        
        # Count Yoruba-specific patterns
        yoruba_score = 0
        for pattern in self.yoruba_patterns:
            matches = len(re.findall(pattern, text_lower))
            yoruba_score += matches
        
        # Count English-specific patterns
        english_score = 0
        for pattern in self.english_patterns:
            matches = len(re.findall(pattern, text_lower))
            english_score += matches
        
        # Check for Yoruba-specific characters
        yoruba_chars = len(re.findall(r'[ọọẹẹṣṣ]', text))
        yoruba_score += yoruba_chars * 2  # Weight Yoruba characters more heavily
        
        # Determine language based on scores
        if yoruba_score > english_score:
            return "yo"
        elif english_score > yoruba_score:
            return "en"
        else:
            # If scores are equal, check for common words
            return self._fallback_detection(text_lower)
    
    def _fallback_detection(self, text: str) -> str:
        """Fallback detection using common words"""
        yoruba_common_words = {
            "bawo", "o", "ni", "se", "dabọ", "oogun", "dokita", "ile", "iwosan",
            "iro", "iba", "ori", "fifo", "alafia", "dara", "ko", "ti", "wa"
        }
        
        english_common_words = {
            "the", "and", "or", "but", "in", "on", "at", "to", "for", "of",
            "with", "by", "is", "are", "was", "were", "be", "been", "have",
            "has", "had", "do", "does", "did", "will", "would", "could", "should"
        }
        
        words = set(text.split())
        
        yoruba_matches = len(words.intersection(yoruba_common_words))
        english_matches = len(words.intersection(english_common_words))
        
        if yoruba_matches > english_matches:
            return "yo"
        else:
            return "en"  # Default to English
    
    def _load_yoruba_patterns(self) -> List[str]:
        """Load Yoruba language patterns"""
        return [
            r'\b(bawo|o|ni|se|dabọ|oogun|dokita|ile|iwosan)\b',
            r'\b(iro|iba|ori|fifo|alafia|dara|ko|ti|wa)\b',
            r'\b(ẹ|ọ|ṣ)\w*',  # Words starting with Yoruba characters
            r'\b\w*[ọọẹẹṣṣ]\w*\b',  # Words containing Yoruba characters
            r'\b(ẹyin|ẹ|ọ|ṣ)\b',  # Common Yoruba pronouns/particles
        ]
    
    def _load_english_patterns(self) -> List[str]:
        """Load English language patterns"""
        return [
            r'\b(the|and|or|but|in|on|at|to|for|of)\b',
            r'\b(with|by|is|are|was|were|be|been|have|has)\b',
            r'\b(had|do|does|did|will|would|could|should)\b',
            r'\b(hello|how|are|you|thank|goodbye|medicine|doctor|hospital)\b',
            r'\b(pain|fever|headache|treatment|symptom|disease|illness)\b',
        ]
    
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
            text_lower = text.lower()
            
            # Calculate scores
            yoruba_score = 0
            for pattern in self.yoruba_patterns:
                matches = len(re.findall(pattern, text_lower))
                yoruba_score += matches
            
            english_score = 0
            for pattern in self.english_patterns:
                matches = len(re.findall(pattern, text_lower))
                english_score += matches
            
            # Add character-based scores
            yoruba_chars = len(re.findall(r'[ọọẹẹṣṣ]', text))
            yoruba_score += yoruba_chars * 2
            
            # Normalize scores
            total_score = yoruba_score + english_score
            if total_score == 0:
                yoruba_confidence = 0.5
                english_confidence = 0.5
            else:
                yoruba_confidence = yoruba_score / total_score
                english_confidence = english_score / total_score
            
            return {
                "yoruba_confidence": yoruba_confidence,
                "english_confidence": english_confidence,
                "detected_language": "yo" if yoruba_confidence > english_confidence else "en",
                "confidence_score": max(yoruba_confidence, english_confidence),
                "scores": {
                    "yoruba": yoruba_score,
                    "english": english_score,
                },
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
            "patterns_loaded": {
                "yoruba": len(self.yoruba_patterns),
                "english": len(self.english_patterns),
            },
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