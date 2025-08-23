"""
Markdown quality checks using markdownlint and LanguageTool.
"""

import subprocess
import sys
from typing import List
from .config import MARKDOWNLINT_TIMEOUT, LANGUAGETOOL_TIMEOUT, get_bool_env
from .utils import find_project_root


def run_markdownlint(file_path: str) -> List[str]:
    """Run markdownlint-cli2 on a Markdown file."""
    errors: List[str] = []

    try:
        result = subprocess.run(
            ["npx", "--yes", "markdownlint-cli2", file_path],
            capture_output=True,
            text=True,
            timeout=MARKDOWNLINT_TIMEOUT,
        )
        if result.returncode != 0:
            error_output = result.stderr if result.stderr.strip() else result.stdout
            errors.append(f"Markdownlint issues:\n{error_output}")
    except subprocess.TimeoutExpired:
        errors.append(f"Markdownlint timed out for {file_path}")
    except FileNotFoundError:
        if get_bool_env("STRICT_MARKDOWN", False):
            errors.append("npx not found. Install Node.js and npm/npx")
        else:
            print("Warning: npx not found. Skipping markdownlint.", file=sys.stderr)
    except OSError as e:
        errors.append(f"Markdownlint execution error: {e}")

    return errors


def run_languagetool(file_path: str) -> List[str]:
    """Run LanguageTool filtered check on a file."""
    errors: List[str] = []

    try:
        project_root = find_project_root()
        if not project_root:
            print(
                "Warning: Could not find project root for LanguageTool check.",
                file=sys.stderr,
            )
            return errors  # Could not find project root

        # Use the filtered LanguageTool script if it exists
        script_path = project_root / "scripts" / "filter_language_issues.py"
        if not script_path.exists():
            print(
                f"Warning: LanguageTool script not found at {script_path}",
                file=sys.stderr,
            )
            return errors  # Skip if script doesn't exist

        # Use the current Python interpreter for consistency and security
        python_cmd = sys.executable

        # Run the script with the file as argument to avoid embedding
        result = subprocess.run(
            [python_cmd, str(script_path), file_path],
            capture_output=True,
            text=True,
            timeout=LANGUAGETOOL_TIMEOUT,
            cwd=str(project_root),
        )

        if result.returncode == 0 and result.stdout.strip():
            errors.append(f"LanguageTool grammar/style suggestions:\n{result.stdout}")
        elif result.stderr.strip():
            print(f"LanguageTool script error: {result.stderr}", file=sys.stderr)

    except subprocess.TimeoutExpired:
        errors.append(f"LanguageTool timed out for {file_path}")
    except Exception as e:
        print(f"LanguageTool error: {e}", file=sys.stderr)

    return errors
