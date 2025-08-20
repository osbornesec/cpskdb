# Project Structure

## Current Status
The project is in initial setup phase. Only the CLAUDE.md configuration file exists currently.

## Planned Directory Structure
```
cpskdb/
├── python/
│   ├── src/
│   │   ├── api/         # FastAPI REST endpoints and routing
│   │   │   ├── __init__.py
│   │   │   ├── main.py              # Application entry point
│   │   │   ├── routes/              # API route definitions
│   │   │   ├── middleware/          # Custom middleware
│   │   │   └── dependencies.py      # Dependency injection
│   │   ├── agents/      # LangGraph multi-agent orchestration
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py      # Main agent orchestrator
│   │   │   ├── routing_agent.py     # Query routing agent
│   │   │   ├── qa_agent.py          # Question-answering agent
│   │   │   ├── search_agent.py      # Search specialist agent
│   │   │   └── validation_agent.py  # Response validation agent
│   │   ├── ingestion/   # Document processing and chunking pipeline
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py          # Main ingestion pipeline
│   │   │   ├── parsers/             # Document parsers
│   │   │   ├── chunkers/            # Chunking strategies
│   │   │   └── processors/          # Text processors
│   │   ├── embeddings/  # Voyage AI and local embedding models
│   │   │   ├── __init__.py
│   │   │   ├── voyage_service.py    # Voyage AI integration
│   │   │   ├── cache.py             # Redis caching
│   │   │   └── fallback.py          # Local embedding fallback
│   │   ├── retrieval/   # Vector search and reranking logic
│   │   │   ├── __init__.py
│   │   │   ├── vector_search.py     # Qdrant search
│   │   │   ├── hybrid_search.py     # Hybrid search implementation
│   │   │   ├── reranker.py          # Cohere reranking
│   │   │   └── filters.py           # Search filters
│   │   ├── models/      # Pydantic schemas and database models
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py           # Pydantic models
│   │   │   ├── database.py          # SQLAlchemy models
│   │   │   └── validators.py        # Custom validators
│   │   └── config/      # Configuration management
│   │       ├── __init__.py
│   │       ├── settings.py          # Settings management
│   │       └── constants.py         # Application constants
│   └── tests/
│       ├── unit/        # Unit tests for individual components
│       ├── integration/ # Integration tests for component interactions
│       ├── e2e/         # End-to-end workflow tests
│       ├── fixtures/    # Test fixtures and data
│       └── conftest.py  # Pytest configuration
├── docker/              # Docker and Docker Compose configurations
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.dev.yml
├── config/              # Application configuration files
│   ├── .env.example
│   └── logging.yaml
├── scripts/             # Utility and setup scripts
│   ├── setup.sh
│   ├── migrate.sh
│   └── seed_data.py
├── docs/                # Project documentation
│   ├── API.md
│   ├── ARCHITECTURE.md
│   └── DEPLOYMENT.md
├── .ai/                 # AI-related documentation
│   └── docs/
│       ├── tasks.md     # Task tracking
│       ├── tests.md     # Test specifications
│       └── PRD.md       # Product requirements
├── alembic/            # Database migrations
│   ├── versions/
│   └── alembic.ini
├── pyproject.toml      # Python project configuration
├── requirements.txt    # Python dependencies
├── Makefile           # Build automation
├── .gitignore         # Git ignore rules
├── .pre-commit-config.yaml  # Pre-commit hooks
├── CLAUDE.md          # Development instructions (exists)
└── README.md          # Project overview
```

## Key Design Principles
1. **Separation of Concerns**: Clear boundaries between layers
2. **Dependency Injection**: Use FastAPI's DI system
3. **Async-First**: Leverage async/await for I/O operations
4. **Testability**: Design for easy unit and integration testing
5. **Configuration Management**: Environment-based configuration
6. **Error Handling**: Comprehensive error handling at all layers
7. **Logging**: Structured logging throughout the application

## Module Responsibilities
- **api/**: HTTP layer, request/response handling
- **agents/**: Business logic for agent orchestration
- **ingestion/**: Document processing pipeline
- **embeddings/**: Vector embedding generation
- **retrieval/**: Search and ranking logic
- **models/**: Data structures and validation
- **config/**: Application configuration