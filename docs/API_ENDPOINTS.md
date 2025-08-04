# HealthLang AI MVP - API Documentation

This document provides comprehensive API documentation for the HealthLang AI MVP system, including all available endpoints, request/response formats, and usage examples.

## 🚀 **Base URL**
```
http://localhost:8000
```

## 📚 **API Overview**

The HealthLang AI MVP provides a **RESTful API** with the following main categories:
- **Medical Queries**: Process medical questions with RAG and translation using LLaMA-4 Maverick
- **Translation**: Yoruba-English bidirectional translation using LLaMA-4 Maverick
- **Health**: System health and monitoring endpoints
- **Documentation**: Interactive API docs (Swagger/ReDoc)

## 🔗 **Available Endpoints**

### **Root Endpoints**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Root endpoint with welcome message |
| `GET` | `/docs` | Interactive API documentation (Swagger) |
| `GET` | `/redoc` | Alternative API documentation (ReDoc) |
| `GET` | `/openapi.json` | OpenAPI specification |

### **Health & Monitoring**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Basic health check |
| `GET` | `/health/detailed` | Detailed health status |
| `GET` | `/metrics` | Prometheus metrics |

### **Medical Query Endpoints**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/query` | Process medical query with RAG |
| `GET` | `/api/v1/supported-languages` | Get supported languages |

### **Translation Endpoints**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/translate/` | Translate text |
| `POST` | `/api/v1/translate/batch` | Batch translation |
| `POST` | `/api/v1/translate/detect-language` | Detect language |
| `GET` | `/api/v1/translate/supported-languages` | Get supported languages |
| `GET` | `/api/v1/translate/translation-stats` | Get translation statistics |

## 🏥 **Medical Query API**

### **POST /api/v1/query**
Process a medical query with translation and RAG (Retrieval-Augmented Generation) using LLaMA-4 Maverick.

**Request Body:**
```json
{
  "text": "What are the symptoms of diabetes?"
}
```

**Response:**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "original_query": "What are the symptoms of diabetes?",
  "response": "**Ọrọ ibeere:** What are the symptoms of diabetes?\n**Idahun:** Àwọn àmì àìsàn ti àrùn sùkàrí (diabetes) ni:\n\n1. **Ìgbẹ̀ ti ó pọ̀ sí**: Ènìyàn tí ó ní diabetes máa ń ṣe ìgbẹ̀ púpọ̀...",
  "processing_time": 13.45,
  "timestamp": "2024-01-15T10:30:00Z",
  "metadata": {
    "original_language": "yo",
    "translation_used": true,
    "processing_steps": 4,
    "error": ""
  },
  "success": true,
  "error": ""
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What are the symptoms of diabetes?"
  }'
```

## 🌐 **Translation API**

### **POST /api/v1/translate/**
Translate text between supported languages using LLaMA-4 Maverick.

**Request Body:**
```json
{
  "text": "Hello, how are you?",
  "source_language": "en",
  "target_language": "yo"
}
```

**Response:**
```json
{
  "request_id": "9213ae4d-18b8-4595-84a2-b736bbef0f24",
  "original_text": "Hello, how are you?",
  "translated_text": "Ẹ n lẹ, bawo ni?",
  "source_language": "en",
  "target_language": "yo",
  "confidence_score": 0.95,
  "processing_time": 1.882943,
  "timestamp": "2025-08-04T20:39:15.282100",
  "metadata": {
    "preserve_formatting": true,
    "text_length": 19,
    "translated_length": 16
  }
}
```

### **POST /api/v1/translate/detect-language**
Detect the language of the provided text.

**Request Body:**
```json
{
  "text": "Bawo ni o"
}
```

**Response:**
```json
{
  "request_id": "874ca5c7-8184-4488-9092-cd0a9ed03107",
  "text": "Bawo ni o",
  "detected_language": "yo",
  "confidence_score": 0.95,
  "processing_time": 0.009,
  "timestamp": "2025-08-04T20:01:46.472000"
}
```

### **GET /api/v1/translate/supported-languages**
Get list of supported languages for translation.

**Response:**
```json
{
  "supported_languages": ["en", "yo"],
  "language_names": {
    "en": "English",
    "yo": "Yoruba"
  },
  "translation_pairs": [
    {
      "source": "en",
      "target": "yo",
      "description": "English to Yoruba"
    },
    {
      "source": "yo",
      "target": "en",
      "description": "Yoruba to English"
    }
  ]
}
```

### **GET /api/v1/translate/translation-stats**
Get translation statistics.

**Response:**
```json
{
  "total_translations": 1250,
  "successful_translations": 1245,
  "failed_translations": 5,
  "success_rate": 0.996,
  "average_processing_time": 2.34,
  "language_distribution": {
    "en_to_yo": 750,
    "yo_to_en": 500
  },
  "model_info": {
    "name": "meta-llama/Llama-4-Maverick-17B-128E-Instruct",
    "provider": "groq",
    "status": "active"
  }
}
```

## 🏥 **Health & Monitoring API**

### **GET /health**
Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "0.1.0"
}
```

### **GET /health/detailed**
Detailed health status of all components.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "components": {
    "translation": {
      "status": "healthy",
      "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct",
      "response_time": 2.1
    },
    "medical_reasoning": {
      "status": "healthy",
      "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct",
      "response_time": 13.5
    },
    "language_detection": {
      "status": "healthy",
      "response_time": 0.08
    }
  },
  "system": {
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 23.1
  }
}
```

### **GET /metrics**
Prometheus metrics endpoint.

**Response:**
```
# HELP healthlang_translations_total Total number of translations
# TYPE healthlang_translations_total counter
healthlang_translations_total{source_language="en",target_language="yo",status="success"} 750
healthlang_translations_total{source_language="yo",target_language="en",status="success"} 500

# HELP healthlang_translation_duration_seconds Translation duration in seconds
# TYPE healthlang_translation_duration_seconds histogram
healthlang_translation_duration_seconds_bucket{source_language="en",target_language="yo",le="1.0"} 200
healthlang_translation_duration_seconds_bucket{source_language="en",target_language="yo",le="2.0"} 450
```

## 🔧 **Configuration Endpoints**

### **GET /api/v1/supported-languages**
Get list of supported languages.

**Response:**
```json
{
  "supported_languages": ["en", "yo"],
  "language_names": {
    "en": "English",
    "yo": "Yoruba"
  }
}
```

## 📊 **Error Responses**

All endpoints return consistent error responses:

**400 Bad Request:**
```json
{
  "error": "Invalid request parameters",
  "error_code": "VALIDATION_ERROR",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "details": {
    "field": "text",
    "message": "Text cannot be empty"
  }
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error",
  "error_code": "INTERNAL_ERROR",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## 🔐 **Authentication & Security**

Currently, the API is designed for internal use. For production deployment, consider adding:

- **API Key Authentication**
- **Rate Limiting** (already configured)
- **CORS** (already configured)
- **Request Validation** (already implemented)

## 🚀 **Usage Examples**

### **Python Example:**
```python
import requests

# Medical query
response = requests.post(
    "http://localhost:8000/api/v1/query",
    json={
        "text": "What are the symptoms of diabetes?"
    }
)

result = response.json()
print(f"Response: {result['response']}")
print(f"Processing Time: {result['processing_time']}s")

# Translation
response = requests.post(
    "http://localhost:8000/api/v1/translate/",
    json={
        "text": "Hello, how are you?",
        "source_language": "en",
        "target_language": "yo"
    }
)

result = response.json()
print(f"Translated: {result['translated_text']}")
```

### **JavaScript Example:**
```javascript
// Medical query
const response = await fetch('http://localhost:8000/api/v1/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    text: 'What are the symptoms of diabetes?'
  })
});

const result = await response.json();
console.log('Response:', result.response);
console.log('Processing Time:', result.processing_time);

// Translation
const translationResponse = await fetch('http://localhost:8000/api/v1/translate/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    text: 'Hello, how are you?',
    source_language: 'en',
    target_language: 'yo'
  })
});

const translationResult = await translationResponse.json();
console.log('Translated:', translationResult.translated_text);
```

### **cURL Examples:**
```bash
# Health check
curl http://localhost:8000/health

# Medical query
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"text": "What are the symptoms of diabetes?"}'

# Translation
curl -X POST "http://localhost:8000/api/v1/translate/" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, how are you?", "source_language": "en", "target_language": "yo"}'

# Language detection
curl -X POST "http://localhost:8000/api/v1/translate/detect-language" \
  -H "Content-Type: application/json" \
  -d '{"text": "Bawo ni o"}'
```

## 📈 **Performance Characteristics**

| Endpoint | Average Response Time | Throughput | Model Used |
|----------|---------------------|------------|------------|
| `/health` | 5ms | 1000+ req/s | - |
| `/api/v1/translate/` | 2.5s | 10+ req/s | LLaMA-4 Maverick |
| `/api/v1/query` | 13-21s | 5+ req/s | LLaMA-4 Maverick |
| `/api/v1/translate/detect-language` | 10ms | 100+ req/s | - |

## 🎯 **Key Features**

### **✅ Working Features:**
- **Medical Query Processing**: Full RAG pipeline with LLaMA-4 Maverick
- **Bidirectional Translation**: English ↔ Yoruba with proper encoding
- **Language Detection**: Automatic language detection
- **Error Handling**: Graceful fallbacks and comprehensive error messages
- **UTF-8 Encoding**: Proper Yoruba character support
- **API Documentation**: Interactive Swagger UI at `/docs`
- **Health Monitoring**: Comprehensive health checks
- **Metrics**: Prometheus metrics for monitoring

### **🔧 Technical Stack:**
- **LLM**: LLaMA-4 Maverick 17B via Groq API
- **Translation**: LLaMA-4 Maverick 17B via Groq API
- **Framework**: FastAPI with async support
- **Encoding**: UTF-8 with proper Yoruba character support
- **Documentation**: Auto-generated OpenAPI/Swagger

## 🔮 **Future Enhancements**

Planned additional features:
- **Document Management**: Upload/process medical documents
- **User Management**: User profiles and preferences
- **Analytics**: Detailed usage analytics
- **Model Management**: Model updates and configuration
- **Caching**: Redis-based response caching
- **Batch Processing**: Enhanced batch operations

The API is **fully functional** and ready for integration with frontend applications, mobile apps, or other services! 🚀

## 🎉 **Recent Updates**

### **✅ Fixed Issues:**
1. **Model Configuration**: Now using correct LLaMA-4 Maverick model throughout
2. **Encoding Issues**: Fixed Yoruba character display problems
3. **API Endpoints**: All endpoints now working correctly
4. **Error Handling**: Improved fallback mechanisms
5. **Documentation**: Updated to reflect current functionality

### **🚀 Performance Improvements:**
- Translation response time: ~2-3 seconds
- Medical query response time: ~13-21 seconds
- Proper UTF-8 encoding for Yoruba characters
- Robust error handling with fallbacks 
The API is **fully functional** and ready for integration with frontend applications, mobile apps, or other services! 🚀 