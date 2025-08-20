# Suggested Development Commands

## Project Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -e .  # Install project in editable mode
pip install -r requirements.txt
```

## Docker Services
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f [service_name]

# Check service health
docker-compose ps
```

## Code Quality Commands
```bash
# Format code with black
black src/ tests/

# Lint with ruff
ruff check src/ tests/
ruff check --fix src/ tests/  # Auto-fix issues

# Type checking with mypy
mypy src/

# Run pre-commit hooks
pre-commit run --all-files
```

## Testing Commands
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_embeddings.py
```

## Database Commands
```bash
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback migration
alembic downgrade -1
```

## Development Server
```bash
# Run FastAPI development server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Run with custom config
python -m src.api.main
```

## Ollama Model Management
```bash
# Pull model
ollama pull gpt-oss-20b

# List models
ollama list

# Run model
ollama run gpt-oss-20b
```

## Git Commands
```bash
# Check status
git status

# Stage changes
git add .

# Commit with message
git commit -m "feat: description"

# Push to remote
git push origin main
```

## Makefile Shortcuts (when implemented)
```bash
make install      # Install dependencies
make test        # Run tests
make lint        # Run linters
make format      # Format code
make clean       # Clean cache files
make docker-up   # Start Docker services
make docker-down # Stop Docker services
```

## System Utilities (Linux)
```bash
# File operations
ls -la          # List all files
find . -name "*.py"  # Find Python files
grep -r "pattern" .  # Search in files

# Process management
ps aux | grep python
kill -9 [PID]

# Resource monitoring
htop
df -h
du -sh *
```

## Python REPL for Testing
```python
# Quick testing in Python REPL
python
>>> from src.embeddings import VoyageEmbeddingService
>>> service = VoyageEmbeddingService()
>>> embeddings = service.embed_texts(["test"])
```