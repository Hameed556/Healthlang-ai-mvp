
# HealthLang AI MVP

A bilingual (Yoruba-English) medical Q&A system powered by LLaMA-4 Maverick via Groq API, with medical reasoning and translation now integrated via a robust MCP HTTP server.

## 🚀 Features

- **Bilingual Support**: Yoruba ↔ English translation and medical Q&A
- **Medical Intelligence**: Advanced medical reasoning via LLaMA-4 Maverick 17B
- **High-Quality Translation**: LLaMA-4 Maverick powered translation with proper Yoruba character support
- **Fast Performance**: Groq LPU acceleration for real-time responses
- **Production Ready**: FastAPI + comprehensive error handling and monitoring
- **UTF-8 Encoding**: Proper support for Yoruba diacritical marks and special characters

## 🏗️ Architecture

```
User Query (Yoruba/English) 
    ↓
Language Detection
    ↓
Translation Service (LLaMA-4 Maverick)
    ↓
Medical Reasoning (LLaMA-4 Maverick)
    ↓
Response Generation & Translation
    ↓
Formatted Medical Answer (Yoruba)
```


## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **LLM**: LLaMA-4 Maverick 17B via Groq API
- **Medical Reasoning & Tools**: MCP Node.js server (HTTP endpoints)
- **Translation**: MCP HTTP endpoints (Yoruba-English)
- **Deployment**: Docker, Kubernetes ready
- **Monitoring**: Prometheus metrics, comprehensive logging
- **Documentation**: Auto-generated OpenAPI/Swagger

## 📦 Quick Start


### Prerequisites

- Python 3.11+
- Groq API key
- MCP Node.js server (see MCP documentation)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd healthlang-ai-mvp
   ```


2. **Set up environment**
    ```bash
    cp .env.example .env
    # Edit .env with your API keys and MCP server config:
    # GROQ_API_KEY=your_groq_api_key
    # MCP_BASE_URL=https://healthcare-mcp.onrender.com
    # MCP_API_KEY=your_mcp_api_key (if required)
    ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```


4. **Run the application**
    ```bash
    # Start MCP server (must be running for medical reasoning and translation)
    node mcp_servers/healthcare_server.js

    # Development
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info

    # Production with Docker
    docker-compose up -d
    ```


## 📚 API Documentation

Once running (with MCP server active), visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **MCP Health Check**: http://localhost:8000/mcp-health
- **Metrics**: http://localhost:8000/metrics


### Example Usage

```python
import requests

# Medical query (English → Yoruba response)
response = requests.post("http://localhost:8000/api/v1/query", json={
    "text": "What are the symptoms of diabetes?"
})
result = response.json()
print(f"Response: {result['response']}")
print(f"Processing Time: {result['processing_time']}s")

# Translation (English → Yoruba)
response = requests.post("http://localhost:8000/api/v1/translate/", json={
    "text": "Hello, how are you?",
    "source_language": "en",
    "target_language": "yo"
})
result = response.json()
print(f"Translated: {result['translated_text']}")

# Language detection
response = requests.post("http://localhost:8000/api/v1/translate/detect-language", json={
    "text": "Bawo ni o"
})
result = response.json()
print(f"Detected Language: {result['detected_language']}")
```


### cURL Examples

```bash
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

## 🎯 Key Features


### ✅ **Working Features:**
- **Medical Query Processing**: Full pipeline with MCP HTTP server and LLaMA-4 Maverick
- **Bidirectional Translation**: English ↔ Yoruba via MCP HTTP endpoints
- **Language Detection**: Automatic via MCP HTTP endpoints
- **Error Handling**: Graceful fallbacks and comprehensive error messages
- **UTF-8 Encoding**: Proper Yoruba character support (ẹ, ọ, ṣ, etc.)
- **API Documentation**: Interactive Swagger UI at `/docs`
- **Health Monitoring**: Comprehensive health checks, including MCP server
- **Metrics**: Prometheus metrics for monitoring

### 🔧 **Technical Stack:**
- **LLM**: LLaMA-4 Maverick 17B via Groq API
- **Translation**: LLaMA-4 Maverick 17B via Groq API
- **Framework**: FastAPI with async support
- **Encoding**: UTF-8 with proper Yoruba character support
- **Documentation**: Auto-generated OpenAPI/Swagger

## 📈 Performance Characteristics

| Endpoint | Average Response Time | Throughput | Model Used |
|----------|---------------------|------------|------------|
| `/health` | 5ms | 1000+ req/s | - |
| `/api/v1/translate/` | 2.5s | 10+ req/s | LLaMA-4 Maverick |
| `/api/v1/query` | 13-21s | 5+ req/s | LLaMA-4 Maverick |
| `/api/v1/translate/detect-language` | 10ms | 100+ req/s | - |

## 🧪 Testing

```bash
# Run all tests
pytest

# Test specific endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/supported-languages
```

## 📊 Monitoring

- **Health Check**: http://localhost:8000/health
- **Detailed Health**: http://localhost:8000/health/detailed
- **Metrics**: http://localhost:8000/metrics
- **API Documentation**: http://localhost:8000/docs

## 🎉 Recent Updates

### ✅ **Fixed Issues:**
1. **Model Configuration**: Now using correct LLaMA-4 Maverick model throughout
2. **Encoding Issues**: Fixed Yoruba character display problems
3. **API Endpoints**: All endpoints now working correctly
4. **Error Handling**: Improved fallback mechanisms
5. **Documentation**: Updated to reflect current functionality

### 🚀 **Performance Improvements:**
- Translation response time: ~2-3 seconds
- Medical query response time: ~13-21 seconds
- Proper UTF-8 encoding for Yoruba characters
- Robust error handling with fallbacks

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the [API documentation](docs/API_ENDPOINTS.md)
- Review the [system architecture](docs/SYSTEM_ARCHITECTURE.md)

## 🔮 Roadmap

- [ ] Voice input/output support
- [ ] Additional African languages
- [ ] Mobile app integration
- [ ] Advanced medical reasoning with RAG
- [ ] Multi-modal support (images, documents)
- [ ] Caching layer for improved performance
- [ ] Batch processing capabilities

## 🚀 Getting Started

The system is **fully functional** and ready for integration! Start by:

1. Setting up your API keys in `.env`
2. Running the application with `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
3. Testing the API at http://localhost:8000/docs
4. Exploring the comprehensive API documentation

The HealthLang AI MVP provides a robust foundation for bilingual medical AI applications with production-ready features and comprehensive error handling! 🎉 