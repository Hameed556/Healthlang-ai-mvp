# HealthLang AI MVP Makefile

# Variables
PYTHON := python3
PIP := pip3
DOCKER := docker
DOCKER_COMPOSE := docker-compose
APP_NAME := healthlang-ai-mvp
PYTEST := pytest

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

.PHONY: help install dev-install test lint format clean docker-build docker-run docker-stop docker-logs setup init-data

# Default target
help:
	@echo "$(BLUE)HealthLang AI MVP - Available Commands:$(NC)"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  install        - Install production dependencies"
	@echo "  dev-install    - Install development dependencies"
	@echo "  test           - Run tests"
	@echo "  test-coverage  - Run tests with coverage"
	@echo "  lint           - Run linting checks"
	@echo "  format         - Format code with black and isort"
	@echo "  clean          - Clean up cache and temporary files"
	@echo ""
	@echo "$(GREEN)Docker:$(NC)"
	@echo "  docker-build   - Build Docker image"
	@echo "  docker-run     - Run with Docker Compose"
	@echo "  docker-stop    - Stop Docker containers"
	@echo "  docker-logs    - Show Docker logs"
	@echo "  docker-clean   - Clean Docker containers and images"
	@echo ""
	@echo "$(GREEN)Setup:$(NC)"
	@echo "  setup          - Initial project setup"
	@echo "  init-data      - Initialize data directories and models"
	@echo "  download-models - Download required models"
	@echo "  process-data   - Process medical data"
	@echo ""
	@echo "$(GREEN)Database:$(NC)"
	@echo "  setup-db       - Setup database and vector store"
	@echo "  migrate        - Run database migrations"
	@echo ""
	@echo "$(GREEN)Monitoring:$(NC)"
	@echo "  start-monitoring - Start monitoring stack (Prometheus + Grafana)"
	@echo "  stop-monitoring  - Stop monitoring stack"

# Development commands
install:
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	$(PIP) install -r requirements.txt

dev-install:
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-asyncio pytest-cov black isort flake8 mypy

test:
	@echo "$(BLUE)Running tests...$(NC)"
	$(PYTEST) tests/ -v

test-coverage:
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(PYTEST) tests/ -v --cov=app --cov-report=html --cov-report=term

lint:
	@echo "$(BLUE)Running linting checks...$(NC)"
	flake8 app/ tests/
	mypy app/

format:
	@echo "$(BLUE)Formatting code...$(NC)"
	black app/ tests/
	isort app/ tests/

clean:
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf build/
	rm -rf dist/

# Docker commands
docker-build:
	@echo "$(BLUE)Building Docker image...$(NC)"
	$(DOCKER) build -t $(APP_NAME) .

docker-run:
	@echo "$(BLUE)Starting services with Docker Compose...$(NC)"
	$(DOCKER_COMPOSE) up -d

docker-stop:
	@echo "$(BLUE)Stopping Docker containers...$(NC)"
	$(DOCKER_COMPOSE) down

docker-logs:
	@echo "$(BLUE)Showing Docker logs...$(NC)"
	$(DOCKER_COMPOSE) logs -f

docker-clean:
	@echo "$(BLUE)Cleaning Docker containers and images...$(NC)"
	$(DOCKER_COMPOSE) down -v --rmi all
	$(DOCKER) system prune -f

# Setup commands
setup:
	@echo "$(BLUE)Setting up HealthLang AI MVP...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Creating .env file from template...$(NC)"; \
		cp env.example .env; \
		echo "$(RED)Please edit .env file with your configuration!$(NC)"; \
	fi
	@echo "$(BLUE)Creating necessary directories...$(NC)"
	mkdir -p logs data/medical_knowledge/{raw,processed,embeddings}
	mkdir -p data/translation/{yoruba_english,medical_terms,parallel_corpus}
	mkdir -p data/models/{translation,checkpoints}
	@echo "$(GREEN)Setup complete!$(NC)"

init-data:
	@echo "$(BLUE)Initializing data directories...$(NC)"
	mkdir -p data/medical_knowledge/{raw,processed,embeddings}
	mkdir -p data/translation/{yoruba_english,medical_terms,parallel_corpus}
	mkdir -p data/models/{translation,checkpoints}
	touch data/medical_knowledge/raw/.gitkeep
	touch data/medical_knowledge/processed/.gitkeep
	touch data/medical_knowledge/embeddings/.gitkeep
	touch data/translation/yoruba_english/.gitkeep
	touch data/translation/medical_terms/.gitkeep
	touch data/translation/parallel_corpus/.gitkeep
	touch data/models/translation/.gitkeep
	touch data/models/checkpoints/.gitkeep
	@echo "$(GREEN)Data directories initialized!$(NC)"

download-models:
	@echo "$(BLUE)Downloading required models...$(NC)"
	$(PYTHON) scripts/download_models.py

process-data:
	@echo "$(BLUE)Processing medical data...$(NC)"
	$(PYTHON) scripts/process_medical_data.py

# Database commands
setup-db:
	@echo "$(BLUE)Setting up database and vector store...$(NC)"
	$(PYTHON) scripts/setup_database.py

migrate:
	@echo "$(BLUE)Running database migrations...$(NC)"
	alembic upgrade head

# Monitoring commands
start-monitoring:
	@echo "$(BLUE)Starting monitoring stack...$(NC)"
	$(DOCKER_COMPOSE) up -d prometheus grafana

stop-monitoring:
	@echo "$(BLUE)Stopping monitoring stack...$(NC)"
	$(DOCKER_COMPOSE) stop prometheus grafana

# Production commands
deploy:
	@echo "$(BLUE)Deploying to production...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.yml --profile production up -d

deploy-advanced:
	@echo "$(BLUE)Deploying with advanced features...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.yml --profile production --profile advanced up -d

# Utility commands
logs:
	@echo "$(BLUE)Showing application logs...$(NC)"
	tail -f logs/healthlang.log

status:
	@echo "$(BLUE)Checking service status...$(NC)"
	$(DOCKER_COMPOSE) ps

restart:
	@echo "$(BLUE)Restarting services...$(NC)"
	$(DOCKER_COMPOSE) restart

# Development server
dev:
	@echo "$(BLUE)Starting development server...$(NC)"
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Health check
health:
	@echo "$(BLUE)Checking application health...$(NC)"
	curl -f http://localhost:8000/health || echo "$(RED)Application is not healthy$(NC)"

# Security scan
security-scan:
	@echo "$(BLUE)Running security scan...$(NC)"
	safety check

# Performance test
perf-test:
	@echo "$(BLUE)Running performance tests...$(NC)"
	$(PYTEST) tests/performance/ -v -m performance

# Documentation
docs:
	@echo "$(BLUE)Building documentation...$(NC)"
	mkdocs build

docs-serve:
	@echo "$(BLUE)Serving documentation...$(NC)"
	mkdocs serve

# Backup and restore
backup:
	@echo "$(BLUE)Creating backup...$(NC)"
	tar -czf backup-$(shell date +%Y%m%d-%H%M%S).tar.gz data/ logs/

restore:
	@echo "$(BLUE)Restoring from backup...$(NC)"
	@read -p "Enter backup file name: " backup_file; \
	tar -xzf $$backup_file

# Git hooks
install-hooks:
	@echo "$(BLUE)Installing git hooks...$(NC)"
	cp scripts/git-hooks/* .git/hooks/
	chmod +x .git/hooks/* 