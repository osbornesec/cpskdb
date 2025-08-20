# Code Style and Conventions

## Development Methodology
- **Test-Driven Development (TDD)**: Write tests before implementation
- **Semantic Code Operations**: Use Serena MCP tools for all code operations
- **Documentation-First**: Research with @agent-context7-docs-searcher before coding

## Python Code Standards

### Style Guide
- Follow **PEP 8** for Python code style
- Use **type hints** for all function signatures
- Maximum line length: 100 characters (configured in black)
- Use descriptive variable and function names

### Type Annotations
- All functions must have complete type hints
- Use typing module for complex types
- Example:
  ```python
  from typing import List, Dict, Optional
  
  def process_documents(
      documents: List[Document],
      config: Optional[Dict[str, Any]] = None
  ) -> ProcessedResult:
      ...
  ```

### Documentation
- Document all public APIs
- Use docstrings for classes and functions
- Include parameter descriptions and return types
- Document complex logic inline

### Error Handling
- Use custom exceptions for domain-specific errors
- Always include meaningful error messages
- Use logging instead of print statements

### Testing Conventions
- Test files mirror source structure in tests/
- Unit tests in tests/unit/
- Integration tests in tests/integration/
- End-to-end tests in tests/e2e/
- Minimum 80% code coverage target

### Naming Conventions
- **Classes**: PascalCase (e.g., `DocumentParser`)
- **Functions/Methods**: snake_case (e.g., `process_chunk`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_CHUNK_SIZE`)
- **Private methods**: prefix with underscore (e.g., `_validate_input`)

### File Organization
- One class per file for major components
- Related utilities grouped in modules
- Clear separation of concerns (API, business logic, data access)

### Import Order
1. Standard library imports
2. Third-party library imports
3. Local application imports
(Groups separated by blank lines)

### Async/Await
- Use async/await for I/O operations
- FastAPI endpoints should be async when possible
- Proper async context management