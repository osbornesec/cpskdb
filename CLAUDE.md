# Agentic RAG System - Project Documentation

## Project Overview
Building a locally hosted, agentic Retrieval-Augmented Generation (RAG) system for multi-product technical data with high accuracy, auditability, and data privacy.

## Architecture

### System Design
The system implements an agentic RAG architecture with the following data flow:

1. **Document Ingestion**: Parse, chunk, and embed documents into vector storage
2. **Query Processing**: Analyze user intent and route to appropriate agents
3. **Knowledge Retrieval**: Vector search with reranking for relevant context
4. **Response Generation**: Multi-agent synthesis with validation
5. **Audit & Feedback**: Track citations and collect user feedback

### Multi-Agent Framework
Built on LangGraph for orchestrated agent workflows:

- **Supervisor Agent**: Intent classification and routing logic
- **Product Specialist Agents**: Domain-specific knowledge retrieval
- **Cross-Reference Agent**: Inter-product comparisons and correlations  
- **Synthesis Agent**: Context aggregation and response generation
- **Validation Agent**: Quality assurance and guardrails

### Technology Stack
**Core Infrastructure:**
- FastAPI: REST API with async support
- Qdrant: Vector database for embeddings
- PostgreSQL: Metadata, logs, and relationships
- Redis: Caching and session storage
- Ollama: Local LLM (GPT-OSS-20B)

**AI/ML Components:**
- LangGraph: Agent orchestration framework
- Voyage AI: Production embedding service
- Cohere: Reranking for improved relevance
- Custom chunking: Semantic and structural strategies

**Data Flow:**

```text
Documents → Parse → Chunk → Embed → Qdrant
    ↓
Query → Intent → Route → Retrieve → Rerank → Generate → Validate → Response
```


## Directory Structure

```text
.
├── src/                 # Main application source code
│   ├── api/            # FastAPI routes and endpoints
│   │   ├── routes/     # Individual route modules
│   │   ├── middleware/ # Custom middleware
│   │   └── dependencies.py # Shared dependencies
│   ├── agents/         # LangGraph agents and workflows
│   │   ├── supervisor/ # Main routing agent
│   │   ├── specialists/ # Product-specific agents
│   │   ├── synthesis/  # Response generation agents
│   │   └── validation/ # Quality assurance agents
│   ├── ingestion/      # Document processing pipeline
│   │   ├── parsers/    # Document format parsers
│   │   ├── chunkers/   # Text chunking strategies
│   │   └── pipeline.py # Orchestration logic
│   ├── embeddings/     # Embedding services (Voyage AI, local)
│   │   ├── providers/  # Different embedding providers
│   │   ├── cache/      # Embedding caching layer
│   │   └── service.py  # Main embedding service
│   ├── retrieval/      # Vector search and ranking
│   │   ├── vector_store.py # Qdrant client
│   │   ├── rerankers/  # Cohere and other rerankers
│   │   └── search.py   # Search orchestration
│   └── models/         # Pydantic models and schemas
│       ├── requests.py # API request models
│       ├── responses.py # API response models
│       └── database.py # Database models
├── tests/              # Test suite
│   ├── unit/          # Unit tests for individual modules
│   ├── integration/   # Integration tests for service interactions
│   └── e2e/           # End-to-end workflow tests
├── docker/             # Container configurations
│   ├── Dockerfile     # Application container
│   ├── docker-compose.yml # Development environment
│   └── docker-compose.prod.yml # Production environment
├── config/             # Configuration files
│   ├── settings.py    # Application settings
│   ├── database.py    # Database configuration
│   └── logging.py     # Logging configuration
├── scripts/            # Utility and deployment scripts
│   ├── deploy.sh      # Deployment automation
│   ├── backup.sh      # Database backup scripts
│   └── migrate.sh     # Database migration scripts
└── docs/               # Project documentation
    ├── api/           # API documentation
    ├── architecture/  # System design documents
    └── deployment/    # Deployment guides
```


**Key Directory Purposes:**
- **src/**: Contains all application source code, organized by functional area
- **tests/**: Comprehensive test suite with unit, integration, and e2e tests
- **docker/**: Containerization configs for development and production
- **config/**: Centralized configuration management
- **scripts/**: Automation scripts for deployment and maintenance
- **docs/**: Technical documentation and guides

## Configuration Management

### Environment Variables
Core configuration through environment files:

**Required Variables:**
```bash
# Database Configuration
POSTGRES_URL=postgresql://<user>:<password>@localhost:5432/cpskdb
QDRANT_HOST=localhost
QDRANT_PORT=6333
REDIS_URL=redis://localhost:6379

# AI Services
VOYAGE_API_KEY=voyage_key_here
COHERE_API_KEY=cohere_key_here
OLLAMA_HOST=http://localhost:11434

# Application Settings
API_VERSION=v1
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000
```

**Optional Variables:**
```bash
# Performance Tuning
EMBEDDING_BATCH_SIZE=128
VECTOR_SEARCH_LIMIT=50
CACHE_TTL=3600

# Feature Flags
ENABLE_RERANKING=true
ENABLE_QUERY_CACHE=true
ENABLE_METRICS=true
```

### Configuration Structure
**Pydantic Settings Classes:**
- `DatabaseSettings`: Connection configs and pool settings
- `EmbeddingSettings`: Provider configs and rate limits
- `AgentSettings`: LLM parameters and workflow configs
- `APISettings`: Server configs and middleware settings

### Development Environment
Docker Compose setup for local development:

**Services:**
- **Qdrant** (port 6333): Vector database with persistence
- **PostgreSQL** (port 5432): Metadata and audit logs
- **Redis** (port 6379): Caching and session storage
- **Ollama** (port 11434): Local LLM inference

**Setup Commands:**
```bash
# Start all services
docker compose up -d

# Initialize database
python scripts/init_db.py

# Run application
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation
RESTful API with OpenAPI documentation available at `/docs`:

**Core Endpoints:**
- `POST /api/v1/query` - Submit queries to the RAG system
- `GET /api/v1/query/{query_id}` - Retrieve query results and status
- `POST /api/v1/query/batch` - Batch query processing
- `GET /api/v1/citations/{query_id}` - Get source citations
- `POST /api/v1/feedback` - Submit feedback on responses

**Ingestion Endpoints:**
- `POST /api/v1/ingest/document` - Single document upload
- `POST /api/v1/ingest/batch` - Batch document processing
- `GET /api/v1/ingest/status/{job_id}` - Check ingestion status

**System Endpoints:**
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness probe for K8s
- `GET /health/metrics` - Prometheus metrics

## Testing Strategy
Comprehensive test coverage across all system layers:

**Unit Tests (`tests/unit/`):**
- Component-level testing for individual modules
- Mock external dependencies (APIs, databases)
- Fast execution for TDD workflow

**Integration Tests (`tests/integration/`):**
- Service interaction testing
- Database integration with test containers
- API endpoint testing with test clients

**End-to-End Tests (`tests/e2e/`):**
- Complete workflow validation
- Real service dependencies
- Performance and load testing

**Test Commands:**
```bash
# Run all tests
pytest tests/

# Run specific test types
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov=src tests/
```

## Claude Code Integration

### MCP Server Configuration
This project leverages Serena MCP for semantic code operations:

**Primary Tools:**
- `mcp__serena__find_symbol` - Locate code symbols
- `mcp__serena__replace_symbol_body` - Edit functions/classes
- `mcp__serena__search_for_pattern` - Pattern-based search
- `mcp__serena__get_symbols_overview` - File structure analysis

**Memory Management:**
- Project knowledge stored in `.claude/memories/`
- Architecture patterns documented for reuse
- Task completion tracking with persistent state

### Subagent Integration
**@agent-context7-docs-searcher** for documentation research:
- FastAPI best practices and patterns
- LangGraph agent development
- Vector database optimization
- ML/AI system architecture

**Development Workflow:**
1. Use @agent-context7-docs-searcher for research
2. Apply Serena MCP for code implementation
3. Follow TDD with comprehensive test coverage
4. Document patterns in project memories

# CRITICAL: CODE OPERATIONS RULE
  For ALL code search and editing operations:
  1. Use Serena MCP tools (find_symbol, replace_symbol_body, etc.) as PRIMARY method
  2. Use @agent-context7-docs-searcher for all documentation research
  3. Traditional tools (grep, sed) are FALLBACK ONLY
  4. This applies to ALL agents and subagents

## IMPORTANT: Documentation Research Before Coding
  **ALWAYS use @agent-context7-docs-searcher BEFORE writing any code:**
  - Invoke this subagent to research language, library, and framework usage
  - Provides best practices, patterns, and implementation guidance
  - Ensures code follows current standards and avoids antipatterns
  - Example: `@agent-context7-docs-searcher "Research React hooks best practices for data fetching"`

## Serena MCP Server - Semantic Code Intelligence

### Overview
Serena MCP is a semantic code analysis and manipulation server that provides intelligent, symbol-aware operations for codebases. It should be used as the PRIMARY method for ALL code operations, with traditional tools (grep, sed, etc.) only as fallbacks.

### Core Capabilities

#### Search Code (ALWAYS use these first)
- **Find symbols**: `mcp__serena__find_symbol(name_path="ClassName", include_body=true)`
  - Searches for code entities by name path pattern
  - Supports depth parameter to retrieve children (e.g., methods of a class)
  - Can include/exclude specific symbol kinds (classes, functions, variables, etc.)
  
- **Find references**: `mcp__serena__find_referencing_symbols(name_path="methodName", relative_path="file.py")`
  - Finds all references to a specific symbol
  - Returns metadata and code snippets around references
  
- **Pattern search**: `mcp__serena__search_for_pattern(substring_pattern="TODO|FIXME")`
  - Flexible regex search across codebase
  - Supports file inclusion/exclusion globs
  - Can restrict to code files only
  
- **Symbol overview**: `mcp__serena__get_symbols_overview(relative_path="src/")`
  - High-level understanding of symbols in a file
  - Shows top-level classes, functions, variables
  - Essential first step when exploring new files

#### File Operations
- **List directory**: `mcp__serena__list_dir(relative_path=".", recursive=true)`
  - Lists non-gitignored files and directories
  
- **Find files**: `mcp__serena__find_file(file_mask="*.py", relative_path=".")`
  - Finds files matching patterns using wildcards

#### Edit Code (PREFER symbol-based operations)
- **Replace symbol body**: `mcp__serena__replace_symbol_body(name_path="functionName", relative_path="file.py", body="new code")`
  - Replaces entire function/class/method body
  - Preserves indentation and context
  
- **Insert before symbol**: `mcp__serena__insert_before_symbol(name_path="className", body="imports")`
  - Ideal for adding imports or new top-level definitions
  
- **Insert after symbol**: `mcp__serena__insert_after_symbol(name_path="methodName", body="new method")`
  - Adds new methods, functions, or classes after existing ones

#### Memory Management
- **Write memory**: `mcp__serena__write_memory(memory_name="architecture_overview", content="...")`
  - Store important project information for future reference
  
- **Read memory**: `mcp__serena__read_memory(memory_file_name="architecture_overview.md")`
  - Retrieve stored project knowledge
  
- **List memories**: `mcp__serena__list_memories()`
  - View all available memory files

#### Project Management
- **Check onboarding**: `mcp__serena__check_onboarding_performed()`
  - Verify if project onboarding is complete
  
- **Onboarding**: `mcp__serena__onboarding()`
  - Initialize project understanding

#### Thinking Tools (Use strategically)
- **Think about collected information**: `mcp__serena__think_about_collected_information()`
  - Call after completing search sequences
  
- **Think about task adherence**: `mcp__serena__think_about_task_adherence()`
  - Call before making code changes
  
- **Think about whether done**: `mcp__serena__think_about_whether_you_are_done()`
  - Call when task appears complete

### Best Practices

1. **Symbol-based editing over text replacement**
   - Use symbol operations for entire functions/classes
   - Only use regex for small, targeted changes within symbols

2. **Efficient code exploration**
   - Start with `get_symbols_overview` for new files
   - Use `find_symbol` with `include_body=false` first
   - Only read full bodies when necessary

3. **Name path patterns**
   - Simple name: `"method"` - matches any method
   - Relative path: `"class/method"` - method within class
   - Absolute path: `"/class/method"` - top-level class method

4. **Always verify before editing**
   - Use thinking tools before code changes
   - Find references before modifying public APIs
   - Check for test files that may need updates

## Knowledge Management Integration

### Documentation Research

**Use @agent-context7-docs-searcher for all documentation needs:**
- Technical guidance and best practices
- Library and framework usage
- Implementation patterns
- API documentation

**Usage Guidelines:**
- Always use the agent before implementing from scratch
- Adapt discovered patterns to project-specific requirements
- Use for both complex features and simple API usage
- Validate documentation against current best practices

## Research-Driven Development Standards

### Before Any Implementation

**Research checklist:**

- [ ] Use @agent-context7-docs-searcher to research implementation approach
- [ ] Research best practices for relevant technologies
- [ ] Understand security implications
- [ ] Check for common pitfalls or antipatterns

### Using @agent-context7-docs-searcher

**When to use:**
- Before implementing any new feature or functionality
- When working with unfamiliar libraries or frameworks
- To find the most current best practices
- To research proper API usage and patterns

**How to invoke:**
```bash
@agent-context7-docs-searcher "Research [specific topic/library/pattern]"
```

**Example invocations:**
- `@agent-context7-docs-searcher "Research TypeScript generics and type constraints"`
- `@agent-context7-docs-searcher "Find best practices for React state management"`
- `@agent-context7-docs-searcher "Research Node.js async error handling patterns"`
- `@agent-context7-docs-searcher "Find PostgreSQL connection pooling implementation"`

### Knowledge Source Prioritization

**Query Strategy:**
- Start with broad architectural queries, narrow to specific implementation
- Use @agent-context7-docs-searcher for both strategic decisions and tactical "how-to" questions
- Request cross-referencing of multiple documentation sources for validation
- Use focused topic queries for targeted results

## Quality Assurance Integration

### Code Operations Standards

**Use Serena MCP for ALL code operations:**
- [ ] All code searches performed with Serena MCP tools
- [ ] All code edits made with Serena symbol operations
- [ ] Traditional tools (grep, sed, awk) used ONLY as fallback
- [ ] Memory management for persistent project knowledge

### Research Validation

**Always validate research findings:**
- Cross-reference multiple sources
- Verify recency of information
- Test applicability to current project context
- Document assumptions and limitations

## Git and GitHub Best Practices

### Repository Information
- **Repository URL**: https://github.com/osbornesec/cpskdb
- **Owner**: Michael Osborne (michael@allthingsai.life)
- **Project**: Agentic RAG System - Locally hosted, multi-product technical data retrieval system

### Git Configuration
- **User**: Michael Osborne
- **Email**: michael@allthingsai.life
- **Default Branch**: main
- **Remote Origin**: https://github.com/osbornesec/cpskdb.git

### Commit Standards

**Commit Message Format:**

```text
<type>: <subject>

<body>

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Commit Types:**
- `feat`: New feature implementation
- `fix`: Bug fixes
- `docs`: Documentation updates
- `refactor`: Code refactoring without functionality changes
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, dependencies, configuration
- `perf`: Performance improvements
- `style`: Code formatting, style changes

**Example Commit Messages:**
- `feat: implement Qdrant vector database client with batch processing`
- `fix: resolve memory leak in embedding cache service`
- `docs: add API documentation for query endpoints`
- `refactor: extract document parsing logic into separate modules`

### Branch Management

**Branch Naming Convention:**
- `feature/task-XX-description` - New features (e.g., `feature/task-95-fastapi-structure`)
- `fix/issue-description` - Bug fixes (e.g., `fix/memory-leak-embeddings`)
- `docs/description` - Documentation updates (e.g., `docs/api-reference`)
- `refactor/description` - Code refactoring (e.g., `refactor/chunking-pipeline`)

**Workflow:**
1. Create feature branch from `main`
2. Implement changes with TDD approach
3. Commit frequently with descriptive messages
4. Push branch and create Pull Request
5. Code review and merge to `main`

### Pull Request Standards

**PR Title Format:**
`[Task XX] Description of changes`

**PR Description Template:**
```markdown
## Summary
- Brief description of changes
- Link to related task/issue

## Changes Made
- [ ] List of specific changes
- [ ] Test coverage added/updated
- [ ] Documentation updated

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Review Checklist
- [ ] Code follows project conventions
- [ ] Security considerations addressed
- [ ] Performance impact assessed
- [ ] Breaking changes documented

🤖 Generated with [Claude Code](https://claude.ai/code)
```

### Git Security Best Practices

**Never Commit:**
- API keys, tokens, or credentials
- Environment files (.env) with secrets
- Large model files or datasets
- Personal or sensitive information
- Database dumps or backups

**Pre-commit Checks:**
- Verify .gitignore patterns are working
- Run `git status` to review staged files
- Check for secrets with `git diff --cached`
- Ensure commit messages are descriptive

### File Management

**Always Ignore:**
- Python bytecode (`__pycache__/`, `*.pyc`)
- Virtual environments (`.venv/`, `venv/`)
- IDE configuration files (`.vscode/`, `.idea/`)
- OS-specific files (`.DS_Store`, `Thumbs.db`)
- Logs and temporary files (`*.log`, `tmp/`)
- AI/ML artifacts (`models/`, `*.pkl`, `embeddings/`)
- Database files (`*.db`, `dump.rdb`, `qdrant_data/`)

**Track in Git:**
- Source code and configuration templates
- Documentation and README files
- Test files and test data (small samples only)
- Build scripts and deployment configurations
- Project structure and dependency files

### Collaboration Guidelines

**Code Review Requirements:**
- All changes must go through Pull Requests
- At least one reviewer approval required
- Automated tests must pass
- Security scan must pass
- Documentation must be updated

**Issue Management:**
- Link commits to issues/tasks when applicable
- Use issue templates for consistency
- Label issues appropriately (bug, enhancement, documentation)
- Close issues via commit messages: `fixes #123`

### Backup and Recovery

**Repository Backup:**
- Primary: GitHub remote repository
- Local: Multiple clones on different machines
- Archive: Periodic downloads of repository state

**Recovery Procedures:**
- Lost work: Check `git reflog` for recent commits
- Corrupted repository: Clone fresh from GitHub
- Accidental commits: Use `git revert` instead of `git reset`
- Secret exposure: Rotate credentials immediately, use `git filter-branch` if needed

### Integration with Development Workflow

**Daily Git Operations:**
```bash
# Start of day
git pull origin main
git status

# During development
git add .
git commit -m "descriptive message"
git push origin feature-branch

# End of task
git push origin feature-branch
# Create PR via GitHub CLI or web interface
```

**Emergency Procedures:**
- **Exposed Secret**: Immediately rotate credentials, remove from history
- **Broken main**: Revert problematic commit, investigate cause
- **Merge Conflicts**: Resolve locally, test thoroughly before pushing

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
ALWAYS use @agent-context7-docs-searcher BEFORE writing any code.
ALWAYS use Serena MCP for code operations, traditional tools as fallback only.
ALWAYS use @agent-context7-docs-searcher for ALL documentation research.