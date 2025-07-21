# HealthLang AI MVP - API Documentation

This document provides comprehensive API documentation for the HealthLang AI MVP system, including all available endpoints, request/response formats, and usage examples.

## 🚀 **Base URL**
```
http://localhost:8000
```

## 📚 **API Overview**

The HealthLang AI MVP provides a **RESTful API** with the following main categories:
- **Medical Queries**: Process medical questions with RAG and translation
- **Translation**: Yoruba-English bidirectional translation
- **Health**: System health and monitoring endpoints
- **Documentation**: Interactive API docs (Swagger/ReDoc)

## 🔗 **Available Endpoints**

### **Root Endpoints**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Root endpoint with welcome message |
| `GET` | `/info` | Application information |
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
| `GET` | `/api/v1/query/{request_id}` | Get query status |
| `POST` | `/api/v1/query/batch` | Process multiple queries |
| `GET` | `/api/v1/supported-languages` | Get supported languages |
| `GET` | `/api/v1/query-stats` | Get query statistics |

### **Translation Endpoints**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/translate` | Translate text |
| `POST` | `/api/v1/translate/batch` | Batch translation |
| `GET` | `/api/v1/translate/detect` | Detect language |
| `GET` | `/api/v1/translate/quality` | Get translation quality |

## 🏥 **Medical Query API**

### **POST /api/v1/query**
Process a medical query with translation and RAG (Retrieval-Augmented Generation).

**Request Body:**
```json
{
  "text": "What are the symptoms of diabetes?",
  "source_language": "en",
  "target_language": "yo",
  "use_cache": true,
  "include_sources": true,
  "max_tokens": 2048,
  "temperature": 0.1
}
```

**Response:**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "original_query": "What are the symptoms of diabetes?",
  "source_language": "en",
  "target_language": "yo",
  "translated_query": "Kini awọn aami diabetes?",
  "response": "Awọn aami diabetes ni: 1) Igbẹ ti o pọ si ati igbẹ ti o ma n ṣe...",
  "processing_time": 2.45,
  "timestamp": "2024-01-15T10:30:00Z",
  "metadata": {
    "rag_enabled": true,
    "documents_retrieved": 3,
    "model_used": "llama-3-8b-8192",
    "cache_hit": false
  },
  "sources": [
    {
      "title": "WHO Diabetes Guidelines 2024",
      "url": "https://www.who.int/diabetes",
      "relevance_score": 0.92
    },
    {
      "title": "CDC Diabetes Information",
      "url": "https://www.cdc.gov/diabetes",
      "relevance_score": 0.88
    }
  ]
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What are the symptoms of diabetes?",
    "source_language": "en",
    "target_language": "yo",
    "include_sources": true
  }'
```

### **POST /api/v1/query/batch**
Process multiple medical queries in batch.

**Request Body:**
```json
{
  "queries": [
    {
      "text": "What are the symptoms of diabetes?",
      "source_language": "en",
      "target_language": "yo"
    },
    {
      "text": "Kini awọn oogun fun hypertension?",
      "source_language": "yo",
      "target_language": "en"
    }
  ]
}
```

**Response:**
```json
{
  "batch_id": "batch-550e8400-e29b-41d4-a716-446655440000",
  "results": [
    {
      "request_id": "550e8400-e29b-41d4-a716-446655440001",
      "original_query": "What are the symptoms of diabetes?",
      "response": "Awọn aami diabetes ni...",
      "status": "completed",
      "processing_time": 2.45
    },
    {
      "request_id": "550e8400-e29b-41d4-a716-446655440002",
      "original_query": "Kini awọn oogun fun hypertension?",
      "response": "The medications for hypertension include...",
      "status": "completed",
      "processing_time": 2.12
    }
  ],
  "total_queries": 2,
  "successful_queries": 2,
  "failed_queries": 0,
  "total_processing_time": 4.57
}
```

## 🌐 **Translation API**

### **POST /api/v1/translate**
Translate text between supported languages.

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
  "translated_text": "Bawo ni o?",
  "source_language": "en",
  "target_language": "yo",
  "confidence_score": 0.95,
  "processing_time": 0.15
}
```

### **POST /api/v1/translate/batch**
Batch translation of multiple texts.

**Request Body:**
```json
{
  "texts": [
    "Hello, how are you?",
    "Thank you very much",
    "Goodbye"
  ],
  "source_language": "en",
  "target_language": "yo"
}
```

**Response:**
```json
{
  "translations": [
    "Bawo ni o?",
    "O se pupọ",
    "O dabọ"
  ],
  "source_language": "en",
  "target_language": "yo",
  "processing_time": 0.45
}
```

### **GET /api/v1/translate/detect**
Detect the language of the provided text.

**Query Parameters:**
- `text`: Text to detect language for

**Response:**
```json
{
  "detected_language": "yo",
  "confidence_score": 0.92,
  "processing_time": 0.08
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
      "response_time": 0.15
    },
    "llm": {
      "status": "healthy",
      "model": "llama-3-8b-8192",
      "response_time": 2.1
    },
    "vector_store": {
      "status": "healthy",
      "documents": 15420,
      "response_time": 0.08
    },
    "cache": {
      "status": "healthy",
      "hit_rate": 0.67
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
# HELP healthlang_queries_total Total number of medical queries
# TYPE healthlang_queries_total counter
healthlang_queries_total{source_language="en",target_language="yo",status="success"} 1250
healthlang_queries_total{source_language="yo",target_language="en",status="success"} 890

# HELP healthlang_query_duration_seconds Query processing duration in seconds
# TYPE healthlang_query_duration_seconds histogram
healthlang_query_duration_seconds_bucket{source_language="en",target_language="yo",le="1.0"} 450
healthlang_query_duration_seconds_bucket{source_language="en",target_language="yo",le="2.0"} 800
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

### **GET /api/v1/query-stats**
Get query processing statistics.

**Response:**
```json
{
  "total_queries": 2140,
  "successful_queries": 2089,
  "failed_queries": 51,
  "success_rate": 0.976,
  "average_processing_time": 2.34,
  "language_distribution": {
    "en_to_yo": 1250,
    "yo_to_en": 890
  },
  "cache_stats": {
    "hit_rate": 0.67,
    "total_hits": 1433,
    "total_misses": 707
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
        "text": "What are the symptoms of diabetes?",
        "source_language": "en",
        "target_language": "yo",
        "include_sources": True
    }
)

result = response.json()
print(f"Response: {result['response']}")
print(f"Sources: {result['sources']}")
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
    text: 'What are the symptoms of diabetes?',
    source_language: 'en',
    target_language: 'yo',
    include_sources: true
  })
});

const result = await response.json();
console.log('Response:', result.response);
console.log('Sources:', result.sources);
```

### **cURL Examples:**
```bash
# Health check
curl http://localhost:8000/health

# Medical query
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"text": "What are the symptoms of diabetes?", "source_language": "en", "target_language": "yo"}'

# Translation
curl -X POST "http://localhost:8000/api/v1/translate" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello", "source_language": "en", "target_language": "yo"}'
```

## 📈 **Performance Characteristics**

| Endpoint | Average Response Time | Throughput |
|----------|---------------------|------------|
| `/health` | 5ms | 1000+ req/s |
| `/api/v1/translate` | 150ms | 100+ req/s |
| `/api/v1/query` | 2.5s | 10+ req/s |
| `/api/v1/query/batch` | 5s | 5+ req/s |

## 🔮 **Future Endpoints**

Planned additional endpoints:
- **Document Management**: Upload/process medical documents
- **User Management**: User profiles and preferences
- **Analytics**: Detailed usage analytics
- **Model Management**: Model updates and configuration

The API is **fully functional** and ready for integration with frontend applications, mobile apps, or other services! 🚀 