# Models Directory

This directory contains all the machine learning models used by HealthLang AI MVP.

## Directory Structure

```
data/models/
├── translation/          # Translation models (Yoruba ↔ English)
├── medical/             # Medical analysis models
├── embeddings/          # Embedding models for RAG
└── README.md           # This file
```

## Model Locations

### 1. Translation Models (`translation/`)
**Purpose**: Handle Yoruba-English bidirectional translation
**Location**: `data/models/translation/`
**Configuration**: `app/config.py` → `TRANSLATION_MODEL_PATH`
**Service**: `app/services/translation/translator.py`

**Models Used**:
- **Primary**: Fine-tuned T5 or MarianMT for Yoruba-English
- **Fallback**: Google Translate API or OpenAI GPT for translation
- **Language Detection**: FastText or spaCy language detection models

**Files**:
- `yoruba_english_model.bin` - Main translation model
- `english_yoruba_model.bin` - Reverse translation model
- `tokenizer.json` - Tokenizer configuration
- `config.json` - Model configuration
- `vocabulary.txt` - Vocabulary file

### 2. Medical Analysis Models (`medical/`)
**Purpose**: Medical reasoning and diagnosis assistance
**Location**: `data/models/medical/`
**Configuration**: `app/config.py` → `MEDICAL_MODEL_NAME`, `MEDICAL_MODEL_PROVIDER`
**Service**: `app/services/medical/llm_client.py`

**Models Used**:
- **Primary**: LLaMA-3-8B via Groq (fast inference)
- **Alternative**: GPT-4 via OpenAI (higher quality)
- **Local**: Quantized LLaMA-3-8B for offline use
- **Medical-Specific**: Fine-tuned medical reasoning models

**Configuration**:
```python
# In app/config.py
MEDICAL_MODEL_NAME = "llama-3-8b-8192"  # Default model
MEDICAL_MODEL_PROVIDER = "groq"         # Default provider
GROQ_MODEL = "llama-3-8b-8192"         # Groq model name
OPENAI_MODEL = "gpt-3.5-turbo"         # OpenAI model name
```

### 3. Embedding Models (`embeddings/`)
**Purpose**: Generate vector embeddings for RAG system
**Location**: `data/models/embeddings/`
**Configuration**: `app/config.py` → `EMBEDDING_MODEL`
**Service**: `app/services/rag/embeddings.py`

**Models Used**:
- **Primary**: `sentence-transformers/all-MiniLM-L6-v2` (fast, good quality)
- **Alternative**: `sentence-transformers/all-mpnet-base-v2` (higher quality)
- **Medical-Specific**: Fine-tuned medical embeddings

## Model Management

### Downloading Models
```bash
# Download translation models
make download-translation-models

# Download medical models (if using local models)
make download-medical-models

# Download embedding models
make download-embedding-models
```

### Updating Models
```bash
# Update all models
make update-models

# Update specific model type
make update-translation-models
make update-medical-models
make update-embedding-models
```

### Model Configuration
Models are configured via environment variables in `.env`:
```bash
# Translation
TRANSLATION_MODEL_PATH=./data/models/translation

# Medical Analysis
MEDICAL_MODEL_NAME=llama-3-8b-8192
MEDICAL_MODEL_PROVIDER=groq

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## Model Providers

### Translation Models
1. **Local Models**: Fine-tuned T5/MarianMT models
2. **Cloud APIs**: Google Translate, OpenAI GPT
3. **Hybrid**: Local + cloud fallback

### Medical Models
1. **Groq**: Fast inference with LLaMA-3-8B
2. **OpenAI**: High-quality GPT-4 responses
3. **Anthropic**: Claude for medical reasoning
4. **Local**: Quantized models for offline use

### Embedding Models
1. **Sentence Transformers**: Local embedding generation
2. **OpenAI**: Text-embedding-ada-002
3. **Cohere**: Embed models

## Performance Considerations

- **Translation**: ~100ms per sentence
- **Medical Analysis**: ~2-5 seconds per query
- **Embeddings**: ~50ms per document chunk
- **RAG Retrieval**: ~200ms per query

## Security & Privacy

- All models run locally when possible
- API keys stored securely in environment variables
- No sensitive data sent to external services without consent
- Model outputs validated for medical accuracy 