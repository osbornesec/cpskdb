.DEFAULT_GOAL := help
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help install clean docker-up docker-down test test-unit test-integration test-e2e format lint type-check quality dev pre-commit-install pre-commit-run

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

$(VENV)/pyvenv.cfg: pyproject.toml
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

install: $(VENV)/pyvenv.cfg  ## Install dependencies in virtual environment

docker-up:  ## Start Docker Compose services
	@if ! command -v docker >/dev/null 2>&1; then \
		echo "Docker not found. Please install Docker and try again."; \
		exit 1; \
	fi
	docker compose up -d qdrant
	@echo "Waiting for Qdrant to be ready..."
	@until curl -s http://localhost:6333/healthz >/dev/null 2>&1; do sleep 1; done
	@echo "Qdrant is ready!"

docker-down:  ## Stop Docker Compose services  
	@if ! command -v docker >/dev/null 2>&1; then \
		echo "Docker not found. Please install Docker and try again."; \
		exit 1; \
	fi
	docker compose down

test: install  ## Run all tests
	@if [ -d "tests" ]; then \
		$(PYTHON) -m pytest tests/ -v --cov=src; \
	else \
		echo "Tests directory not found. Create tests/ directory first."; \
	fi

test-unit: install  ## Run unit tests only
	@if [ -d "tests/unit" ]; then \
		$(PYTHON) -m pytest tests/unit/ -v --cov=src --cov-report=html; \
	else \
		echo "Unit tests directory not found. Create tests/unit/ directory first."; \
	fi

test-integration: install docker-up  ## Run integration tests
	@if [ -d "tests/integration" ]; then \
		$(PYTHON) -m pytest tests/integration/ -v; \
		$(MAKE) docker-down; \
	else \
		echo "Integration tests directory not found. Create tests/integration/ directory first."; \
		$(MAKE) docker-down; \
	fi

test-e2e: install docker-up  ## Run end-to-end tests
	@if [ -d "tests/e2e" ]; then \
		$(PYTHON) -m pytest tests/e2e/ -v -s; \
		$(MAKE) docker-down; \
	else \
		echo "E2E tests directory not found. Create tests/e2e/ directory first."; \
		$(MAKE) docker-down; \
	fi

format: install  ## Format code with ruff
	$(PYTHON) -m ruff format .

lint: install  ## Run linting checks with ruff
	$(PYTHON) -m ruff check .

type-check: install  ## Run type checking with mypy
	$(PYTHON) -m mypy src/

quality: format lint type-check  ## Run all code quality checks

dev: install docker-up  ## Start development server
	@echo "Starting development environment..."
	@echo "Qdrant available at http://localhost:6333"
	@if [ -f "src/api/main.py" ]; then \
		$(PYTHON) -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000; \
	else \
		echo "FastAPI main.py not found. Create src/api/main.py first."; \
	fi

pre-commit-install: install  ## Install pre-commit git hooks
	$(PYTHON) -m pre_commit install
	@echo "Pre-commit hooks installed successfully!"

pre-commit-run: install  ## Run pre-commit hooks on all files
	$(PYTHON) -m pre_commit run --all-files

clean:  ## Clean build artifacts and virtual environment
	rm -rf $(VENV)
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf build/ dist/ *.egg-info/ .coverage htmlcov/ .pytest_cache/