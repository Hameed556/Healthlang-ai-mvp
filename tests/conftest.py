"""
Pytest configuration and fixtures for HealthLang AI MVP tests.
"""

import pytest
import pytest_asyncio
import asyncio
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.config import settings  # noqa: F401
from app.models.database_models import Base


# Test database configuration
TEST_DATABASE_URL = "sqlite:///./test_healthlang.db"

# Create test database engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db():
    """Create test database and tables."""
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session(test_db):
    """Create a new database session for a test."""
    connection = test_db.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session) -> Generator:
    """Create a test client for the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    class MockSettings:
        GROQ_API_KEY = "test_groq_key"
        SECRET_KEY = "test_secret_key"
        DEBUG = True
        TESTING = True
        DATABASE_URL = TEST_DATABASE_URL
        REDIS_URL = "redis://localhost:6379/1"
        CHROMA_PERSIST_DIRECTORY = "./test_data/chroma"
        EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
        VECTOR_STORE_TYPE = "chroma"
        RAG_ENABLED = True
        RATE_LIMIT_PER_MINUTE = 100
        RATE_LIMIT_PER_HOUR = 1000
        CORS_ORIGINS = ["http://localhost:3000"]
        LOG_LEVEL = "DEBUG"
        PROMETHEUS_ENABLED = False
    
    return MockSettings()


@pytest.fixture
def sample_medical_query():
    """Sample medical query for testing."""
    return {
        "query": "What are the symptoms of diabetes?",
        "language": "en",
        "query_type": "symptom_analysis",
        "context": {"user_age": 45, "user_gender": "female"},
        "output_format": "json"
    }


@pytest.fixture
def sample_translation_request():
    """Sample translation request for testing."""
    return {
        "text": "Hello, how are you?",
        "source_language": "en",
        "target_language": "yo",
        "context": "greeting",
        "preserve_formatting": True
    }


@pytest.fixture
def sample_document():
    """Sample document for RAG testing."""
    return {
        "id": "test_doc_001",
        "content": (
            "Diabetes is a chronic disease that affects how your body turns "
            "food into energy."
        ),
        "metadata": {
            "title": "Diabetes Information",
            "source": "WHO Guidelines",
            "language": "en",
            "type": "medical_guideline"
        },
        "source": "who_diabetes_guidelines.pdf"
    }


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return {
        "content": (
            "Diabetes symptoms include increased thirst, frequent urination, "
            "and fatigue."
        ),
        "model": "llama-3-8b-8192",
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 25,
            "total_tokens": 75
        },
        "finish_reason": "stop",
        "response_time": 1.5,
        "provider": "groq"
    }


@pytest.fixture
def mock_embedding_response():
    """Mock embedding response for testing."""
    return {
        # 100-dimensional vector
        "embeddings": [[0.1, 0.2, 0.3, 0.4, 0.5] * 20],
        "model": "all-MiniLM-L6-v2",
        "dimensions": 100,
        "generation_time": 0.1,
        "metadata": {
            "device": "cpu",
            "normalized": True,
            "batch_size": 1
        }
    }


@pytest.fixture
def mock_vector_search_response():
    """Mock vector search response for testing."""
    return {
        "results": [
            {
                "document": {
                    "id": "doc_001",
                    "content": (
                        "Diabetes symptoms include increased thirst and "
                        "frequent urination."
                    ),
                    "metadata": {"source": "WHO", "type": "medical"}
                },
                "similarity_score": 0.85,
                "rank": 1
            }
        ],
        "total_results": 1,
        "search_time": 0.05,
        "metadata": {
            "collection": "medical_docs",
            "similarity_threshold": 0.5
        }
    }


@pytest.fixture
def test_user_data():
    """Test user data for authentication tests."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "preferred_language": "en"
    }


@pytest.fixture
def auth_headers():
    """Authentication headers for protected endpoints."""
    return {
        "Authorization": "Bearer test_access_token",
        "Content-Type": "application/json"
    }


# Async fixtures for async tests
@pytest_asyncio.fixture
async def async_client():
    """Async test client."""
    from httpx import AsyncClient
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        yield client


@pytest.fixture
async def mock_embedding_service():
    """Mock embedding service for testing."""
    class MockEmbeddingService:
        async def generate_single_embedding(self, text: str) -> list:
            return [0.1] * 100  # Return 100-dimensional vector
        
        async def generate_batch_embeddings(self, texts: list) -> list:
            return [[0.1] * 100 for _ in texts]
        
        async def health_check(self) -> dict:
            return {"status": "healthy", "model": "test_model"}
    
    return MockEmbeddingService()


@pytest.fixture
async def mock_vector_store():
    """Mock vector store for testing."""
    class MockVectorStore:
        async def search(self, request):
            return {
                "results": [
                    {
                        "document": {
                            "id": "test_doc",
                            "content": "Test content",
                            "metadata": {}
                        },
                        "similarity_score": 0.8,
                        "rank": 1
                    }
                ],
                "total_results": 1,
                "search_time": 0.1,
                "metadata": {}
            }
        
        async def health_check(self) -> dict:
            return {"status": "healthy", "store_type": "test"}
    
    return MockVectorStore()


@pytest.fixture
async def mock_llm_client():
    """Mock LLM client for testing."""
    class MockLLMClient:
        async def generate(self, request):
            return {
                "content": "Mock LLM response",
                "model": "test_model",
                "usage": {"total_tokens": 50},
                "finish_reason": "stop",
                "response_time": 1.0,
                "provider": "test"
            }
        
        async def health_check(self) -> dict:
            return {"status": "healthy", "provider": "test"}
    
    return MockLLMClient()
