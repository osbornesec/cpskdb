"""Core configuration and constants for the Python check hook."""

import os

# Tools that modify files
FILE_MODIFICATION_TOOLS = ["Write", "Edit", "MultiEdit", "NotebookEdit"]

# Maximum lines of code (excluding comments and empty lines)
# Default 150 LOC is a conservative choice for high-quality, maintainable modules
MAX_LINES_OF_CODE = int(os.environ.get("MAX_LINES_OF_CODE", "150"))

# File extensions
PYTHON_EXTENSIONS = (".py",)
MARKDOWN_EXTENSIONS = (".md", ".markdown", ".mdx")

# Timeout values (seconds)
RUFF_TIMEOUT = 45
MYPY_TIMEOUT = 60
MYPY_BATCH_TIMEOUT = 120
MARKDOWNLINT_TIMEOUT = 90
LANGUAGETOOL_TIMEOUT = 45
GIT_TIMEOUT = 30


def get_bool_env(name: str, default: bool = False) -> bool:
    """Get boolean environment variable value."""
    val = os.environ.get(name)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "on"}
