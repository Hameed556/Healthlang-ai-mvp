# Multi-stage build for HealthLang AI MVP
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt requirements-prod.txt pyproject.toml ./

# Install Python dependencies (use production requirements for smaller image)
RUN pip install --no-cache-dir -r requirements-prod.txt

# Development stage
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir pytest pytest-asyncio pytest-cov black isort flake8 mypy

# Copy source code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data/medical_knowledge/embeddings

# Expose port
EXPOSE 8000

# Development command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production

# Create non-root user
RUN groupadd -r healthlang && useradd -r -g healthlang healthlang

# Copy source code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/data/medical_knowledge/embeddings \
    && chown -R healthlang:healthlang /app

# Switch to non-root user
USER healthlang

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Testing stage
FROM base as testing

# Install testing dependencies
RUN pip install --no-cache-dir pytest pytest-asyncio pytest-cov httpx

# Copy source code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data/medical_knowledge/embeddings

# Run tests
CMD ["pytest", "-v", "--cov=app", "--cov-report=html", "--cov-report=term"] 