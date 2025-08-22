# CPSKDB: Agentic RAG System

## Executive Summary

**Mission**: Building a locally hosted, agentic Retrieval-Augmented
Generation (RAG) system for multi-product technical data with high accuracy,
auditability, and data privacy.

**Current Status**: Task 99 - Implementing comprehensive Docker Compose test
scenarios (32/87 completed)

---

## 🏗️ System Architecture

### Core Data Flow

```mermaid
graph LR
    A[Documents] --> B[Parse & Chunk] --> C[Embed] --> D[Qdrant]
    E[Query] --> F[Intent Analysis] --> G[Agent Router] --> H[Vector Search]
    H --> I[Rerank] --> J[Synthesize] --> K[Validate] --> L[Response]
```

### Multi-Agent Framework (LangGraph)

- **🧠 Supervisor**: Intent classification & routing
- **🔍 Specialists**: Domain-specific retrieval  
- **🔗 Cross-Reference**: Inter-product correlations
- **⚡ Synthesis**: Context aggregation
- **✅ Validation**: Quality assurance & guardrails

### Technology Stack

```yaml
Infrastructure:
  api: FastAPI (async)
  vector_db: Qdrant (port 6333)
  metadata: PostgreSQL (port 5432)
  cache: Redis (port 6379)
  llm: Ollama (port 11434)

AI_ML:
  orchestration: LangGraph
  embeddings: Voyage AI
  reranking: Cohere
  chunking: Custom semantic strategies
```

---

## 📁 Project Structure

```text
cpskdb/
├── src/                    # 🎯 Core application
│   ├── api/               # FastAPI routes & middleware
│   ├── agents/            # LangGraph workflows
│   ├── ingestion/         # Document processing pipeline
│   ├── embeddings/        # Voyage AI & local providers
│   ├── retrieval/         # Qdrant client & rerankers
│   └── models/            # Pydantic schemas
├── tests/                 # 🧪 Comprehensive test suite
│   ├── unit/             # Component testing
│   ├── integration/      # Service interactions
│   └── e2e/              # End-to-end workflows
├── docker/               # 🐳 Container configurations
├── config/               # ⚙️ Settings management
├── scripts/              # 🔧 Automation & deployment
└── docs/                 # 📚 Technical documentation
```

---

## ⚡ Quick Start

### Environment Setup

```bash
# Required variables
export POSTGRES_URL="postgresql://user:pass@localhost:5432/cpskdb"
export QDRANT_HOST="localhost"
export VOYAGE_API_KEY="your_key"
export COHERE_API_KEY="your_key"

# Optional: Configure restart policy for different environments
# Local/Dev (default): unless-stopped
# CI/Testing: on-failure:3 (limits retries, surfaces errors quickly)
export QDRANT_RESTART_POLICY=unless-stopped  # or on-failure:3 for CI

# Start infrastructure services (Qdrant vector database)
docker compose up -d

# Run application locally for development
# Note: This runs the app on the host, not in a container
uvicorn src.api.main:app --reload --port 8000
```

### API Endpoints

```yaml
Core:
  - POST /api/v1/query           # Submit RAG queries
  - GET  /api/v1/query/{id}      # Retrieve results
  - POST /api/v1/feedback        # Quality feedback

Ingestion:
  - POST /api/v1/ingest/document # Upload documents
  - GET  /api/v1/ingest/status   # Processing status

System:
  - GET  /health                 # Health check
  - GET  /health/metrics         # Prometheus metrics
```

---

## 🔧 Development Workflow

### Research-First Development

**Always use before coding**:

```bash
# Before ANY coding
@agent-context7-docs-searcher "Research [topic/library/pattern]"
```

### Test-Driven Development

```bash
# Test execution
pytest tests/unit/          # Fast component tests
pytest tests/integration/   # Service interactions  
pytest tests/e2e/          # Complete workflows
pytest --cov=src tests/    # Coverage analysis

# Quality checks
ruff format .               # Code formatting
ruff check .               # Linting
mypy src/                  # Type checking
npx markdownlint-cli2 "**/*.md"  # Documentation
```

---

## 🎯 Current Task Context

### Task 99: Docker Compose Test Implementation

**Objective**: Complete all 87 comprehensive test scenarios for Qdrant
service configuration

**Progress**: 32/87 scenarios implemented

- ✅ Basic functionality (7 scenarios)
- ✅ Performance & resource (14 scenarios)  
- ✅ Security & validation (12 scenarios)
- ✅ Advanced integration (15 scenarios)
- ✅ State management (18 scenarios)
- ✅ Recovery & resilience (14 scenarios)
- 🔄 Error handling & edge cases (15 scenarios) - IN PROGRESS
- ⏳ Boundary conditions (20 scenarios) - PENDING

**File**: `tests/test_docker_compose_qdrant.py` (3,151 lines)

---


## 📋 Quality Standards

### Immediate Action Items

When detected, fix IMMEDIATELY:

- **Ruff formatting**: `ruff format`
- **Ruff linting**: Import errors, unused variables
- **Mypy issues**: Type annotations, stubs
- **LanguageTool**: Add false positives to dictionary

### LanguageTool Dictionary

Location: `scripts/languagetool_personal_dict.txt`

Common terms already added:

- Frameworks: `FastAPI`, `LangGraph`, `Qdrant`, `Redis`, `Ollama`
- Python: `pytest`, `pydantic`, `subprocess`, `tempfile`
- Classes: `TestQdrantDockerCompose`, `DatabaseSettings`
- Acronyms: `API`, `JSON`, `TDD`, `RAG`, `LLM`

---

## 🔒 Git & Security

### Repository Info

- **URL**: https://github.com/osbornesec/cpskdb
- **Owner**: Michael Osborne (Michael [at] allthingsai.life)
- **Branch**: main

### Commit Standards

```text
<type>: <subject>

<body>

🤖 Generated with AI assistance
```

**Types**: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

### Security Rules

**NEVER COMMIT**:

- API keys, credentials, secrets
- `.env` files with sensitive data  
- Large model files, datasets
- Database dumps, backups

---

## 🎯 Success Metrics

### Completion Criteria

- [ ] All 87 test scenarios implemented
- [ ] Docker Compose configuration validated
- [ ] Health checks properly configured
- [ ] Volume persistence verified
- [ ] Network isolation tested
- [ ] Error handling comprehensive
- [ ] Performance benchmarks established

### Quality Gates

- [ ] All tests pass (unit, integration, e2e)
- [ ] Code quality tools pass (ruff, mypy)
- [ ] Documentation validated (markdownlint)
- [ ] Security scan clean
- [ ] Performance within limits

---

## 📚 Knowledge Integration

### Documentation Research

**Always use before coding**:

```bash
@agent-context7-docs-searcher "Research [specific need]"
```


---


## 🎯 Development Environment

### Docker Compose Services

**Current (default compose):**

- **Qdrant** (port 6333): Vector database with persistence

**Full Stack (optional/future):**

- **PostgreSQL** (port 5432): Metadata and audit logs
- **Redis** (port 6379): Caching and session storage
- **Ollama** (port 11434): Local LLM inference

### Configuration Structure

**Pydantic Settings Classes**:

- `DatabaseSettings`: Connection configs and pool settings
- `EmbeddingSettings`: Provider configs and rate limits
- `AgentSettings`: LLM parameters and workflow configs
- `APISettings`: Server configs and middleware settings

---

**🎯 Current Focus**: Complete remaining 55 test scenarios for comprehensive
Docker Compose validation following TDD methodology.

---

## Important Instruction Reminders

Do what has been asked; nothing more, nothing less.
ALWAYS use @agent-context7-docs-searcher BEFORE writing any code.
For ALL documentation research, use @agent-context7-docs-searcher.
