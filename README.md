# HealthLang AI MVP

A bilingual (Yoruba-English) medical Q&A system powered by Groq-accelerated LLMs with RAG integration from trusted medical sources.

## 🚀 Features

- **Bilingual Support**: Yoruba ↔ English translation and medical Q&A
- **Medical Intelligence**: Lightweight medical reasoning via Groq + LLaMA
- **RAG Integration**: Retrieval-augmented generation from trusted medical sources
- **Fast Performance**: Groq LPU acceleration for real-time responses
- **Production Ready**: FastAPI + Docker deployment with comprehensive testing

## 🏗️ Architecture

```
User Query (Yoruba/English) 
    ↓
Translation Service (Yoruba ↔ English)
    ↓
Medical RAG Pipeline
    ↓
Groq LLM Processing
    ↓
Response Generation & Translation
    ↓
Formatted Medical Answer
```

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **LLM**: Groq + LLaMA models
- **Translation**: Fine-tuned Yoruba-English models
- **Vector DB**: Chroma/FAISS for medical knowledge
- **Deployment**: Docker, Kubernetes
- **Monitoring**: Prometheus, Grafana

## 📦 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Groq API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd healthlang-ai-mvp
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Groq API key and other settings
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the system**
   ```bash
   python scripts/setup_database.py
   python scripts/download_models.py
   python scripts/process_medical_data.py
   ```

5. **Run the application**
   ```bash
   # Development
   uvicorn app.main:app --reload
   
   # Production with Docker
   docker-compose up -d
   ```

## 📚 API Documentation

Once running, visit:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Example Usage

```python
import requests

# English query → English response (default)
response = requests.post("http://localhost:8000/api/v1/query", json={
    "text": "What are the symptoms of diabetes?",
    "source_language": "en"
})

# Yoruba query → Yoruba response (default)
response = requests.post("http://localhost:8000/api/v1/query", json={
    "text": "Kini awọn aami diabetes?",
    "source_language": "yo"
})

# Optional translation: English → Yoruba
response = requests.post("http://localhost:8000/api/v1/query", json={
    "text": "What are the symptoms of diabetes?",
    "source_language": "en",
    "target_language": "yo",
    "translate_response": True
})

print(response.json())
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/
```

## 📊 Monitoring

- **Metrics**: http://localhost:9090 (Prometheus)
- **Dashboards**: http://localhost:3000 (Grafana)

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
- Check the [documentation](docs/)
- Review the [deployment guide](docs/DEPLOYMENT_GUIDE.md)

## 🔮 Roadmap

- [ ] Voice input/output support
- [ ] Additional African languages
- [ ] Mobile app integration
- [ ] Advanced medical reasoning
- [ ] Multi-modal support (images, documents) 