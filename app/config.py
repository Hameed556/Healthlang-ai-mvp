"""
Configuration settings for HealthLang AI MVP
"""

import os
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Application Configuration
    APP_NAME: str = Field(default="HealthLang AI MVP", env="APP_NAME")
    APP_VERSION: str = Field(default="0.1.0", env="APP_VERSION")
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # Server Configuration
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=1, env="WORKERS")
    RELOAD: bool = Field(default=False, env="RELOAD")
    
    # API Keys and External Services
    GROQ_API_KEY: str = Field(default="test_api_key_for_development", env="GROQ_API_KEY")
    XAI_GROK_API_KEY: str = Field(default="test_api_key_for_development", env="XAI_GROK_API_KEY")
    GROQ_BASE_URL: str = Field(default="https://api.groq.com/openai/v1", env="GROQ_BASE_URL")
    XAI_GROK_BASE_URL: str = Field(default="https://api.x.ai/v1", env="XAI_GROK_BASE_URL")
    LOCAL_MODEL_ENDPOINT: Optional[str] = Field(default=None, env="LOCAL_MODEL_ENDPOINT")
    
    # LLM Configuration
    LLM_PROVIDER: str = Field(default="groq", env="LLM_PROVIDER")
    GROQ_MODEL: str = Field(default="meta-llama/llama-4-maverick-17b-128e-instruct", env="GROQ_MODEL")
    OPENAI_MODEL: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    LOCAL_MODEL: str = Field(default="llama-3-8b", env="LOCAL_MODEL")
    LLM_TIMEOUT: int = Field(default=30, env="LLM_TIMEOUT")
    
    # GPU Configuration
    USE_GPU: bool = Field(default=False, env="USE_GPU")
    USE_MPS: bool = Field(default=False, env="USE_MPS")
    
    # Additional Embedding Models
    ADDITIONAL_EMBEDDING_MODELS: List[str] = Field(default=[], env="ADDITIONAL_EMBEDDING_MODELS")
    
    @field_validator("ADDITIONAL_EMBEDDING_MODELS", mode="before")
    @classmethod
    def parse_additional_embedding_models(cls, v):
        if isinstance(v, str):
            if not v or v.strip() == "":
                return []
            return [model.strip() for model in v.split(",") if model.strip()]
        return v or []
    
    # Database Configuration
    DATABASE_URL: str = Field(default="sqlite:///./healthlang.db", env="DATABASE_URL")
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    CHROMA_DB_PATH: str = Field(default="./data/medical_knowledge/embeddings", env="CHROMA_DB_PATH")
    
    # Vector Database Configuration
    VECTOR_DB_TYPE: str = Field(default="chroma", env="VECTOR_DB_TYPE")
    EMBEDDING_MODEL: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    CHUNK_SIZE: int = Field(default=1000, env="CHUNK_SIZE")
    CHUNK_OVERLAP: int = Field(default=200, env="CHUNK_OVERLAP")
    CHROMA_PERSIST_DIRECTORY: str = Field(default="./data/chroma", env="CHROMA_PERSIST_DIRECTORY")
    
    # Translation Configuration
    TRANSLATION_MODEL_PATH: str = Field(default="./data/models/translation", env="TRANSLATION_MODEL_PATH")
    TRANSLATION_MODEL: str = Field(default="meta-llama/Llama-4-Maverick-17B-128E-Instruct", env="TRANSLATION_MODEL")
    TRANSLATION_PROVIDER: str = Field(default="groq", env="TRANSLATION_PROVIDER")
    
    # Medical Analysis Configuration
    MEDICAL_MODEL_NAME: str = Field(default="grok-beta", env="MEDICAL_MODEL_NAME")
    MEDICAL_MODEL_PROVIDER: str = Field(default="xai", env="MEDICAL_MODEL_PROVIDER")
    MAX_TOKENS: int = Field(default=2048, env="MAX_TOKENS")  # Reduced for faster responses
    TEMPERATURE: float = Field(default=0.1, env="TEMPERATURE")
    TOP_P: float = Field(default=0.9, env="TOP_P")
    
    # RAG Configuration
    RAG_ENABLED: bool = Field(default=True, env="RAG_ENABLED")
    MAX_RETRIEVAL_DOCS: int = Field(default=3, env="MAX_RETRIEVAL_DOCS")  # Reduced for speed
    SIMILARITY_THRESHOLD: float = Field(default=0.75, env="SIMILARITY_THRESHOLD")  # Higher threshold
    KNOWLEDGE_BASE_PATH: str = Field(default="./data/medical_knowledge/processed", env="KNOWLEDGE_BASE_PATH")
    
    # Security Configuration
    SECRET_KEY: str = Field(default="your_secret_key_here_change_in_production", env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:8000", env="CORS_ORIGINS")
    
    @field_validator("CORS_ORIGINS")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            # Parse comma-separated string into list
            if v and v.strip():
                return [origin.strip() for origin in v.split(",") if origin.strip()]
            else:
                return ["http://localhost:3000", "http://localhost:8000"]  # Default fallback
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000", "http://localhost:8000"]  # Default fallback
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=120, env="RATE_LIMIT_PER_MINUTE")  # Increased for Render
    RATE_LIMIT_PER_HOUR: int = Field(default=2000, env="RATE_LIMIT_PER_HOUR")  # Increased for Render
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    LOG_FILE: str = Field(default="./logs/healthlang.log", env="LOG_FILE")
    
    # Monitoring Configuration
    PROMETHEUS_ENABLED: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    PROMETHEUS_PORT: int = Field(default=9090, env="PROMETHEUS_PORT")
    GRAFANA_PORT: int = Field(default=3000, env="GRAFANA_PORT")
    
    # Cache Configuration
    CACHE_TTL: int = Field(default=7200, env="CACHE_TTL")  # 2 hours for better caching
    CACHE_MAX_SIZE: int = Field(default=2000, env="CACHE_MAX_SIZE")  # Increased cache size
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    ALLOWED_FILE_TYPES: str = Field(default="pdf,docx,txt,md", env="ALLOWED_FILE_TYPES")
    
    @field_validator("ALLOWED_FILE_TYPES")
    @classmethod
    def parse_allowed_file_types(cls, v):
        if isinstance(v, str):
            return [ftype.strip() for ftype in v.split(",") if ftype.strip()]
        elif isinstance(v, list):
            return v
        return ["pdf", "docx", "txt", "md"]
    
    # Medical Knowledge Sources
    MEDICAL_SOURCES_PATH: str = Field(default="./data/medical_knowledge/raw", env="MEDICAL_SOURCES_PATH")
    WHO_GUIDELINES_URL: str = Field(default="https://www.who.int/health-topics", env="WHO_GUIDELINES_URL")
    CDC_GUIDELINES_URL: str = Field(default="https://www.cdc.gov/healthcommunication", env="CDC_GUIDELINES_URL")
    
    # MCP Configuration
    MCP_ENABLED: bool = Field(default=False, env="MCP_ENABLED")
    MCP_HEALTHCARE_SERVER_PATH: str = Field(default="./mcp_servers/healthcare_server.py", env="MCP_HEALTHCARE_SERVER_PATH")
    MCP_TIMEOUT: int = Field(default=30, env="MCP_TIMEOUT")
    
    # Development Configuration
    TESTING: bool = Field(default=False, env="TESTING")
    TEST_DATABASE_URL: str = Field(default="sqlite:///./test_healthlang.db", env="TEST_DATABASE_URL")
    MOCK_GROQ_RESPONSES: bool = Field(default=False, env="MOCK_GROQ_RESPONSES")
    
    # Docker Configuration
    DOCKER_IMAGE_NAME: str = Field(default="healthlang-ai-mvp", env="DOCKER_IMAGE_NAME")
    DOCKER_TAG: str = Field(default="latest", env="DOCKER_TAG")
    DOCKER_REGISTRY: str = Field(default="your-registry.com", env="DOCKER_REGISTRY")
    
    # Kubernetes Configuration
    K8S_NAMESPACE: str = Field(default="healthlang", env="K8S_NAMESPACE")
    K8S_REPLICAS: int = Field(default=3, env="K8S_REPLICAS")
    K8S_RESOURCE_LIMITS_CPU: str = Field(default="1000m", env="K8S_RESOURCE_LIMITS_CPU")
    K8S_RESOURCE_LIMITS_MEMORY: str = Field(default="2Gi", env="K8S_RESOURCE_LIMITS_MEMORY")
    K8S_RESOURCE_REQUESTS_CPU: str = Field(default="500m", env="K8S_RESOURCE_REQUESTS_CPU")
    K8S_RESOURCE_REQUESTS_MEMORY: str = Field(default="1Gi", env="K8S_RESOURCE_REQUESTS_MEMORY")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENVIRONMENT.lower() in ["development", "dev"]
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENVIRONMENT.lower() in ["production", "prod"]
    
    def is_testing(self) -> bool:
        """Check if running in testing mode"""
        return self.TESTING or self.ENVIRONMENT.lower() == "testing"
    
    def get_database_url(self) -> str:
        """Get the appropriate database URL based on environment"""
        if self.is_testing():
            return self.TEST_DATABASE_URL
        return self.DATABASE_URL
    
    def validate_settings(self) -> None:
        """Validate critical settings"""
        # Only validate API keys in production
        if self.is_production():
            if not self.GROQ_API_KEY or self.GROQ_API_KEY == "your_real_groq_api_key_here":
                raise ValueError("GROQ_API_KEY must be set")
            
            if self.SECRET_KEY == "your_secret_key_here_change_in_production":
                raise ValueError("SECRET_KEY must be changed in production")
        
        # Create necessary directories
        if not os.path.exists(self.CHROMA_DB_PATH):
            os.makedirs(self.CHROMA_DB_PATH, exist_ok=True)
        
        if not os.path.exists(os.path.dirname(self.LOG_FILE)):
            os.makedirs(os.path.dirname(self.LOG_FILE), exist_ok=True)


# Create settings instance
settings = Settings()

# Validate settings on import
try:
    settings.validate_settings()
except ValueError as e:
    import logging
    logging.error(f"Configuration error: {e}")
    raise 