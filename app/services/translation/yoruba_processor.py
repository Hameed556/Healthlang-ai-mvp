"""
Yoruba text processing service for HealthLang AI MVP
"""

import re
from typing import Dict, Any, List
from datetime import datetime

from app.config import settings
from app.core.exceptions import TranslationError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class YorubaProcessor:
    """
    Yoruba-specific text processing service
    """
    
    def __init__(self):
        self._initialized = False
        self.yoruba_characters = self._load_yoruba_characters()
        self.medical_terms = self._load_medical_terms()
        self.normalization_rules = self._load_normalization_rules()
    
    async def initialize(self) -> None:
        """Initialize the Yoruba processor"""
        if self._initialized:
            return
        
        logger.info("Initializing YorubaProcessor...")
        
        try:
            # Load Yoruba-specific models or resources if needed
            self._initialized = True
            logger.info("YorubaProcessor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize YorubaProcessor: {e}")
            raise TranslationError(f"Yoruba processor initialization failed: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup Yoruba processor resources"""
        logger.info("Cleaning up YorubaProcessor...")
        self._initialized = False
        logger.info("YorubaProcessor cleanup completed")
    
    async def preprocess(self, text: str) -> str:
        """
        Preprocess Yoruba text before translation
        
        Args:
            text: Yoruba text to preprocess
            
        Returns:
            Preprocessed text
        """
        if not self._initialized:
            await self.initialize()
        
        if not text:
            return text
        
        try:
            logger.debug(f"Preprocessing Yoruba text: {text[:100]}...")
            
            # Apply preprocessing steps
            processed_text = text
            
            # 1. Normalize Yoruba characters
            processed_text = self._normalize_yoruba_characters(processed_text)
            
            # 2. Standardize spacing
            processed_text = self._standardize_spacing(processed_text)
            
            # 3. Handle contractions
            processed_text = self._expand_contractions(processed_text)
            
            # 4. Clean up punctuation
            processed_text = self._clean_punctuation(processed_text)
            
            logger.debug(f"Preprocessing completed: {processed_text[:100]}...")
            return processed_text
            
        except Exception as e:
            logger.error(f"Yoruba preprocessing failed: {e}")
            raise TranslationError(f"Failed to preprocess Yoruba text: {e}")
    
    async def postprocess(self, text: str) -> str:
        """
        Postprocess translated text to improve Yoruba quality
        
        Args:
            text: Translated text to postprocess
            
        Returns:
            Postprocessed text
        """
        if not self._initialized:
            await self.initialize()
        
        if not text:
            return text
        
        try:
            logger.debug(f"Postprocessing Yoruba text: {text[:100]}...")
            
            # Apply postprocessing steps
            processed_text = text
            
            # 1. Restore Yoruba characters
            processed_text = self._restore_yoruba_characters(processed_text)
            
            # 2. Apply Yoruba grammar rules
            processed_text = self._apply_grammar_rules(processed_text)
            
            # 3. Improve medical terminology
            processed_text = self._improve_medical_terms(processed_text)
            
            # 4. Final formatting
            processed_text = self._final_formatting(processed_text)
            
            logger.debug(f"Postprocessing completed: {processed_text[:100]}...")
            return processed_text
            
        except Exception as e:
            logger.error(f"Yoruba postprocessing failed: {e}")
            raise TranslationError(f"Failed to postprocess Yoruba text: {e}")
    
    async def tokenize(self, text: str) -> List[str]:
        """
        Tokenize Yoruba text
        
        Args:
            text: Yoruba text to tokenize
            
        Returns:
            List of tokens
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Simple tokenization for MVP
            # In production, use proper Yoruba tokenization
            tokens = text.split()
            
            # Handle Yoruba-specific tokenization
            processed_tokens = []
            for token in tokens:
                # Split on Yoruba-specific boundaries
                sub_tokens = re.split(r'([ọọẹẹṣṣ])', token)
                processed_tokens.extend([t for t in sub_tokens if t])
            
            return processed_tokens
            
        except Exception as e:
            logger.error(f"Yoruba tokenization failed: {e}")
            raise TranslationError(f"Failed to tokenize Yoruba text: {e}")
    
    def _normalize_yoruba_characters(self, text: str) -> str:
        """Normalize Yoruba characters"""
        # Replace common variations with standard forms
        replacements = {
            'ọ': 'ọ',  # Ensure consistent ọ
            'ọ': 'ọ',  # Ensure consistent ọ
            'ẹ': 'ẹ',  # Ensure consistent ẹ
            'ẹ': 'ẹ',  # Ensure consistent ẹ
            'ṣ': 'ṣ',  # Ensure consistent ṣ
            'ṣ': 'ṣ',  # Ensure consistent ṣ
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def _standardize_spacing(self, text: str) -> str:
        """Standardize spacing in Yoruba text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Ensure proper spacing around Yoruba particles
        particles = ['o', 'ni', 'ti', 'ko', 'ṣe', 'wa']
        for particle in particles:
            text = re.sub(f'\\b{particle}\\b', f' {particle} ', text)
        
        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _expand_contractions(self, text: str) -> str:
        """Expand Yoruba contractions"""
        contractions = {
            "o'n": "o ni",
            "o'ṣe": "o ṣe",
            "o'wa": "o wa",
            "o'ko": "o ko",
            "ẹ'n": "ẹ ni",
            "ẹ'ṣe": "ẹ ṣe",
            "ẹ'wa": "ẹ wa",
        }
        
        for contraction, expansion in contractions.items():
            text = text.replace(contraction, expansion)
        
        return text
    
    def _clean_punctuation(self, text: str) -> str:
        """Clean up punctuation in Yoruba text"""
        # Standardize Yoruba punctuation
        text = re.sub(r'[?!]+', '?', text)  # Multiple question marks to single
        text = re.sub(r'[.!]+', '.', text)  # Multiple periods to single
        
        # Ensure proper spacing around punctuation
        text = re.sub(r'\s*([.!?])\s*', r'\1 ', text)
        
        return text.strip()
    
    def _restore_yoruba_characters(self, text: str) -> str:
        """Restore proper Yoruba characters"""
        # This would be more sophisticated in production
        # For MVP, we'll do basic character restoration
        return text
    
    def _apply_grammar_rules(self, text: str) -> str:
        """Apply Yoruba grammar rules"""
        # Basic grammar corrections for MVP
        # In production, this would use a proper grammar checker
        
        # Ensure proper verb forms
        text = re.sub(r'\b(ṣe)\s+', r'ṣe ', text)
        text = re.sub(r'\b(wa)\s+', r'wa ', text)
        
        # Ensure proper pronoun forms
        text = re.sub(r'\b(o)\s+', r'o ', text)
        text = re.sub(r'\b(ẹ)\s+', r'ẹ ', text)
        
        return text
    
    def _improve_medical_terms(self, text: str) -> str:
        """Improve medical terminology in Yoruba"""
        # Replace common medical term variations with standard forms
        for term, standard in self.medical_terms.items():
            text = re.sub(rf'\b{term}\b', standard, text, flags=re.IGNORECASE)
        
        return text
    
    def _final_formatting(self, text: str) -> str:
        """Apply final formatting to Yoruba text"""
        # Ensure proper capitalization
        sentences = text.split('. ')
        formatted_sentences = []
        
        for sentence in sentences:
            if sentence:
                # Capitalize first letter
                sentence = sentence[0].upper() + sentence[1:] if sentence else sentence
                formatted_sentences.append(sentence)
        
        return '. '.join(formatted_sentences)
    
    def _load_yoruba_characters(self) -> Dict[str, str]:
        """Load Yoruba character mappings"""
        return {
            'ọ': 'ọ',
            'ọ': 'ọ',
            'ẹ': 'ẹ',
            'ẹ': 'ẹ',
            'ṣ': 'ṣ',
            'ṣ': 'ṣ',
        }
    
    def _load_medical_terms(self) -> Dict[str, str]:
        """Load medical term standardizations"""
        return {
            'dokita': 'dokita',
            'oogun': 'oogun',
            'ile iwosan': 'ile iwosan',
            'iro': 'iro',
            'iba': 'iba',
            'ori fifo': 'ori fifo',
            'itọju': 'itọju',
            'alafia': 'alafia',
            'arun': 'arun',
            'iwosan': 'iwosan',
        }
    
    def _load_normalization_rules(self) -> List[Dict[str, str]]:
        """Load text normalization rules"""
        return [
            {'pattern': r'\s+', 'replacement': ' '},
            {'pattern': r'[ọọ]', 'replacement': 'ọ'},
            {'pattern': r'[ẹẹ]', 'replacement': 'ẹ'},
            {'pattern': r'[ṣṣ]', 'replacement': 'ṣ'},
        ]
    
    async def validate_yoruba_text(self, text: str) -> Dict[str, Any]:
        """
        Validate Yoruba text quality
        
        Args:
            text: Text to validate
            
        Returns:
            Validation results
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            validation_result = {
                "is_valid": True,
                "score": 0.0,
                "issues": [],
                "suggestions": [],
                "timestamp": datetime.now().isoformat(),
            }
            
            # Check for Yoruba characters
            yoruba_chars = len(re.findall(r'[ọọẹẹṣṣ]', text))
            if yoruba_chars == 0:
                validation_result["issues"].append("No Yoruba characters found")
                validation_result["score"] -= 0.3
            
            # Check for common Yoruba words
            yoruba_words = ['o', 'ni', 'ṣe', 'wa', 'ko', 'ti', 'bawo', 'dara']
            found_words = sum(1 for word in yoruba_words if word in text.lower())
            if found_words == 0:
                validation_result["issues"].append("No common Yoruba words found")
                validation_result["score"] -= 0.2
            
            # Check text length
            if len(text) < 5:
                validation_result["issues"].append("Text too short")
                validation_result["score"] -= 0.1
            
            # Calculate final score
            validation_result["score"] = max(0.0, 1.0 + validation_result["score"])
            
            if validation_result["score"] < 0.5:
                validation_result["is_valid"] = False
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Yoruba text validation failed: {e}")
            return {
                "is_valid": False,
                "score": 0.0,
                "issues": [f"Validation error: {e}"],
                "suggestions": [],
                "timestamp": datetime.now().isoformat(),
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Yoruba processor"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "yoruba_characters": len(self.yoruba_characters),
                "medical_terms": len(self.medical_terms),
                "normalization_rules": len(self.normalization_rules),
            },
        }
        
        try:
            # Test preprocessing and postprocessing
            test_text = "Bawo ni o? Mo wa ni ile iwosan."
            
            preprocessed = await self.preprocess(test_text)
            postprocessed = await self.postprocess(preprocessed)
            
            if preprocessed and postprocessed:
                health_status["test_results"] = "passed"
            else:
                health_status["status"] = "degraded"
                health_status["test_results"] = "failed"
            
        except Exception as e:
            logger.error(f"Yoruba processor health check failed: {e}")
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status 