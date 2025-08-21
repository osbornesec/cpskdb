# 🤖 Agentic RAG System

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)

> A locally hosted, agentic Retrieval-Augmented Generation system for multi-product technical data with high accuracy, auditability, and data privacy.

## ✨ Features

- **Multi-Agent Architecture**: LangGraph-powered agent orchestration with specialized agents
- **Local Deployment**: Complete data privacy with local hosting capabilities
- **Vector Search**: Qdrant integration with advanced reranking capabilities
- **REST API**: FastAPI-based endpoints with automatic OpenAPI documentation
- **Audit Trail**: Comprehensive query and response tracking for accountability
- **Extensible**: Plugin architecture for custom agents and data sources

## 🏗️ Architecture

### Core Components
- **FastAPI Server**: REST API with async support and automatic documentation
- **LangGraph Agents**: Multi-agent orchestration framework
- **Qdrant**: Vector database for embeddings storage and retrieval
- **PostgreSQL**: Metadata storage and audit logs
- **Redis**: Caching layer for performance optimization
- **Ollama**: Local LLM inference with GPT-OSS-20B model

### Multi-Agent Framework
Built on LangGraph for orchestrated agent workflows:

- **Supervisor Agent**: Intent classification and routing logic
- **Product Specialist Agents**: Domain-specific knowledge retrieval
- **Cross-Reference Agent**: Inter-product comparisons and correlations
- **Synthesis Agent**: Context aggregation and response generation
- **Validation Agent**: Quality assurance and guardrails

### Data Flow
```
Documents → Parse → Chunk → Embed → Qdrant
    ↓
Query → Intent → Route → Retrieve → Rerank → Generate → Validate → Response
```

## 📦 Installation

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- 8GB+ RAM recommended

### Quick Start
```bash
# Clone and setup
git clone https://github.com/osbornesec/cpskdb.git
cd cpskdb

# Start infrastructure services
docker-compose up -d

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000/docs` for the interactive API documentation.

## 💡 Usage

### Basic Query Example
```python
import httpx

response = httpx.post("http://localhost:8000/api/v1/query", json={
    "query": "How do I configure authentication in FastAPI?",
    "context": "web_development"
})

print(response.json())
```

### Document Ingestion
```python
# Upload documents for processing
files = {"file": open("technical_doc.pdf", "rb")}
response = httpx.post("http://localhost:8000/api/v1/ingest/document", files=files)
```

## ⚙️ Configuration

The system uses environment variables for configuration:

```bash
# Database Configuration
POSTGRES_URL=postgresql://user:pass@localhost:5432/cpskdb
QDRANT_HOST=localhost
QDRANT_PORT=6333
REDIS_URL=redis://localhost:6379

# AI Services
VOYAGE_API_KEY=your_voyage_key
COHERE_API_KEY=your_cohere_key
OLLAMA_HOST=http://localhost:11434

# Application Settings
API_VERSION=v1
DEBUG=false
LOG_LEVEL=INFO
```

## 📚 API Documentation

The system provides comprehensive API documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

### Key Endpoints
- `POST /api/v1/query` - Submit queries to the RAG system
- `GET /api/v1/query/{query_id}` - Retrieve query results and status
- `POST /api/v1/ingest/document` - Upload documents for processing
- `GET /health` - System health check

## 🛠️ Development

### Setup Development Environment
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/ -v

# Run with coverage
pytest --cov=src tests/
```

### Project Structure
```
src/
├── api/              # FastAPI routes and middleware
├── agents/           # LangGraph agent implementations
├── ingestion/        # Document processing pipeline
├── embeddings/       # Embedding services
├── retrieval/        # Vector search and ranking
└── models/           # Pydantic schemas
```

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for details.

### Development Process
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Ensure all tests pass (`pytest`)
5. Submit a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.