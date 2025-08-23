"""
Main entry point for the Python check hook.
"""

import json
import sys
from pathlib import Path
from typing import List

from .config import (
    FILE_MODIFICATION_TOOLS,
    PYTHON_EXTENSIONS,
    MARKDOWN_EXTENSIONS,
    get_bool_env,
)
from .file_extractor import get_modified_files
from .git_utils import auto_commit_changes
from .markdown_checker import run_markdownlint, run_languagetool
from .python_checker import run_ruff, run_mypy, run_mypy_batch
from .size_validator import validate_file_size
from .utils import find_project_root


def main() -> None:
    """Main entry point for the post-tool use Python check."""
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    tool_response = input_data.get("tool_response", {})

    # Check if this is a file modification tool
    if tool_name not in FILE_MODIFICATION_TOOLS:
        # Not a file modification tool, exit normally
        sys.exit(0)

    # Check if the operation was successful
    if "success" in tool_response and not tool_response["success"]:
        # Operation failed, no need to run checks
        sys.exit(0)

    # Get modified Python and Markdown files
    python_files, markdown_files = get_modified_files(
        tool_name, tool_input, tool_response
    )
    all_modified_files = python_files + markdown_files

    project_root = find_project_root() or Path.cwd()

    # Deduplicate and filter out non-existent files (resolved to project root)
    unique_files = sorted(list(set(all_modified_files)))
    resolved_files: List[str] = []
    for f in unique_files:
        p = Path(f)
        abs_p = p if p.is_absolute() else (project_root / p)
        if abs_p.exists():
            resolved_files.append(str(abs_p))

    existing_files = resolved_files

    # Run file size validation first (critical check) - only for Python files
    size_errors = []
    for file_path in [f for f in existing_files if f.endswith(PYTHON_EXTENSIONS)]:
        file_size_errors = validate_file_size(file_path)
        if file_size_errors:
            size_errors.extend(file_size_errors)

    # If any file exceeds size limit, fail immediately
    if size_errors:
        for error in size_errors:
            print(error, file=sys.stderr)
        sys.exit(2)

    # Run quality checks on modified files
    all_errors = []

    # Check Python files
    py_existing = [f for f in existing_files if f.endswith(PYTHON_EXTENSIONS)]
    for file_path in py_existing:
        # Run ruff checks
        ruff_errors = run_ruff(file_path)
        if ruff_errors:
            all_errors.append(f"\n=== Ruff issues in {file_path} ===")
            all_errors.extend(ruff_errors)

    # Run mypy checks (batch when many files)
    if py_existing:
        if len(py_existing) > 3:
            mypy_errors = run_mypy_batch(py_existing, project_root)
            if mypy_errors:
                all_errors.append("\n=== Mypy issues (batch) ===")
                all_errors.extend(mypy_errors)
        else:
            for file_path in py_existing:
                mypy_errors = run_mypy(file_path)
                if mypy_errors:
                    all_errors.append(f"\n=== Mypy issues in {file_path} ===")
                    all_errors.extend(mypy_errors)

    # Check Markdown files
    for file_path in [f for f in existing_files if f.endswith(MARKDOWN_EXTENSIONS)]:
        # Run markdownlint checks
        markdown_errors = run_markdownlint(file_path)
        if markdown_errors:
            all_errors.append(f"\n=== Markdownlint issues in {file_path} ===")
            all_errors.extend(markdown_errors)

        # Run LanguageTool checks (non-blocking by default)
        lt_errors = run_languagetool(file_path)
        if lt_errors:
            if get_bool_env("STRICT_GRAMMAR", False):
                all_errors.append(f"\n=== LanguageTool issues in {file_path} ===")
                all_errors.extend(lt_errors)
            else:
                print(
                    f"LanguageTool suggestions for {file_path}:\n"
                    + "\n".join(lt_errors),
                    file=sys.stderr,
                )

    # Auto-commit changes for safety only on success and when explicitly enabled
    if not all_errors and get_bool_env("AUTO_COMMIT", False):
        auto_commit_changes(existing_files, tool_name)

    # If there are any quality errors, report them to Claude
    if all_errors:
        error_message = "\n".join(all_errors)
        print(f"Quality check failures detected:\n{error_message}", file=sys.stderr)
        # Exit code 2 will feed the errors back to Claude
        sys.exit(2)

    # All checks passed
    sys.exit(0)
