"""
Validation utilities for HealthLang AI MVP
"""

import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from app.config import settings


def validate_language_code(language_code: str) -> bool:
    """
    Validate if a language code is supported
    
    Args:
        language_code: Language code to validate (e.g., 'en', 'yo')
        
    Returns:
        True if language is supported, False otherwise
    """
    if not language_code:
        return False
    
    supported_languages = ["en", "yo"]
    return language_code.lower() in supported_languages


def validate_text_length(text: str, min_length: int = 1, max_length: int = 10000) -> bool:
    """
    Validate text length
    
    Args:
        text: Text to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        
    Returns:
        True if text length is valid, False otherwise
    """
    if not text:
        return False
    
    text_length = len(text.strip())
    return min_length <= text_length <= max_length


def validate_url(url: str) -> bool:
    """
    Validate URL format
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid, False otherwise
    """
    if not url:
        return False
    
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email to validate
        
    Returns:
        True if email is valid, False otherwise
    """
    if not email:
        return False
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_medical_query(text: str) -> Dict[str, Any]:
    """
    Validate medical query content
    
    Args:
        text: Medical query text to validate
        
    Returns:
        Dictionary with validation results
    """
    result = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "suggestions": []
    }
    
    # Check if text is empty
    if not text or not text.strip():
        result["is_valid"] = False
        result["errors"].append("Query text cannot be empty")
        return result
    
    # Check text length
    if not validate_text_length(text, min_length=10, max_length=5000):
        result["is_valid"] = False
        result["errors"].append("Query text must be between 10 and 5000 characters")
    
    # Check for potentially harmful content
    harmful_patterns = [
        r'\b(kill|suicide|harm|hurt)\b',
        r'\b(drug|illegal|prescription)\b',
        r'\b(emergency|urgent|immediate)\b'
    ]
    
    for pattern in harmful_patterns:
        if re.search(pattern, text.lower()):
            result["warnings"].append(f"Query contains potentially concerning terms: {pattern}")
    
    # Check for medical terms (basic check)
    medical_terms = [
        r'\b(pain|symptom|disease|illness|condition)\b',
        r'\b(treatment|medicine|medication|therapy)\b',
        r'\b(doctor|physician|nurse|hospital)\b'
    ]
    
    has_medical_content = any(re.search(pattern, text.lower()) for pattern in medical_terms)
    if not has_medical_content:
        result["suggestions"].append("Query may not be medical-related")
    
    return result


def validate_translation_request(
    text: str,
    source_language: str,
    target_language: str
) -> Dict[str, Any]:
    """
    Validate translation request
    
    Args:
        text: Text to translate
        source_language: Source language code
        target_language: Target language code
        
    Returns:
        Dictionary with validation results
    """
    result = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "suggestions": []
    }
    
    # Validate text
    if not validate_text_length(text, min_length=1, max_length=10000):
        result["is_valid"] = False
        result["errors"].append("Text must be between 1 and 10000 characters")
    
    # Validate source language
    if not validate_language_code(source_language):
        result["is_valid"] = False
        result["errors"].append(f"Unsupported source language: {source_language}")
    
    # Validate target language
    if not validate_language_code(target_language):
        result["is_valid"] = False
        result["errors"].append(f"Unsupported target language: {target_language}")
    
    # Check if source and target are the same
    if source_language == target_language:
        result["warnings"].append("Source and target languages are the same")
    
    return result


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key format
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if API key format is valid, False otherwise
    """
    if not api_key:
        return False
    
    # Basic validation - API keys should be non-empty and have reasonable length
    return len(api_key.strip()) >= 10


def validate_file_type(filename: str, allowed_types: Optional[List[str]] = None) -> bool:
    """
    Validate file type based on extension
    
    Args:
        filename: Name of the file to validate
        allowed_types: List of allowed file extensions (without dot)
        
    Returns:
        True if file type is allowed, False otherwise
    """
    if not filename:
        return False
    
    if allowed_types is None:
        allowed_types = settings.ALLOWED_FILE_TYPES
    
    # Extract file extension
    if '.' not in filename:
        return False
    
    file_extension = filename.split('.')[-1].lower()
    return file_extension in allowed_types


def validate_file_size(file_size: int, max_size: Optional[int] = None) -> bool:
    """
    Validate file size
    
    Args:
        file_size: File size in bytes
        max_size: Maximum allowed file size in bytes
        
    Returns:
        True if file size is valid, False otherwise
    """
    if max_size is None:
        max_size = settings.MAX_FILE_SIZE
    
    return 0 < file_size <= max_size


def sanitize_text(text: str) -> str:
    """
    Sanitize text input
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text


def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Basic JSON schema validation
    
    Args:
        data: Data to validate
        schema: Schema definition
        
    Returns:
        Dictionary with validation results
    """
    result = {
        "is_valid": True,
        "errors": [],
        "missing_fields": [],
        "extra_fields": []
    }
    
    # Check required fields
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in data:
            result["is_valid"] = False
            result["missing_fields"].append(field)
    
    # Check field types
    properties = schema.get("properties", {})
    for field_name, field_value in data.items():
        if field_name in properties:
            field_schema = properties[field_name]
            expected_type = field_schema.get("type")
            
            if expected_type == "string" and not isinstance(field_value, str):
                result["is_valid"] = False
                result["errors"].append(f"Field '{field_name}' must be a string")
            elif expected_type == "integer" and not isinstance(field_value, int):
                result["is_valid"] = False
                result["errors"].append(f"Field '{field_name}' must be an integer")
            elif expected_type == "boolean" and not isinstance(field_value, bool):
                result["is_valid"] = False
                result["errors"].append(f"Field '{field_name}' must be a boolean")
    
    return result


def validate_rate_limit_key(key: str) -> bool:
    """
    Validate rate limiting key format
    
    Args:
        key: Rate limiting key to validate
        
    Returns:
        True if key format is valid, False otherwise
    """
    if not key:
        return False
    
    # Rate limiting keys should be non-empty and not too long
    return 1 <= len(key) <= 255


def validate_cache_key(key: str) -> bool:
    """
    Validate cache key format
    
    Args:
        key: Cache key to validate
        
    Returns:
        True if key format is valid, False otherwise
    """
    if not key:
        return False
    
    # Cache keys should be non-empty and not too long
    # Also check for invalid characters
    invalid_chars = ['\x00', '\n', '\r', '\t']
    return (
        1 <= len(key) <= 250 and
        not any(char in key for char in invalid_chars)
    ) 