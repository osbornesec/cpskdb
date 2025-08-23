# Python Check Hook - Modular Implementation

This directory contains the modular implementation of the Python and Markdown quality check hook.

## Structure

- `__init__.py` - Package initialization and main export
- `main.py` - Main entry point and orchestration logic (83 LOC)
- `config.py` - Configuration constants and environment variables (18 LOC)
- `utils.py` - Utility functions for path resolution and project detection (46 LOC)
- `file_extractor.py` - File path extraction from tool inputs/responses (55 LOC)
- `size_validator.py` - File size validation and line counting (31 LOC)
- `python_checker.py` - Python code quality checks (ruff, mypy) (80 LOC)
- `markdown_checker.py` - Markdown quality checks (markdownlint, LanguageTool) (58 LOC)
- `git_utils.py` - Git auto-commit functionality (68 LOC)

## Design Principles

1. **Single Responsibility**: Each module has a focused, single responsibility
2. **Size Compliance**: All modules are under the 150 LOC limit
3. **Clear Separation**: Logic is cleanly separated by functional domain
4. **Maintainability**: Easier to test, debug, and modify individual components
5. **Reusability**: Components can be imported and used independently

## Benefits

- **Easier Testing**: Each module can be unit tested in isolation
- **Better Maintainability**: Changes to one aspect don't affect others
- **Improved Readability**: Smaller, focused files are easier to understand
- **Modular Development**: Different developers can work on different modules
- **Selective Import**: Only needed functionality can be imported

## Usage

The main entry point (`post_tool_use_python_check.py`) imports from this package:

```python
from python_check import main

if __name__ == "__main__":
    main()
```

Individual components can also be imported directly:

```python
from python_check.python_checker import run_ruff, run_mypy
from python_check.size_validator import validate_file_size
```
