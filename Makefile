# Kopitar NHL Analytics Platform - Development Makefile

.PHONY: help install install-dev test lint format type-check docker-up docker-down clean

# Default target
help:
	@echo "Kopitar NHL Analytics Platform - Available commands:"
	@echo ""
	@echo "  install        Install production dependencies"
	@echo "  install-dev    Install development dependencies"
	@echo "  test          Run all tests"
	@echo "  test-cov      Run tests with coverage"
	@echo "  lint          Run linting (flake8)"
	@echo "  format        Format code (black, isort)"
	@echo "  type-check    Run type checking (mypy)"
	@echo "  docker-up     Start development environment"
	@echo "  docker-down   Stop development environment"
	@echo "  docker-logs   Show docker logs"
	@echo "  clean         Clean cache and temporary files"
	@echo "  setup-env     Initial environment setup"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev,ml,monitoring]"
	pre-commit install

# Testing
test:
	pytest

test-cov:
	pytest --cov=src/kopitar --cov-report=html --cov-report=term

# Code Quality
lint:
	flake8 src/ tests/
	black --check src/ tests/
	isort --check-only src/ tests/

format:
	black src/ tests/
	isort src/ tests/

type-check:
	mypy src/

# Docker Development Environment
docker-up:
	docker-compose -f docker-compose.dev.yml up -d
	@echo "Development environment started!"
	@echo "  - Jupyter Lab: http://localhost:8888"
	@echo "  - Airflow: http://localhost:8080"
	@echo "  - Grafana: http://localhost:3000"
	@echo "  - PostgreSQL: localhost:5432"
	@echo "  - Redis: localhost:6379"
	@echo "  - InfluxDB: http://localhost:8086"

docker-down:
	docker-compose -f docker-compose.dev.yml down

docker-logs:
	docker-compose -f docker-compose.dev.yml logs -f

docker-build:
	docker-compose -f docker-compose.dev.yml build

# Data Pipeline
collect-data:
	python -m kopitar.data.collectors.nhl_api

process-data:
	python -m kopitar.data.processors.game_processor

run-analysis:
	python -m kopitar.analysis.fatigue_analyzer

# Database Operations
init-db:
	python -m kopitar.database.init_db

migrate-db:
	alembic upgrade head

seed-db:
	python -m kopitar.database.seed_data

# API Server
run-api:
	uvicorn kopitar.api.main:app --reload --host 0.0.0.0 --port 8000

# Jupyter
jupyter:
	jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/

# Environment Setup
setup-env:
	cp .env.example .env
	@echo "Created .env file. Please update with your configuration."
	@echo "Run 'make install-dev' to install dependencies."
	@echo "Run 'make docker-up' to start development environment."

# Production
build:
	python -m build

# MLflow
mlflow-ui:
	mlflow ui --host 0.0.0.0 --port 5000

# Monitoring
prometheus:
	docker run -d -p 9090:9090 --name kopitar-prometheus prom/prometheus

# Development helpers
notebook:
	jupyter lab notebooks/

check: lint type-check test

pre-commit:
	pre-commit run --all-files

# Documentation
docs:
	@echo "Documentation available in markdown files:"
	@echo "  - CLAUDE.md: AI Assistant Context"
	@echo "  - planning.md: Project Roadmap"
	@echo "  - technical_architecture.md: System Design"
	@echo "  - team_roles.md: Team Structure"