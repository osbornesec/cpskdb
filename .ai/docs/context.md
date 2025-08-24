# Python Coding Standards Research - Production RAG System

## Research Query
Comprehensive Python coding style guidelines and best practices for production RAG system with:
- Python PEP 8 and modern extensions
- FastAPI best practices
- Async Python standards
- Type annotations with mypy
- pytest conventions
- Error handling and logging
- Import organization
- Documentation standards
- Security practices
- Performance optimization

## Target Stack
- FastAPI
- LangGraph
- Qdrant
- Modern Python async patterns

---

## Research Results

### 1. Python PEP 8 Style Guidelines

**Core PEP 8 Principles**:
- Line length: 79 characters for code, 72 for docstrings/comments
- Indentation: 4 spaces per level
- Naming conventions:
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
  - Private attributes: `_leading_underscore`

**Modern Extensions**:
- PEP 484: Type hints
- PEP 526: Variable annotations
- PEP 563: Postponed evaluation of annotations
- Black formatter compatibility (88 character line length acceptable)

### 2. FastAPI Best Practices

**Project Structure**:
```python
app/
├── __init__.py
├── main.py          # FastAPI app instance
├── dependencies.py  # Shared dependencies
├── routers/         # API route modules
├── models/          # Pydantic models
├── services/        # Business logic
└── core/           # Configuration, security
```

**Route Organization**:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

router = APIRouter(prefix="/api/v1", tags=["items"])

@router.post("/items/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    item: ItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ItemResponse:
    """Create new item with proper error handling."""
    try:
        return await item_service.create(db, item, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
```

**Dependency Injection**:
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### 3. Async Python Standards

**Async Function Naming**:
- Prefix with `async_` or use descriptive async verbs: `fetch_data`, `process_documents`
- Avoid blocking calls in async functions

**Context Managers**:
```python
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

@asynccontextmanager
async def managed_resource() -> AsyncGenerator[Resource, None]:
    resource = await acquire_resource()
    try:
        yield resource
    finally:
        await resource.cleanup()

# Usage
async with managed_resource() as resource:
    await resource.process()
```

**Error Handling**:
```python
async def robust_async_operation() -> Result:
    try:
        async with asyncio.timeout(30):  # Python 3.11+
            result = await external_api_call()
            return result
    except asyncio.TimeoutError:
        logger.error("Operation timed out")
        raise ServiceUnavailableError("External service timeout")
    except Exception as e:
        logger.exception("Unexpected error in async operation")
        raise
```

### 4. Type Annotation Best Practices

**Comprehensive Type Coverage**:
```python
from typing import Optional, List, Dict, Any, Union, TypeVar, Generic, Protocol
from collections.abc import Callable, Awaitable
from pydantic import BaseModel

T = TypeVar('T')
U = TypeVar('U')

class Repository(Protocol[T]):
    async def find_by_id(self, id: int) -> Optional[T]: ...
    async def create(self, entity: T) -> T: ...

class Service(Generic[T]):
    def __init__(self, repo: Repository[T]) -> None:
        self._repo = repo

    async def get_or_create(self, id: int, factory: Callable[[], T]) -> T:
        entity = await self._repo.find_by_id(id)
        if entity is None:
            entity = factory()
            await self._repo.create(entity)
        return entity
```

**Mypy Configuration** (pyproject.toml):
```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
```

### 5. Test Organization (pytest)

**Directory Structure**:
```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Fast, isolated tests
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/             # Service interactions
│   ├── test_api_routes.py
│   ├── test_database.py
│   └── test_external_apis.py
└── e2e/                     # End-to-end workflows
    ├── test_user_journeys.py
    └── test_system_flows.py
```

**Naming Conventions**:
```python
import pytest
from unittest.mock import Mock, AsyncMock
from httpx import AsyncClient

class TestUserService:
    """Test suite for UserService class."""

    @pytest.fixture
    async def user_service(self, mock_db_session) -> UserService:
        return UserService(mock_db_session)

    async def test_create_user_success(self, user_service: UserService):
        """Test successful user creation with valid data."""
        # Arrange
        user_data = UserCreate(email="test@example.com", name="Test User")

        # Act
        result = await user_service.create_user(user_data)

        # Assert
        assert result.email == user_data.email
        assert result.id is not None

    async def test_create_user_duplicate_email_raises_error(self, user_service: UserService):
        """Test that duplicate email raises appropriate error."""
        with pytest.raises(DuplicateEmailError, match="Email already exists"):
            await user_service.create_user(duplicate_user_data)
```

### 6. Error Handling and Logging

**Structured Logging**:
```python
import logging
import structlog
from typing import Any, Dict

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

async def process_document(doc_id: str) -> ProcessResult:
    """Process document with comprehensive logging."""
    logger.info("Starting document processing", doc_id=doc_id)

    try:
        # Processing logic
        result = await _process_document_internal(doc_id)
        logger.info(
            "Document processing completed successfully",
            doc_id=doc_id,
            processing_time=result.processing_time,
            chunks_created=len(result.chunks)
        )
        return result

    except DocumentNotFoundError:
        logger.warning("Document not found", doc_id=doc_id)
        raise
    except ProcessingError as e:
        logger.error(
            "Document processing failed",
            doc_id=doc_id,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        raise
    except Exception:
        logger.exception("Unexpected error during document processing", doc_id=doc_id)
        raise
```

**Custom Exception Hierarchy**:
```python
class CPSKDBError(Exception):
    """Base exception for all CPSKDB errors."""

class ValidationError(CPSKDBError):
    """Data validation failed."""

class DocumentNotFoundError(CPSKDBError):
    """Requested document does not exist."""

class ProcessingError(CPSKDBError):
    """Document processing failed."""

class ExternalServiceError(CPSKDBError):
    """External service integration error."""

    def __init__(self, service_name: str, message: str, status_code: Optional[int] = None):
        self.service_name = service_name
        self.status_code = status_code
        super().__init__(f"{service_name}: {message}")
```

### 7. Import Organization

**Import Ordering (isort configuration)**:
```toml
[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["cpskdb"]
known_third_party = ["fastapi", "qdrant_client", "langchain"]
sections = ["FUTURE", "STDLIB", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"]
```

**Import Structure**:
```python
# Standard library imports
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

# Third-party imports
import structlog
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, Field, validator
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Local application imports
from cpskdb.core.config import settings
from cpskdb.core.security import get_current_user
from cpskdb.models.base import BaseEntity
from cpskdb.models.document import Document, DocumentCreate
from cpskdb.services.embedding import EmbeddingService
from cpskdb.services.retrieval import RetrievalService
```

### 8. Documentation Standards

**Docstring Format (Google Style)**:
```python
async def retrieve_similar_documents(
    query: str,
    limit: int = 10,
    threshold: float = 0.7,
    collection_name: Optional[str] = None
) -> List[SimilarDocument]:
    """Retrieve documents similar to the query using vector search.

    Performs semantic similarity search using embeddings and returns
    the most relevant documents above the specified threshold.

    Args:
        query: The search query text to find similar documents for.
        limit: Maximum number of documents to return. Must be positive.
        threshold: Minimum similarity score threshold (0.0 to 1.0).
        collection_name: Optional collection to search within. If None,
            searches across all collections.

    Returns:
        List of SimilarDocument objects sorted by similarity score
        in descending order.

    Raises:
        ValidationError: If query is empty or limit/threshold are invalid.
        RetrievalError: If the vector search operation fails.
        ExternalServiceError: If the embedding service is unavailable.

    Example:
        >>> docs = await retrieve_similar_documents(
        ...     "machine learning algorithms",
        ...     limit=5,
        ...     threshold=0.8
        ... )
        >>> print(f"Found {len(docs)} similar documents")
    """
```

**Code Comments**:
```python
# Business logic: Apply similarity threshold filtering
# This prevents returning documents with weak semantic similarity
# that could confuse the downstream RAG synthesis process
filtered_results = [
    doc for doc in search_results
    if doc.similarity_score >= threshold
]

# Performance optimization: Batch embedding requests
# Group multiple queries to reduce API calls and latency
if len(queries) > BATCH_THRESHOLD:
    embeddings = await self._embedding_service.embed_batch(queries)
else:
    embeddings = [await self._embedding_service.embed(q) for q in queries]
```

### 9. Security Best Practices

**Input Validation**:
```python
from pydantic import BaseModel, Field, validator
import re

class DocumentUpload(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=1_000_000)
    content_type: str = Field(..., regex=r'^(text/plain|application/pdf|text/markdown)$')

    @validator('title')
    def validate_title(cls, v: str) -> str:
        # Prevent XSS in titles
        if re.search(r'[<>"\']', v):
            raise ValueError('Title contains invalid characters')
        return v.strip()

    @validator('content')
    def validate_content(cls, v: str) -> str:
        # Basic content sanitization
        if len(v.encode('utf-8')) > 10_000_000:  # 10MB limit
            raise ValueError('Content too large')
        return v
```

**Authentication & Authorization**:
```python
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Verify JWT token and return authenticated user."""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        return await get_user_by_id(user_id)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

@router.post("/documents/")
async def create_document(
    doc: DocumentCreate,
    current_user: User = Depends(verify_token)
) -> DocumentResponse:
    # Authorization check
    if not current_user.can_create_documents:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
```

### 10. Performance Optimization

**Database Optimization**:
```python
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select

class DocumentRepository:
    async def get_documents_with_chunks(self, user_id: int) -> List[Document]:
        """Efficiently load documents with their chunks using eager loading."""
        stmt = (
            select(Document)
            .options(
                selectinload(Document.chunks),  # Separate query for chunks
                joinedload(Document.user)       # Join for user data
            )
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()
```

**Caching Strategy**:
```python
from functools import lru_cache
from typing import Optional
import asyncio

class EmbeddingService:
    def __init__(self):
        self._cache: Dict[str, List[float]] = {}
        self._cache_lock = asyncio.Lock()

    @lru_cache(maxsize=1000)
    def _normalize_text(self, text: str) -> str:
        """Cache text normalization for repeated queries."""
        return text.lower().strip()

    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding with async caching."""
        cache_key = self._normalize_text(text)

        async with self._cache_lock:
            if cache_key in self._cache:
                return self._cache[cache_key]

        # Generate embedding
        embedding = await self._client.embed(text)

        async with self._cache_lock:
            self._cache[cache_key] = embedding

        return embedding
```

**Connection Pooling**:
```python
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

class QdrantManager:
    def __init__(self, host: str, port: int, timeout: int = 30):
        self.client = QdrantClient(
            host=host,
            port=port,
            timeout=timeout,
            # Connection pooling configuration
            prefer_grpc=True,
            grpc_port=6334,
            # HTTP connection pooling
            pool_connections=20,
            pool_maxsize=20,
            max_retries=3,
        )
```

---

## Summary of Key Guidelines

1. **Style**: Follow PEP 8 with Black compatibility (88 chars)
2. **Structure**: Use dependency injection and clear separation of concerns
3. **Async**: Proper async/await patterns with context managers
4. **Types**: Comprehensive type hints with mypy strict mode
5. **Testing**: Organized test suites with clear naming
6. **Errors**: Structured logging with custom exception hierarchy
7. **Imports**: Consistent ordering with isort
8. **Docs**: Google-style docstrings with examples
9. **Security**: Input validation, authentication, and authorization
10. **Performance**: Caching, connection pooling, and efficient queries

These guidelines form a comprehensive foundation for production-quality Python development in your RAG system.
