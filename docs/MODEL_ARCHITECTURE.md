# Model Architecture

This document explains where and how the translation and medical models are used in HealthLang AI MVP.

## 🏗️ System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    HealthLang AI MVP                            │
├─────────────────────────────────────────────────────────────────┤
│  API Layer (FastAPI)                                            │
│  ├── /translate     ──→ Translation Service                     │
│  ├── /medical       ──→ Medical Analysis Service                │
│  └── /health        ──→ Health Check                            │
├─────────────────────────────────────────────────────────────────┤
│  Service Layer                                                   │
│  ├── Translation Service    │  Medical Analysis Service         │
│  │   ├── translator.py      │  ├── llm_client.py               │
│  │   ├── language_detector.py│  ├── medical_analyzer.py         │
│  │   └── yoruba_processor.py│  └── response_formatter.py        │
│  └── RAG Service            │                                   │
│      ├── embeddings.py      │                                   │
│      ├── vector_store.py    │                                   │
│      ├── document_processor.py│                                 │
│      └── retriever.py       │                                   │
├─────────────────────────────────────────────────────────────────┤
│  Model Layer                                                   │
│  ├── Translation Models     │  Medical Models                   │
│  │   ──→ data/models/translation/│  ──→ data/models/medical/   │
│  └── Embedding Models       │                                   │
│      ──→ data/models/embeddings/│                              │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Translation Model Flow

### 1. **Model Location**
```
data/models/translation/
├── yoruba_english_model.bin    # Main translation model
├── english_yoruba_model.bin    # Reverse translation
├── tokenizer.json             # Tokenizer configuration
├── config.json                # Model configuration
└── vocabulary.txt             # Vocabulary file
```

### 2. **Service Implementation**
**File**: `app/services/translation/translator.py`

```python
class TranslationService:
    def __init__(self):
        self.language_detector: Optional[LanguageDetector] = None
        self.yoruba_processor: Optional[YorubaProcessor] = None
    
    async def translate(
        self,
        text: str,
        source_language: str = "en",
        target_language: str = "yo",
    ) -> str:
        # 1. Detect language if not specified
        # 2. Load appropriate model from data/models/translation/
        # 3. Process Yoruba-specific features
        # 4. Return translated text
```

### 3. **Configuration**
**File**: `app/config.py`
```python
TRANSLATION_MODEL_PATH: str = Field(
    default="./data/models/translation", 
    env="TRANSLATION_MODEL_PATH"
)
DEFAULT_SOURCE_LANGUAGE: str = Field(default="en", env="DEFAULT_SOURCE_LANGUAGE")
DEFAULT_TARGET_LANGUAGE: str = Field(default="yo", env="DEFAULT_TARGET_LANGUAGE")
SUPPORTED_LANGUAGES: List[str] = Field(default=["en", "yo"], env="SUPPORTED_LANGUAGES")
```

### 4. **API Endpoint**
**File**: `app/api/translation.py`
```python
@router.post("/translate")
async def translate_text(request: TranslationRequest):
    # Calls TranslationService.translate()
    # Uses models from data/models/translation/
```

## 🏥 Medical Model Flow

### 1. **Model Configuration**
**File**: `app/config.py`
```python
MEDICAL_MODEL_NAME: str = Field(default="llama-3-8b-8192", env="MEDICAL_MODEL_NAME")
MEDICAL_MODEL_PROVIDER: str = Field(default="groq", env="MEDICAL_MODEL_PROVIDER")
GROQ_MODEL: str = Field(default="llama-3-8b-8192", env="GROQ_MODEL")
OPENAI_MODEL: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
ANTHROPIC_MODEL: str = Field(default="claude-3-sonnet-20240229", env="ANTHROPIC_MODEL")
LOCAL_MODEL: str = Field(default="llama-3-8b", env="LOCAL_MODEL")
```

### 2. **Service Implementation**
**File**: `app/services/medical/llm_client.py`

```python
class LLMClient:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER  # Default: "groq"
        self.models = {
            LLMProvider.GROQ: settings.GROQ_MODEL,      # "llama-3-8b-8192"
            LLMProvider.OPENAI: settings.OPENAI_MODEL,  # "gpt-3.5-turbo"
            LLMProvider.ANTHROPIC: settings.ANTHROPIC_MODEL,
            LLMProvider.LOCAL: settings.LOCAL_MODEL
        }
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        # Routes to appropriate provider:
        # - Groq: Fast LLaMA-3-8B inference
        # - OpenAI: High-quality GPT responses
        # - Anthropic: Claude medical reasoning
        # - Local: Quantized models
```

### 3. **Medical Analysis Service**
**File**: `app/services/medical/medical_analyzer.py`

```python
class MedicalAnalyzer:
    def __init__(self):
        self.llm_client = LLMClient()
        self.rag_service = RAGService()
    
    async def analyze_medical_query(
        self,
        query: str,
        language: str = "en",
        include_rag: bool = True
    ) -> MedicalAnalysis:
        # 1. Use LLMClient to generate medical reasoning
        # 2. Optionally use RAG for additional context
        # 3. Format response with safety warnings
        # 4. Return structured medical analysis
```

### 4. **API Endpoint**
**File**: `app/api/medical.py`
```python
@router.post("/analyze")
async def analyze_medical_query(request: MedicalQueryRequest):
    # Calls MedicalAnalyzer.analyze_medical_query()
    # Uses LLMClient with configured medical models
```

## 🔍 RAG Model Flow

### 1. **Embedding Models**
**Location**: `data/models/embeddings/`
**Configuration**: `app/config.py`
```python
EMBEDDING_MODEL: str = Field(
    default="sentence-transformers/all-MiniLM-L6-v2", 
    env="EMBEDDING_MODEL"
)
```

### 2. **Service Implementation**
**File**: `app/services/rag/embeddings.py`
```python
class EmbeddingService:
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self.model = SentenceTransformer(self.model_name)
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        # Generate vector embeddings for RAG retrieval
```

## 📊 Model Usage Summary

| Model Type | Location | Service | Provider | Purpose |
|------------|----------|---------|----------|---------|
| **Translation** | `data/models/translation/` | `TranslationService` | Local/Cloud | Yoruba ↔ English |
| **Medical** | Cloud APIs | `LLMClient` | Groq/OpenAI/Anthropic | Medical reasoning |
| **Embeddings** | `data/models/embeddings/` | `EmbeddingService` | Sentence Transformers | RAG vector search |

## 🚀 Model Initialization

### Translation Models
```python
# In app/services/translation/translator.py
async def initialize(self) -> None:
    # Load models from data/models/translation/
    self.language_detector = LanguageDetector()
    self.yoruba_processor = YorubaProcessor()
```

### Medical Models
```python
# In app/services/medical/llm_client.py
def _initialize_clients(self):
    # Initialize API clients for cloud models
    if settings.GROQ_API_KEY:
        self.clients[LLMProvider.GROQ] = AsyncGroq(api_key=settings.GROQ_API_KEY)
    if settings.OPENAI_API_KEY:
        self.clients[LLMProvider.OPENAI] = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
```

### Embedding Models
```python
# In app/services/rag/embeddings.py
def __init__(self):
    # Load embedding model from HuggingFace
    self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
```

## 🔧 Environment Configuration

**File**: `.env`
```bash
# Translation Models
TRANSLATION_MODEL_PATH=./data/models/translation

# Medical Models
MEDICAL_MODEL_NAME=llama-3-8b-8192
MEDICAL_MODEL_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Embedding Models
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## 📈 Performance Characteristics

| Model Type | Latency | Throughput | Quality | Cost |
|------------|---------|------------|---------|------|
| **Translation** | ~100ms | High | Good | Low |
| **Medical (Groq)** | ~2-5s | Medium | Good | Medium |
| **Medical (OpenAI)** | ~5-10s | Low | Excellent | High |
| **Embeddings** | ~50ms | High | Good | Low |

This architecture ensures that:
- **Translation models** are optimized for speed and accuracy
- **Medical models** provide high-quality reasoning with safety checks
- **Embedding models** enable efficient RAG retrieval
- All models are properly configured and managed 