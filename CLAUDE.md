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

### CRITICAL: Code Operations Protocol

**PRIMARY TOOLS** (Always use first):

1. **Serena MCP**: All code search/edit operations
2. **Context7 MCP**: Documentation research  
3. **Traditional tools**: FALLBACK ONLY

**Research-First Development**:

```bash
# Before ANY coding
@agent-context7-docs-searcher "Research [topic/library/pattern]"

# Then implement using Serena MCP tools
mcp__serena__find_symbol
mcp__serena__replace_symbol_body
mcp__serena__insert_after_symbol
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

## 🛠️ Serena MCP Operations

### Code Search (Primary Methods)

```python
# Find symbols by pattern
mcp__serena__find_symbol(
    name_path="ClassName/methodName",
    include_body=True,
    depth=1
)

# Search patterns across codebase
mcp__serena__search_for_pattern(
    substring_pattern="TODO|FIXME",
    restrict_search_to_code_files=True
)

# Get file overview
mcp__serena__get_symbols_overview(
    relative_path="src/api/"
)
```

### Code Editing (Symbol-Based)

```python
# Replace entire functions/classes
mcp__serena__replace_symbol_body(
    name_path="functionName",
    relative_path="file.py", 
    body="new implementation"
)

# Insert new code
mcp__serena__insert_after_symbol(
    name_path="lastMethod",
    body="def new_method():\n    pass"
)
```

### Memory Management

```python
# Store project knowledge
mcp__serena__write_memory(
    memory_name="test_patterns",
    content="TDD implementation strategies..."
)

# Retrieve stored knowledge  
mcp__serena__read_memory(
    memory_file_name="architecture_overview.md"
)
```

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

🤖 Generated with [Claude Code](https://claude.ai/code)
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

### Project Memory

Location: `.claude/memories/`

- Architecture patterns
- Implementation decisions  
- Task completion tracking
- Best practices discovered

---

## 🛠️ Detailed Serena MCP Reference

### Core Capabilities

#### Search Code (ALWAYS use these first)

- **Find symbols**: `mcp__serena__find_symbol(name_path="ClassName", include_body=True)`
  - Searches for code entities by name path pattern
  - Supports depth parameter to retrieve children (e.g., methods of a class)
  - Can include/exclude specific symbol kinds (classes, functions, variables, etc.)
  
- **Find references**: `mcp__serena__find_referencing_symbols(name_path=
  "methodName", relative_path="file.py")`
  - Finds all references to a specific symbol
  - Returns metadata and code snippets around references
  
- **Pattern search**: `mcp__serena__search_for_pattern(substring_pattern=
  "TODO|FIXME")`
  - Flexible regex search across codebase
  - Supports file inclusion/exclusion globs
  - Can restrict to code files only
  
- **Symbol overview**: `mcp__serena__get_symbols_overview(relative_path=
  "src/")`
  - High-level understanding of symbols in a file
  - Shows top-level classes, functions, variables
  - Essential first step when exploring new files

#### File Operations

- **List directory**: `mcp__serena__list_dir(relative_path=".",
  recursive=true)`
  - Lists non-git ignored files and directories
  
- **Find files**: `mcp__serena__find_file(file_mask="*.py",
  relative_path=".")`
  - Finds files matching patterns using wildcards

#### Edit Code (PREFER symbol-based operations)

- **Replace symbol body**: `mcp__serena__replace_symbol_body(name_path=
  "functionName", relative_path="file.py", body="new code")`
  - Replaces entire function/class/method body
  - Preserves indentation and context
  
- **Insert before symbol**: `mcp__serena__insert_before_symbol(name_path=
  "className", body="imports")`
  - Ideal for adding imports or new top-level definitions
  
- **Insert after symbol**: `mcp__serena__insert_after_symbol(name_path=
  "methodName", body="new method")`
  - Adds new methods, functions, or classes after existing ones

#### Project Management

- **Check onboarding**: `mcp__serena__check_onboarding_performed()`
- **Onboarding**: `mcp__serena__onboarding()`

#### Thinking Tools (Use strategically)

- **Think about collected information**:
  `mcp__serena__think_about_collected_information()`
- **Think about task adherence**: `mcp__serena__think_about_task_adherence()`
- **Think about whether done**: `mcp__serena__think_about_whether_you_are_done()`

### Best Practices

1. **Symbol-based editing over text replacement**
2. **Efficient code exploration**: Start with overview, then targeted reads
3. **Name path patterns**: Simple ("method"), relative ("class/method"),
   absolute ("/class/method")
4. **Always verify before editing**: Use thinking tools, find references

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
Use Serena MCP for code operations, with traditional tools as fallback only.
For ALL documentation research, use @agent-context7-docs-searcher.
