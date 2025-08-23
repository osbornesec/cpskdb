"""
Python code quality checks using ruff and mypy.
"""

import subprocess
import sys
from pathlib import Path
from typing import List
from .config import RUFF_TIMEOUT, MYPY_TIMEOUT, MYPY_BATCH_TIMEOUT, get_bool_env


def run_ruff(file_path: str) -> List[str]:
    """Run ruff linter and formatter on a Python file."""
    errors: List[str] = []

    # Run ruff check (linting)
    try:
        result = subprocess.run(
            ["ruff", "check", file_path],
            capture_output=True,
            text=True,
            timeout=RUFF_TIMEOUT,
        )
        if result.returncode != 0:
            errors.append(f"Ruff linting issues:\n{result.stdout}")
    except subprocess.TimeoutExpired:
        errors.append(f"Ruff check timed out for {file_path}")
    except FileNotFoundError:
        if get_bool_env("STRICT_LINT", False):
            errors.append("Ruff not found. Install with: pip install ruff")
        else:
            print("Warning: Ruff not found. Skipping ruff checks.", file=sys.stderr)
    except Exception as e:
        errors.append(f"Ruff check error: {e}")

    # Run ruff format --check (formatting check)
    try:
        result = subprocess.run(
            ["ruff", "format", "--check", file_path],
            capture_output=True,
            text=True,
            timeout=RUFF_TIMEOUT,
        )
        if result.returncode != 0:
            errors.append(f"Ruff formatting issues:\n{result.stdout}")
    except subprocess.TimeoutExpired:
        errors.append(f"Ruff format check timed out for {file_path}")
    except FileNotFoundError:
        pass  # Already reported above
    except Exception as e:
        errors.append(f"Ruff format check error: {e}")

    return errors


def run_mypy(file_path: str) -> List[str]:
    """Run mypy type checker on a Python file."""
    errors: List[str] = []

    try:
        result = subprocess.run(
            ["mypy", file_path], capture_output=True, text=True, timeout=MYPY_TIMEOUT
        )
        if result.returncode != 0:
            errors.append(f"Mypy type checking issues:\n{result.stdout}")
    except subprocess.TimeoutExpired:
        errors.append(f"Mypy timed out for {file_path}")
    except FileNotFoundError:
        if get_bool_env("STRICT_LINT", False):
            errors.append("Mypy not found. Install with: pip install mypy")
        else:
            print("Warning: Mypy not found. Skipping mypy checks.", file=sys.stderr)
    except Exception as e:
        errors.append(f"Mypy error: {e}")

    return errors


def run_mypy_batch(python_files: List[str], project_root: Path) -> List[str]:
    """Run mypy once for multiple files (project scope) when many files changed."""
    if not python_files:
        return []

    errors: List[str] = []
    try:
        # Prefer running on project root for broader context
        scope = str(project_root)
        result = subprocess.run(
            ["mypy", scope], capture_output=True, text=True, timeout=MYPY_BATCH_TIMEOUT
        )
        if result.returncode != 0:
            errors.append(f"Mypy type checking issues (batch):\n{result.stdout}")
    except subprocess.TimeoutExpired:
        errors.append("Mypy timed out for project scope")
    except FileNotFoundError:
        if get_bool_env("STRICT_LINT", False):
            errors.append("Mypy not found. Install with: pip install mypy")
        else:
            print("Warning: Mypy not found. Skipping mypy checks.", file=sys.stderr)
    except Exception as e:
        errors.append(f"Mypy error: {e}")

    return errors
