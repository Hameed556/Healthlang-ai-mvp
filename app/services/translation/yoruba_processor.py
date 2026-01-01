"""
Yoruba text processing service for HealthLang AI MVP
"""

import re
from typing import Dict, Any, List
from datetime import datetime

from app.config import settings
from app.core.exceptions import TranslationError
from app.utils.logger import get_logger
from app.services.medical.llm_client import LLMClient, LLMRequest

logger = get_logger(__name__)


class YorubaProcessor:
    """
    Yoruba-specific text processing service
    """
    
    def __init__(self):
        self._initialized = False
        self.llm_client = LLMClient()
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
        Postprocess translated text to improve Yoruba quality using LLM
        
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
            
            # Apply basic postprocessing steps first
            processed_text = text
            
            # 1. Restore Yoruba characters
            processed_text = self._restore_yoruba_characters(processed_text)
            
            # 2. Improve medical terminology
            processed_text = self._improve_medical_terms(processed_text)
            
            # 3. Use LLM to improve Yoruba quality
            processed_text = await self._llm_improve_yoruba(processed_text)
            
            # 4. Final formatting
            processed_text = self._final_formatting(processed_text)
            
            logger.debug(f"Postprocessing completed: {processed_text[:100]}...")
            return processed_text
            
        except Exception as e:
            logger.error(f"Yoruba postprocessing failed: {e}")
            # Return basic processing on error
            return self._basic_postprocess(text)
    
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
        # Ensure consistent Yoruba character forms
        for old, new in self.yoruba_characters.items():
            text = text.replace(old, new)
        return text
    
    async def _llm_improve_yoruba(self, text: str) -> str:
        """
        Use LLM to improve Yoruba text quality, grammar, and naturalness.
        
        Args:
            text: Yoruba text to improve
            
        Returns:
            Improved Yoruba text
        """
        try:
            system_prompt = """You are a Yoruba language expert specializing in Nigerian Yoruba.
Your task is to improve Yoruba text by:
1. Correcting grammar and ensuring proper Yoruba syntax
2. Using natural, idiomatic Yoruba expressions
3. Ensuring proper use of Yoruba characters (ẹ, ọ, ṣ)
4. Making the text sound natural and fluent
5. Preserving the original meaning exactly

Provide ONLY the improved Yoruba text without explanations."""
            
            prompt = f"""Improve this Yoruba text to make it more natural and grammatically correct:

{text}

Provide the improved version:"""
            
            request = LLMRequest(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=500,
                temperature=0.2  # Slightly higher for natural variation
            )
            
            response = await self.llm_client.generate(request)
            improved_text = response.content.strip()
            
            # Validate the improved text has content
            if improved_text and len(improved_text) >= len(text) * 0.5:
                logger.debug(f"LLM improved Yoruba text successfully")
                return improved_text
            else:
                logger.warning("LLM improvement resulted in shorter text, keeping original")
                return text
                
        except Exception as e:
            logger.warning(f"LLM improvement failed, using original text: {e}")
            return text
    
    def _basic_postprocess(self, text: str) -> str:
        """
        Basic postprocessing fallback when LLM fails.
        
        Args:
            text: Text to process
            
        Returns:
            Processed text
        """
        processed = self._restore_yoruba_characters(text)
        processed = self._improve_medical_terms(processed)
        processed = self._final_formatting(processed)
        return processed
    
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
        Validate Yoruba text quality using LLM-based analysis.
        
        Args:
            text: Text to validate
            
        Returns:
            Validation results
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Use LLM for intelligent validation
            validation_result = await self._llm_validate_yoruba(text)
            return validation_result
            
        except Exception as e:
            logger.error(f"LLM validation failed, using fallback: {e}")
            return self._basic_validation(text)
    
    async def _llm_validate_yoruba(self, text: str) -> Dict[str, Any]:
        """
        Use LLM to validate Yoruba text quality.
        
        Args:
            text: Text to validate
            
        Returns:
            Validation results with score and suggestions
        """
        try:
            system_prompt = """You are a Yoruba language expert. Evaluate the quality of Yoruba text.
Assess:
1. Grammar correctness
2. Natural fluency
3. Proper use of Yoruba characters (ẹ, ọ, ṣ)
4. Idiomatic expressions
5. Overall quality

Provide a score from 0.0 to 1.0 and list any issues.
Respond in JSON format:
{
  "score": 0.0-1.0,
  "is_valid": true/false,
  "issues": ["issue1", "issue2"],
  "suggestions": ["suggestion1", "suggestion2"]
}"""
            
            prompt = f"Validate this Yoruba text:\n\n{text}"
            
            request = LLMRequest(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=300,
                temperature=0.1
            )
            
            response = await self.llm_client.generate(request)
            
            # Try to parse JSON response
            import json
            try:
                result = json.loads(response.content.strip())
                result["timestamp"] = datetime.now().isoformat()
                result["method"] = "llm"
                return result
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                logger.warning("LLM response not valid JSON, using basic validation")
                return self._basic_validation(text)
                
        except Exception as e:
            logger.error(f"LLM validation failed: {e}")
            return self._basic_validation(text)
    
    def _basic_validation(self, text: str) -> Dict[str, Any]:
        """
        Basic validation fallback using pattern matching.
        
        Args:
            text: Text to validate
            
        Returns:
            Validation results
        """
        validation_result = {
            "is_valid": True,
            "score": 0.0,
            "issues": [],
            "suggestions": [],
            "method": "basic",
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
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Yoruba processor"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "llm_available": self.llm_client is not None,
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