# Technology Stack

## Core Technologies

### Backend Framework
- **FastAPI**: REST API framework with async support
- **Python 3.11+**: Primary programming language

### AI/ML Components
- **LangGraph**: Multi-agent orchestration framework
- **LangChain**: LLM application framework
- **Ollama**: Local LLM inference (GPT-OSS-20B model)
- **Voyage AI**: Embedding generation service
- **Cohere**: Reranking service for result optimization

### Data Storage
- **Qdrant**: Vector database for semantic search (port 6333)
- **PostgreSQL**: Relational database for metadata and audit trails (port 5432)
- **Redis**: Caching layer for performance optimization (port 6379)

### Document Processing
- **pdfplumber/PyMuPDF**: PDF parsing
- **Beautiful Soup**: HTML processing
- **python-docx**: Word document parsing

### Development Tools
- **pytest**: Testing framework
- **black**: Code formatter
- **ruff**: Fast Python linter
- **mypy**: Static type checker
- **Alembic**: Database migration tool
- **pre-commit**: Git hooks for code quality

### Infrastructure
- **Docker & Docker Compose**: Containerization
- **Prometheus & Grafana**: Monitoring and metrics
- **Custom bridge network**: 'rag-network' for service communication

### Python Key Libraries
- langgraph
- langchain
- qdrant-client
- fastapi
- pydantic
- sqlalchemy
- redis
- voyage-ai
- cohere
- ollama