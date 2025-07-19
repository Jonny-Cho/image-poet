# Image Poet Backend Makefile

# Default environment
ENV ?= local

# Python virtual environment
VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

.PHONY: help install dev dev-s3 localstack-setup localstack-start localstack-stop test clean

help: ## Show this help message
	@echo "Image Poet Backend Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install: ## Install dependencies
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt

dev: ## Start development server (local file storage)
	@echo "🚀 Starting development server with local file storage..."
	@[ ! -f .env ] && cp .env.example .env && echo "Created .env from .env.example" || echo "Using existing .env"
	$(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-localstack: ## Start development server with LocalStack S3
	@echo "🚀 Starting development server with LocalStack S3..."
	@cp .env.localstack .env
	$(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

localstack-setup: ## Setup LocalStack S3 environment
	@echo "🔧 Setting up LocalStack S3..."
	./scripts/setup-localstack.sh

localstack-start: ## Start LocalStack only
	@echo "📦 Starting LocalStack..."
	docker-compose -f docker-compose.localstack.yml up -d

localstack-stop: ## Stop LocalStack
	@echo "🛑 Stopping LocalStack..."
	docker-compose -f docker-compose.localstack.yml down

localstack-status: ## Check LocalStack status
	@echo "📊 LocalStack Status:"
	@docker-compose -f docker-compose.localstack.yml ps
	@echo ""
	@echo "🔍 Health Check:"
	@curl -s http://localhost:4566/health || echo "LocalStack not responding"

test-s3: ## Test S3 connection
	@echo "🧪 Testing S3 connection..."
	@curl -X GET http://localhost:8000/api/v1/storage/status

test: ## Run tests
	$(PYTHON) -m pytest

clean: ## Clean up containers and temp files
	docker-compose -f docker-compose.localstack.yml down -v
	docker system prune -f

logs: ## Show LocalStack logs
	docker-compose -f docker-compose.localstack.yml logs -f

# Environment switching
env-local: ## Switch to local file storage
	@cp .env.example .env
	@echo "✅ Switched to local file storage environment (overwrote existing .env)"

env-localstack: ## Switch to LocalStack S3 environment  
	@cp .env.localstack .env
	@echo "✅ Switched to LocalStack S3 environment"

# Quick commands
quick-start: localstack-setup env-localstack dev-localstack ## Quick start with LocalStack (setup + run)

# AWS commands (for LocalStack)
s3-ls: ## List S3 buckets in LocalStack
	aws --endpoint-url=http://localhost:4566 s3 ls

s3-ls-bucket: ## List contents of image-poet-local bucket
	aws --endpoint-url=http://localhost:4566 s3 ls s3://image-poet-local/ --recursive