
# HealthLang AI MVP

An English-first, safety-forward medical assistant built with FastAPI that consults an MCP serv## 🌐 Real-time Knowledge with Tavily

The system integrates Tavily Search API for real-time general knowledge queries, ensuring current and accurate information:

**Key Features:**
- **Current Information**: Access to real-time data for questions about current events, leadership, recent developments
- **General Knowledge**: Complements medical expertise with broader knowledge base
- **Reliable Sources**: Search results from authoritative websites with proper citations
- **Automatic Detection**: System automatically determines when to use Tavily vs. medical sources
- **ChromaDB Caching**: Results cached locally for improved performance

**When Tavily is Used:**
- General knowledge questions ("Who's the president?", "What's the latest news about...")
- Current events and recent developments
- Non-medical factual queries that benefit from real-time information
- Questions where the LLM's training data might be outdated

**Configuration:**
- `TAVILY_API_KEY` - Your Tavily Search API key (required for real-time features)
- Automatically integrates with existing RAG workflow
- Uses advanced search depth for higher quality results (2 API credits per query)

## 🏗️ MCP Integration

The system uses an HTTP-based MCP (Model Context Protocol) client to fetch external medical context:and optional RAG with real-time knowledge via Tavily Search to provide concise, cited guidance. It defaults to English and can respond in Nigerian Pidgin on explicit request. Powered by configurable LLM providers (Groq primary by default, X.AI optional).

## 🚀 Features

- **English-first Chat**: All user inputs and chatbot responses are handled in English by default
- **Provider-flexible LLM**: Configurable primary provider (Groq by default with meta-llama/llama-4-maverick-17b-128e-instruct; X.AI as optional alternative)
- **Hybrid Context**: Optional RAG + external MCP tools (health topics, PubMed, clinical trials, etc.) + real-time knowledge via Tavily Search
- **Real-time Knowledge**: Tavily Search API integration for current information and general knowledge queries
- **MCP Integration**: HTTP client with robust error handling; graceful fallbacks when MCP unavailable
- **Friendly Medical Persona**: Safety guardrails, "My take" opinions, Nigerian Pidgin only on explicit request
- **Neat Sources**: Compact citations from PubMed/MCP/RAG with structured metadata
- **Translation Endpoints (parked)**: Translate APIs are kept for future voice features but not used by the chatbot flow now
- **Fast Performance**: Groq LPU acceleration for real-time responses
- **Production Ready**: FastAPI + comprehensive error handling and monitoring
- **UTF-8 Encoding**: Proper support for Yoruba diacritical marks and special characters

## 🏗️ Architecture

```
User Query (English)
    ↓
Medical Reasoning (LLaMA-4 Maverick)
    ↓
Optional Context Sources:
  • MCP Tools (PubMed, health topics, etc.)
  • RAG System (medical knowledge base)
  • Tavily Search (real-time general knowledge)
    ↓
Response Generation & Post-processing (opinion, citations, contextual follow-up)
    ↓
Formatted Medical Answer (English)
```


## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **LLM**: LLaMA-4 Maverick 17B via X.AI Grok (primary) and Groq (fallback)
- **Medical Reasoning & Tools**: MCP HTTP server (remote by default; sample local Python server included)
- **Real-time Knowledge**: Tavily Search API with LangChain integration
- **RAG System**: ChromaDB + SentenceTransformers for document retrieval
- **Translation**: Endpoints available but not used by the chat flow (reserved for TTS/STT)
- **Deployment**: Docker, Kubernetes ready
- **Monitoring**: Prometheus metrics, comprehensive logging
- **Documentation**: Auto-generated OpenAPI/Swagger

## 📦 Quick Start


### Prerequisites

- Python 3.11+
- X.AI (Grok) API key (recommended for primary model)
- Groq API key (used as fallback)
- Tavily API key (for real-time knowledge search)
- MCP HTTP server (remote default: https://healthcare-mcp.onrender.com). A sample local Python server is available in `mcp_servers/healthcare_server.py`.

### Installation

1. **Clone the repository**
    ```bash
    git clone <repository-url>
    cd healthlang-ai-mvp
    ```


2. **Set up environment**
        - Copy the example env file and edit values:
            - macOS/Linux:
                ```bash
                cp env.example .env
                ```
            - Windows (PowerShell):
                ```powershell
                Copy-Item env.example .env
                ```
        - Then open `.env` and set your keys and config:
            ```properties
            # LLM Provider Configuration
            MEDICAL_MODEL_PROVIDER=groq  # groq|xai (primary workflow selector)
            GROQ_API_KEY=your_groq_api_key  # required for Groq
            GROQ_MODEL=meta-llama/llama-4-maverick-17b-128e-instruct
            XAI_GROK_API_KEY=your_xai_api_key  # optional; used if provider=xai or as fallback
            MEDICAL_MODEL_NAME=grok-beta  # used when provider=xai
            
            # MCP Configuration
            MCP_ENABLED=true
            MCP_BASE_URL=https://healthcare-mcp.onrender.com
            MCP_API_KEY=  # optional; adds X-API-Key header if set
            
            # RAG Configuration
            RAG_ENABLED=true
            CHROMA_PERSIST_DIRECTORY=./data/chroma
            EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
            
            # Tavily Real-time Knowledge
            TAVILY_API_KEY=your_tavily_api_key
            
            # Server
            HOST=0.0.0.0
            PORT=8000
            ENVIRONMENT=development
            ```

3. **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```


4. **Run the application**
    ```bash
    # MCP server (choose ONE):
    # - Remote (default): ensure MCP_BASE_URL is set (no local process needed)
    # - Local sample (Python):
    python mcp_servers/healthcare_server.py

    # Development
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info
    # If you see a Windows port bind error (WinError 10048), try:
    # python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --log-level info

    # Production with Docker
    docker-compose up -d
    ```


## � MCP Integration

The system uses an HTTP-based MCP (Model Context Protocol) client to fetch external medical context:

**Available MCP Tools:**
- `health_topics`: Evidence-based health information from Health.gov
- `pubmed_search`: Medical literature from PubMed database
- `clinical_trials_search`: Clinical trial information
- `fda_drug_lookup`: FDA drug database lookups
- `medical_terminology_lookup`: ICD-10 code lookups
- `calculate_bmi`: BMI calculation utility

**How it Works:**
1. For each query, the system attempts lightweight MCP lookups (health topics + PubMed)
2. If MCP returns usable items, `metadata.mcp_used` is set to `true` and sources are appended
3. MCP failures are gracefully handled - the system continues with a WHO fallback source
4. Check `/mcp-health` endpoint to verify MCP server connectivity

**Response Parsing:**
The MCP client recognizes common response shapes including `data`, `results`, `items`, `articles`, `records`, `papers`, and `topics` arrays.

**Configuration:**
- `MCP_ENABLED=true/false` - Enable/disable MCP lookups
- `MCP_BASE_URL` - MCP server endpoint (default: https://healthcare-mcp.onrender.com)
- `MCP_API_KEY` - Optional API key for authenticated MCP servers

## �📚 API Documentation

Once running (with an MCP server reachable), visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **MCP Health Check**: http://localhost:8000/mcp-health
- **Metrics**: http://localhost:8000/metrics

Notes:
- `/mcp-health` proxies the upstream MCP and typically includes fields like `session_id` and `uptime_seconds` when healthy.
- Additional probes: `/health/detailed`, `/readiness`, `/liveness`.


### Example Usage

```python
import requests

# Medical query (English in → English out)
response = requests.post("http://localhost:8000/api/v1/query", json={
    "text": "What are the symptoms of diabetes?"
})
result = response.json()
print(f"Response: {result['response']}")
print(f"Processing Time: {result['processing_time']}s")

# Response tail will include:
# - My take: a short, non-diagnostic opinion
# - Contextual follow-up tailored to your question (Pidgin explanation on request)
# - Sources: neat references (PubMed / MCP / RAG) when available

# Translation endpoints are preserved for future voice features.
# They are not used by the chatbot flow. Example calls are still available in docs.

# Language detection endpoint is also preserved for future use.
```


### cURL Examples

**Linux/macOS:**
```bash
# Medical query (English-only chat)
curl -X POST "http://localhost:8001/api/v1/query" \
    -H "Content-Type: application/json" \
    -d '{"text": "What are the symptoms of diabetes?", "include_sources": true}'
```

**Windows PowerShell (recommended):**
```powershell
# Use curl.exe and single quotes for JSON to avoid escaping issues
$body = '{ "text": "What are early signs of type 2 diabetes?", "include_sources": true }'
curl.exe -s -X POST "http://127.0.0.1:8001/api/v1/query" -H "Content-Type: application/json" -d $body

# For Nigerian Pidgin (explicit request)
$body = '{ "text": "Explain malaria prevention. Please answer in Nigerian Pidgin and include sources." }'
curl.exe -s -X POST "http://127.0.0.1:8001/api/v1/query" -H "Content-Type: application/json" -d $body
```

**Windows cmd.exe:**
```cmd
REM Escape inner quotes by doubling them
curl -s -X POST http://127.0.0.1:8001/api/v1/query -H "Content-Type: application/json" -d "{\"text\":\"What are early signs of type 2 diabetes?\",\"include_sources\":true}"
```

## 🎯 Key Features


### ✅ **Working Features:**
- **Medical Query Processing (English-first)**: Full pipeline with MCP HTTP tools and LLaMA-4 Maverick
- **Optional RAG Context**: Retrieves relevant snippets when available
- **Translation Endpoints (Kept for Future Use)**: Available under `/api/v1/translate/*` but not used by the chatbot now
- **Error Handling**: Graceful fallbacks and comprehensive error messages
- **UTF-8 Encoding**: Proper Yoruba character support (ẹ, ọ, ṣ, etc.)
- **API Documentation**: Interactive Swagger UI at `/docs`
- **Health Monitoring**: Comprehensive health checks, including MCP server
- **Metrics**: Prometheus metrics for monitoring

### 🔧 **Technical Stack:**
- **LLM**: LLaMA-4 Maverick 17B via XAI Grok (primary), Groq fallback
- **Translation**: Parked for future voice features
- **Framework**: FastAPI with async support
- **Encoding**: UTF-8 with proper Yoruba character support
- **Documentation**: Auto-generated OpenAPI/Swagger

## 📈 Performance Characteristics

| Endpoint | Average Response Time | Throughput | Model Used |
|----------|---------------------|------------|------------|
| `/health` | 5ms | 1000+ req/s | - |
| `/api/v1/query` | 13-21s | 5+ req/s | LLaMA-4 Maverick |
| `/api/v1/translate/` | parked | - | - |
| `/api/v1/translate/detect-language` | parked | - | - |

## 🔧 Troubleshooting

**Common Issues:**

- **401 Invalid API Key (Groq)**: Verify `GROQ_API_KEY` in `.env` has no extra spaces/quotes. Restart the server after changes.

- **400/404 Model Not Found**: Confirm `GROQ_MODEL` is supported by your Groq account. Try a known model like `llama-3.1-8b-instant`.

- **MCP Not Used (`mcp_used=false`)**: 
  - Check `/mcp-health` endpoint for MCP server connectivity
  - Try more specific medical queries (e.g., mention drug names, conditions)
  - Some broad questions may not trigger MCP responses

- **JSON Decode Errors in Windows curl**: 
  - Use `curl.exe` instead of PowerShell's `curl` alias
  - Ensure request body uses `"text"` key (not `"query"`)
  - Follow Windows-safe quoting patterns above

- **Port 8000 Already in Use (Windows)**: Use `--port 8001` or check `netstat -ano | findstr :8000`

**Environment Variable Issues:**
- String values from `.env` are automatically trimmed of quotes and whitespace
- Provider names are normalized to lowercase (`"Groq"` → `"groq"`)
- Check `GET /health/detailed` to see current provider and model settings

## 🧪 Testing

```bash
# Run all tests
pytest

# Test specific endpoints
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/query -H "Content-Type: application/json" -d '{"text":"test"}'
```

Windows tip: If `curl` behaves unexpectedly in PowerShell, try `Invoke-RestMethod`:

```powershell
$body = @{ text = "test" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/query" -ContentType "application/json" -Body $body
```

## 📊 Monitoring

- **Health Check**: http://localhost:8000/health
- **Detailed Health**: http://localhost:8000/health/detailed
- **Metrics**: http://localhost:8000/metrics
- **API Documentation**: http://localhost:8000/docs

## 🎉 Recent Updates

### ✅ **Latest Changes (October 2025):**
1. **Real-time Knowledge Integration**: Tavily Search API integration for current information and general knowledge
2. **Enhanced RAG System**: Combined MCP + Tavily + traditional RAG for comprehensive context
3. **Intelligent Query Routing**: Automatic detection of medical vs. general knowledge queries
4. **Provider Selection**: Configurable `MEDICAL_MODEL_PROVIDER` (groq/xai) with clean primary/fallback flow
5. **Groq-First Configuration**: Default to Groq with `meta-llama/llama-4-maverick-17b-128e-instruct`
6. **Robust Environment Parsing**: Auto-trim quotes/whitespace from `.env` values to prevent "Invalid API Key" errors
7. **Centralized MCP Config**: MCP settings moved to `app/config.py` for consistency across components
8. **Enhanced MCP Context Extraction**: Better recognition of response shapes (`topics`, `articles`, etc.)
9. **Windows curl Guidance**: PowerShell and cmd.exe safe examples for testing
10. **Graceful Error Handling**: Provider failures return friendly JSON with WHO fallback sources (no 500s)
11. **Success Flag Accuracy**: `metadata.success` correctly reflects actual LLM success vs. fallback responses

### 🚀 **Configuration Improvements:**
- Environment variables centralized in Settings with validation
- Provider normalization and string sanitization
- Consistent model selection based on provider choice
- MCP client now reads from centralized settings (no env drift)

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

- [x] **Real-time Knowledge Integration** - Tavily Search API for current information
- [x] **Advanced RAG System** - Combined MCP + Tavily + document retrieval
- [ ] Voice input/output support
- [ ] Additional African languages
- [ ] Mobile app integration
- [ ] Multi-modal support (images, documents)
- [ ] Enhanced caching layer for improved performance
- [ ] Batch processing capabilities
- [ ] Custom knowledge base uploads

## 🚀 Getting Started

The system is **fully functional** and ready for integration! Start by:

1. Setting up your API keys in `.env` (XAI/Groq) and confirming `MCP_BASE_URL`
2. Running the application with `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` (or `--port 8001` if 8000 is busy on Windows)
3. Testing the API at http://localhost:8000/docs
4. Using the chat endpoint `/api/v1/query` with English inputs and reading English responses
5. Keeping translate endpoints for future voice features (no changes needed now)

The HealthLang AI MVP provides a robust foundation for bilingual medical AI applications with production-ready features and comprehensive error handling! 🎉 