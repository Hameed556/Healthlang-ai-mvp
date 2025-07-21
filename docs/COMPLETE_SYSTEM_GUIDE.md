# HealthLang AI MVP - Complete System Guide

This comprehensive guide explains every folder and file in the HealthLang AI MVP system, their functions, and how they work together to create a bilingual medical Q&A system.

## 🏗️ **System Overview**

HealthLang AI MVP is a **bilingual medical Q&A system** that combines:
- **Translation Service**: Yoruba ↔ English bidirectional translation
- **Medical Analysis**: LLM-powered medical reasoning with Groq
- **RAG System**: Retrieval-augmented generation from trusted medical sources
- **API Interface**: FastAPI REST API for easy integration
- **Language Matching**: Responses match input language by default with optional translation

## 📁 **Root Directory Structure**

```
Healthlang-ai-mvp/
├── 📁 app/                    # Main application code
├── 📁 docs/                   # Documentation
├── 📁 data/                   # Data storage and models
├── 📁 scripts/                # Setup and utility scripts
├── 📁 deployment/             # Deployment configurations
├── 📁 monitoring/             # Monitoring and logging
├── 📁 tests/                  # Test files
├── 📄 README.md               # Project overview
├── 📄 render.yaml             # Render deployment config
├── 📄 requirements.txt        # Python dependencies
├── 📄 pyproject.toml          # Project metadata
├── 📄 setup.py                # Package setup
├── 📄 Dockerfile              # Docker container
├── 📄 docker-compose.yml      # Docker orchestration
├── 📄 Makefile                # Build automation
├── 📄 .gitignore              # Git ignore rules
└── 📄 env.example             # Environment template
```

---

## 🎯 **1. MAIN APPLICATION FOLDER: `/app/`**

The `/app/` folder contains the core application logic, organized in a clean, modular structure.

### **📄 `app/__init__.py`**
**Purpose**: Python package initialization
**Function**: Makes the `app` directory a Python package
**Content**: Package metadata and version information

### **📄 `app/main.py`** ⭐ **ENTRY POINT**
**Purpose**: Application entry point and FastAPI setup
**Key Functions**:
- **FastAPI Application Creation**: Sets up the web server
- **Lifespan Management**: Handles startup/shutdown of services
- **Middleware Setup**: CORS, logging, rate limiting
- **Route Registration**: Connects API endpoints
- **Exception Handling**: Global error handling
- **Metrics Setup**: Prometheus monitoring

**How it works**:
```python
# Startup: Initialize all services
translation_service = TranslationService()
llm_client = GroqLLMClient()
vector_store = VectorStore()

# Runtime: Handle requests through API routes
app.include_router(query.router, prefix="/api/v1")
app.include_router(translation.router, prefix="/api/v1")

# Shutdown: Clean up resources
await translation_service.cleanup()
await llm_client.cleanup()
```

### **📄 `app/config.py`** ⭐ **CONFIGURATION CENTER**
**Purpose**: Central configuration management
**Key Functions**:
- **Environment Variables**: Load from `.env` files
- **API Keys**: Groq, OpenAI, Anthropic
- **Model Settings**: LLM parameters, RAG settings
- **Performance Tuning**: Token limits, cache settings
- **Deployment Settings**: Host, port, workers

**Optimized Settings for Render**:
```python
MAX_TOKENS = 2048              # Reduced for speed
MAX_RETRIEVAL_DOCS = 3         # Fewer docs for speed
SIMILARITY_THRESHOLD = 0.75    # Higher threshold
CACHE_TTL = 7200               # 2-hour cache
RATE_LIMIT_PER_MINUTE = 120    # Increased limits
```

---

## 🧠 **2. CORE LOGIC: `/app/core/`**

### **📄 `app/core/pipeline.py`** ⭐ **MAIN PROCESSING ENGINE**
**Purpose**: Orchestrates the complete medical query processing pipeline
**Key Functions**:
- **Query Processing**: Main `process_query()` method
- **Language Matching**: Automatic language detection and matching
- **Optional Translation**: Translate only when requested
- **RAG Integration**: Document retrieval and context building
- **Medical Analysis**: LLM-powered medical reasoning
- **Response Formatting**: Structured output generation
- **Caching**: Result caching for performance

**Processing Flow**:
```python
async def process_query(self, text, source_language, target_language=None, translate_response=False):
    # 1. Set target language to match source if not specified
    if target_language is None:
        target_language = source_language
    
    # 2. Check cache for existing results
    cached_result = await self._check_cache(context)
    
    # 3. Translate query if needed (only if different languages)
    await self._translate_query(context)
    
    # 4. Retrieve relevant medical documents (RAG)
    await self._retrieve_relevant_documents(context)
    
    # 5. Perform medical analysis with LLM
    await self._analyze_medical_query(context)
    
    # 6. Format response with optional translation
    await self._format_response(context, translate_response)
    
    # 7. Cache the result
    await self._cache_result(context)
```

**Language Matching Logic**:
- **Yoruba Input** → **Yoruba Response** (default)
- **English Input** → **English Response** (default)
- **Translation** only when `translate_response=True`

---

## 🔧 **3. SERVICES: `/app/services/`**

The services folder contains the core business logic components.

### **📁 `/app/services/translation/`** 🌐 **TRANSLATION SERVICE**

#### **📄 `translator.py`**
**Purpose**: Yoruba ↔ English bidirectional translation
**Key Functions**:
- **Language Detection**: Auto-detect input language
- **Bidirectional Translation**: Yoruba ↔ English
- **Quality Assessment**: Translation quality scoring
- **Batch Processing**: Handle multiple translations
- **Model Integration**: LLaMA-4 Maverick via Groq

**Usage**:
```python
# Initialize translation service
translation_service = TranslationService()

# Translate Yoruba to English
english_text = await translation_service.translate(
    text="Kini awọn aami diabetes?",
    source_language="yo",
    target_language="en"
)

# Translate English to Yoruba
yoruba_text = await translation_service.translate(
    text="What are the symptoms of diabetes?",
    source_language="en",
    target_language="yo"
)
```

### **📁 `/app/services/medical/`** 🏥 **MEDICAL ANALYSIS SERVICE**

#### **📄 `medical_analyzer.py`**
**Purpose**: Medical reasoning and diagnosis assistance
**Key Functions**:
- **Medical Analysis**: LLM-powered medical reasoning
- **Safety Checks**: Emergency detection and warnings
- **Structured Output**: Formatted medical responses
- **Context Integration**: Use RAG documents for accuracy
- **Model Management**: Groq LLM integration

#### **📄 `llm_client.py`**
**Purpose**: LLM client management and communication
**Key Functions**:
- **Model Selection**: Choose between Groq, OpenAI, Anthropic
- **Request Handling**: Manage API calls and responses
- **Error Handling**: Retry logic and fallback options
- **Performance Optimization**: Connection pooling and caching

**LLM Configuration**:
```python
# Primary: Groq with LLaMA-3-8B (fast)
llm_client = GroqLLMClient(
    model="llama-3-8b-8192",
    temperature=0.1,
    max_tokens=2048
)

# Backup: OpenAI GPT-3.5 (reliable)
openai_client = OpenAIClient(
    model="gpt-3.5-turbo",
    temperature=0.1
)
```

### **📁 `/app/services/rag/`** 📚 **RAG (RETRIEVAL-AUGMENTED GENERATION) SERVICE**

#### **📄 `retriever.py`**
**Purpose**: Document retrieval and context building
**Key Functions**:
- **Query Processing**: Convert queries to embeddings
- **Vector Search**: Find similar documents in vector database
- **Relevance Scoring**: Rank documents by similarity
- **Context Building**: Prepare context for LLM
- **Source Attribution**: Track document sources

#### **📄 `document_processor.py`**
**Purpose**: Process and prepare medical documents
**Key Functions**:
- **Text Extraction**: Extract text from PDFs, DOCX, etc.
- **Chunking**: Split documents into manageable chunks
- **Embedding Generation**: Create vector embeddings
- **Metadata Extraction**: Extract source, date, author info
- **Quality Filtering**: Remove low-quality content

#### **📄 `vector_store.py`**
**Purpose**: Vector database management
**Key Functions**:
- **Database Operations**: CRUD operations for vectors
- **Similarity Search**: Find similar documents
- **Index Management**: Optimize search performance
- **Persistence**: Save and load vector data
- **Backup/Restore**: Data management operations

**RAG Process**:
```python
# 1. Process query
query_embedding = generate_embedding("What are diabetes symptoms?")

# 2. Search vector database
similar_docs = vector_store.search(
    query_embedding,
    max_results=3,
    similarity_threshold=0.75
)

# 3. Build context
context = build_context(similar_docs)

# 4. Send to LLM with context
response = llm_client.analyze(query, context)
```

---

## 🌐 **4. API LAYER: `/app/api/`**

### **📁 `/app/api/routes/`** 🛣️ **API ENDPOINTS**

#### **📄 `query.py`** ⭐ **MAIN QUERY ENDPOINT**
**Purpose**: Handle medical query requests
**Key Functions**:
- **Request Validation**: Validate input parameters
- **Pipeline Integration**: Connect to processing pipeline
- **Response Formatting**: Structure API responses
- **Error Handling**: Handle and format errors
- **Metrics Collection**: Track usage and performance

**API Endpoints**:
```python
# Main medical query endpoint
POST /api/v1/query
{
    "text": "What are the symptoms of diabetes?",
    "source_language": "en",
    "target_language": null,  # Optional: defaults to source_language
    "translate_response": false,  # Optional: force translation
    "use_cache": true,
    "include_sources": true
}

# Query status endpoint
GET /api/v1/query/{request_id}

# Batch query endpoint
POST /api/v1/query/batch

# Supported languages
GET /api/v1/supported-languages

# Query statistics
GET /api/v1/query-stats
```

#### **📄 `translation.py`**
**Purpose**: Standalone translation endpoints
**Key Functions**:
- **Direct Translation**: Translate text without medical analysis
- **Language Detection**: Auto-detect input language
- **Batch Translation**: Handle multiple translations
- **Quality Assessment**: Translation quality metrics

#### **📄 `health.py`**
**Purpose**: Health check and monitoring endpoints
**Key Functions**:
- **Service Health**: Check all service status
- **Dependency Health**: Database, LLM, RAG status
- **Performance Metrics**: Response times, error rates
- **System Information**: Version, configuration info

---

## 📊 **5. DATA MANAGEMENT: `/data/`**

### **📁 `/data/medical_knowledge/`** 📚 **MEDICAL KNOWLEDGE BASE**

#### **📁 `raw/`**
**Purpose**: Raw medical documents
**Content**:
- **WHO Guidelines**: World Health Organization documents
- **CDC Guidelines**: Centers for Disease Control documents
- **PubMed Papers**: Medical research papers
- **Medical Textbooks**: Standard medical references
- **Local Health Guidelines**: Regional health information

#### **📁 `processed/`**
**Purpose**: Processed and cleaned medical documents
**Content**:
- **Cleaned Text**: Extracted and cleaned text content
- **Structured Data**: Organized medical information
- **Metadata**: Source, date, author information
- **Quality Scores**: Content quality assessments

#### **📁 `embeddings/`**
**Purpose**: Vector embeddings for RAG
**Content**:
- **Document Embeddings**: Vector representations of documents
- **Chunk Embeddings**: Vector representations of text chunks
- **Index Files**: Search optimization files
- **Metadata**: Embedding metadata and mappings

### **📁 `/data/models/`** 🤖 **AI MODELS**

#### **📁 `translation/`**
**Purpose**: Translation model files
**Content**:
- **Yoruba-English Models**: Fine-tuned translation models
- **English-Yoruba Models**: Reverse translation models
- **Vocabulary Files**: Language vocabulary and mappings
- **Configuration Files**: Model parameters and settings

---

## 🛠️ **6. UTILITIES: `/app/utils/`**

### **📄 `logger.py`**
**Purpose**: Centralized logging system
**Key Functions**:
- **Structured Logging**: JSON-formatted logs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR
- **Request Tracking**: Track requests across services
- **Performance Logging**: Log response times and metrics

### **📄 `metrics.py`**
**Purpose**: Performance monitoring and metrics
**Key Functions**:
- **Prometheus Integration**: Metrics collection
- **Custom Metrics**: Query counts, response times
- **Health Metrics**: Service health indicators
- **Business Metrics**: Usage and performance data

### **📄 `exceptions.py`**
**Purpose**: Custom exception handling
**Key Functions**:
- **Custom Exceptions**: HealthLang-specific errors
- **Error Codes**: Standardized error codes
- **Error Messages**: User-friendly error messages
- **Error Handling**: Centralized error management

---

## 📜 **7. SCRIPTS: `/scripts/`**

### **📄 `setup_database.py`**
**Purpose**: Initialize databases and data structures
**Key Functions**:
- **Database Creation**: Create SQLite database
- **Table Setup**: Create necessary tables
- **Index Creation**: Optimize database performance
- **Initial Data**: Load initial configuration data

### **📄 `download_models.py`**
**Purpose**: Download and setup AI models
**Key Functions**:
- **Model Download**: Download translation models
- **Model Verification**: Verify model integrity
- **Model Setup**: Configure model parameters
- **Cache Management**: Manage model cache

### **📄 `process_medical_data.py`**
**Purpose**: Process medical documents for RAG
**Key Functions**:
- **Document Processing**: Extract text from documents
- **Embedding Generation**: Create vector embeddings
- **Quality Assessment**: Assess document quality
- **Index Building**: Build search indexes

---

## 🚀 **8. DEPLOYMENT: `/deployment/`**

### **📄 `Dockerfile`** 🐳 **DOCKER CONTAINER**
**Purpose**: Containerize the application
**Key Functions**:
- **Base Image**: Python 3.11 slim image
- **Dependencies**: Install Python packages
- **Application Setup**: Copy and configure application
- **Runtime Configuration**: Set up runtime environment
- **Health Checks**: Container health monitoring

### **📄 `docker-compose.yml`** 🐙 **DOCKER ORCHESTRATION**
**Purpose**: Multi-service deployment
**Key Functions**:
- **Service Definition**: Define all services
- **Network Configuration**: Service communication
- **Volume Management**: Persistent data storage
- **Environment Variables**: Configuration management
- **Health Monitoring**: Service health checks

### **📄 `render.yaml`** ☁️ **RENDER DEPLOYMENT**
**Purpose**: Render cloud deployment configuration
**Key Functions**:
- **Service Configuration**: Web service setup
- **Environment Variables**: Production configuration
- **Resource Allocation**: CPU, memory allocation
- **Health Checks**: Application health monitoring
- **Auto-deployment**: Continuous deployment setup

---

## 📊 **9. MONITORING: `/monitoring/`**

### **📄 `prometheus.yml`**
**Purpose**: Prometheus monitoring configuration
**Key Functions**:
- **Metrics Collection**: Define metrics to collect
- **Scraping Rules**: How often to collect metrics
- **Alert Rules**: Define alert conditions
- **Service Discovery**: Auto-discover services

### **📄 `grafana/`**
**Purpose**: Grafana dashboard configurations
**Key Functions**:
- **Dashboard Templates**: Pre-built dashboards
- **Query Templates**: Common monitoring queries
- **Alert Configurations**: Alert setup and rules
- **Visualization**: Charts and graphs setup

---

## 🧪 **10. TESTING: `/tests/`**

### **📁 `unit/`**
**Purpose**: Unit tests for individual components
**Content**:
- **Service Tests**: Test individual services
- **Utility Tests**: Test utility functions
- **Model Tests**: Test data models
- **Configuration Tests**: Test configuration loading

### **📁 `integration/`**
**Purpose**: Integration tests for component interactions
**Content**:
- **Pipeline Tests**: Test complete processing pipeline
- **API Tests**: Test API endpoints
- **Database Tests**: Test database operations
- **External Service Tests**: Test external API calls

### **📁 `performance/`**
**Purpose**: Performance and load testing
**Content**:
- **Load Tests**: High-load testing
- **Stress Tests**: Stress testing scenarios
- **Benchmark Tests**: Performance benchmarks
- **Memory Tests**: Memory usage testing

---

## 📋 **11. CONFIGURATION FILES**

### **📄 `requirements.txt`** 📦 **PYTHON DEPENDENCIES**
**Purpose**: List all Python package dependencies
**Key Dependencies**:
```txt
fastapi==0.104.1          # Web framework
uvicorn==0.24.0           # ASGI server
groq==0.4.2               # Groq LLM client
openai==1.3.7             # OpenAI client
chromadb==0.4.18          # Vector database
sentence-transformers==2.2.2  # Text embeddings
prometheus-client==0.19.0 # Metrics collection
redis==5.0.1              # Caching
```

### **📄 `pyproject.toml`** 📋 **PROJECT METADATA**
**Purpose**: Project configuration and metadata
**Key Information**:
- **Project Name**: HealthLang AI MVP
- **Version**: 0.1.0
- **Description**: Bilingual medical Q&A system
- **Dependencies**: Development and runtime dependencies
- **Build Configuration**: Package build settings

### **📄 `setup.py`** 🔧 **PACKAGE SETUP**
**Purpose**: Python package installation configuration
**Key Functions**:
- **Package Definition**: Define package structure
- **Dependency Management**: Handle dependencies
- **Installation Scripts**: Custom installation steps
- **Metadata**: Package metadata and information

### **📄 `Makefile`** 🔨 **BUILD AUTOMATION**
**Purpose**: Automate common development tasks
**Key Commands**:
```makefile
make install      # Install dependencies
make test         # Run all tests
make build        # Build Docker image
make deploy       # Deploy to production
make clean        # Clean build artifacts
make docs         # Generate documentation
```

### **📄 `.gitignore`** 🚫 **GIT IGNORE RULES**
**Purpose**: Exclude files from version control
**Ignored Files**:
- **Environment Files**: `.env`, `.env.local`
- **Cache Directories**: `__pycache__/`, `.pytest_cache/`
- **Build Artifacts**: `dist/`, `build/`
- **Log Files**: `*.log`
- **Data Files**: Large data files and models

### **📄 `env.example`** 📝 **ENVIRONMENT TEMPLATE**
**Purpose**: Template for environment variables
**Key Variables**:
```bash
# API Keys
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Application Settings
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Performance Settings
MAX_TOKENS=2048
MAX_RETRIEVAL_DOCS=3
CACHE_TTL=7200
```

---

## 🔄 **12. HOW EVERYTHING WORKS TOGETHER**

### **Request Flow**:
```
1. User Request → app/main.py (FastAPI)
2. Route Handler → app/api/routes/query.py
3. Request Validation → Pydantic models
4. Pipeline Processing → app/core/pipeline.py
5. Translation Service → app/services/translation/
6. RAG Retrieval → app/services/rag/
7. Medical Analysis → app/services/medical/
8. Response Formatting → Pipeline
9. Caching → Redis/Memory cache
10. Response → User
```

### **Data Flow**:
```
Raw Documents → /data/medical_knowledge/raw/
    ↓
Document Processing → /scripts/process_medical_data.py
    ↓
Processed Documents → /data/medical_knowledge/processed/
    ↓
Embedding Generation → app/services/rag/document_processor.py
    ↓
Vector Storage → /data/medical_knowledge/embeddings/
    ↓
RAG Retrieval → app/services/rag/retriever.py
    ↓
LLM Analysis → app/services/medical/medical_analyzer.py
    ↓
Response Generation → app/core/pipeline.py
```

### **Configuration Flow**:
```
Environment Variables → app/config.py
    ↓
Service Configuration → Individual services
    ↓
Runtime Settings → Application behavior
    ↓
Performance Tuning → Response optimization
```

### **Monitoring Flow**:
```
Application Metrics → app/utils/metrics.py
    ↓
Prometheus Collection → /monitoring/prometheus.yml
    ↓
Grafana Visualization → /monitoring/grafana/
    ↓
Health Checks → app/api/routes/health.py
    ↓
Alerting → Monitoring dashboards
```

---

## 🎯 **13. KEY INTEGRATION POINTS**

### **Language Matching Integration**:
- **Pipeline**: `app/core/pipeline.py` handles language matching logic
- **API**: `app/api/routes/query.py` accepts optional translation parameters
- **Translation**: `app/services/translation/` provides translation when needed
- **Response**: Formatted responses match input language by default

### **Performance Optimization Integration**:
- **Configuration**: `app/config.py` contains optimized settings
- **Caching**: Pipeline and services use caching for speed
- **RAG**: Optimized document retrieval (3 docs, 0.75 threshold)
- **LLM**: Reduced token limits (2048) for faster responses

### **Render Deployment Integration**:
- **Configuration**: `render.yaml` contains deployment settings
- **Environment**: Production-optimized environment variables
- **Health Checks**: `/health` endpoint for monitoring
- **Scaling**: Single worker configuration for starter plan

---

## 🚀 **14. DEPLOYMENT READINESS**

### **Production Checklist**:
- ✅ **Language Matching**: Implemented and tested
- ✅ **Performance Optimization**: Configured for speed
- ✅ **Render Configuration**: Complete deployment setup
- ✅ **Monitoring**: Health checks and metrics
- ✅ **Documentation**: Comprehensive guides
- ✅ **Testing**: Unit and integration tests
- ✅ **Error Handling**: Robust error management
- ✅ **Caching**: Performance optimization
- ✅ **Security**: Environment variable management
- ✅ **Scalability**: Designed for growth

### **Ready for Render Deployment**:
1. **Push to GitHub** with all files
2. **Connect to Render** using `render.yaml`
3. **Set API Keys** in Render dashboard
4. **Deploy** and monitor health checks
5. **Test** language matching and translation
6. **Monitor** performance and usage

The entire system is designed to work together seamlessly, providing fast, accurate, and culturally appropriate medical information in both English and Yoruba! 🎉 