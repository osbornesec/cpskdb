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


def parse_input() -> tuple[str, dict, dict]:
    """Parse and validate JSON input from stdin.
    
    Returns:
        tuple: (tool_name, tool_input, tool_response)
        
    Exits:
        1: If JSON is invalid
    """
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    tool_response = input_data.get("tool_response", {})
    
    return tool_name, tool_input, tool_response


def collect_and_resolve_files(
    tool_name: str, tool_input: dict, tool_response: dict, project_root: Path
) -> tuple[List[str], List[str], List[str]]:
    """Collect and resolve modified files from tool data.
    
    Args:
        tool_name: Name of the tool that was used
        tool_input: Input data passed to the tool
        tool_response: Response data from the tool
        project_root: Project root directory path
        
    Returns:
        tuple: (python_files, markdown_files, existing_files)
        
    Exits:
        0: If tool is not a file modification tool or operation failed
    """
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

    # Deduplicate and filter out non-existent files (resolved to project root)
    unique_files = sorted(list(set(all_modified_files)))
    resolved_files: List[str] = []
    for f in unique_files:
        p = Path(f)
        abs_p = p if p.is_absolute() else (project_root / p)
        if abs_p.exists():
            resolved_files.append(str(abs_p))

    existing_files = resolved_files
    
    # Filter existing files by type
    py_existing = [f for f in existing_files if f.endswith(PYTHON_EXTENSIONS)]
    md_existing = [f for f in existing_files if f.endswith(MARKDOWN_EXTENSIONS)]
    
    return py_existing, md_existing, existing_files


def run_python_checks(py_files: List[str], project_root: Path) -> List[str]:
    """Run Python quality checks on files.
    
    Args:
        py_files: List of Python file paths to check
        project_root: Project root directory path
        
    Returns:
        List of error messages
        
    Exits:
        2: If any file exceeds size limit (critical failure)
    """
    all_errors = []
    
    # Run file size validation first (critical check)
    size_errors = []
    for file_path in py_files:
        file_size_errors = validate_file_size(file_path)
        if file_size_errors:
            size_errors.extend(file_size_errors)

    # If any file exceeds size limit, fail immediately
    if size_errors:
        for error in size_errors:
            print(error, file=sys.stderr)
        sys.exit(2)

    # Run ruff checks on each file
    for file_path in py_files:
        ruff_errors = run_ruff(file_path)
        if ruff_errors:
            all_errors.append(f"\n=== Ruff issues in {file_path} ===")
            all_errors.extend(ruff_errors)

    # Run mypy checks (batch when many files)
    if py_files:
        if len(py_files) > 3:
            mypy_errors = run_mypy_batch(py_files, project_root)
            if mypy_errors:
                all_errors.append("\n=== Mypy issues (batch) ===")
                all_errors.extend(mypy_errors)
        else:
            for file_path in py_files:
                mypy_errors = run_mypy(file_path)
                if mypy_errors:
                    all_errors.append(f"\n=== Mypy issues in {file_path} ===")
                    all_errors.extend(mypy_errors)
    
    return all_errors


def run_markdown_checks(md_files: List[str]) -> List[str]:
    """Run Markdown quality checks on files.
    
    Args:
        md_files: List of Markdown file paths to check
        
    Returns:
        List of error messages (strict errors only, non-strict printed to stderr)
    """
    all_errors = []
    
    for file_path in md_files:
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
    
    return all_errors


def main() -> None:
    """Main entry point for the post-tool use Python check."""
    # Parse input from stdin
    tool_name, tool_input, tool_response = parse_input()
    
    # Find project root
    project_root = find_project_root() or Path.cwd()
    
    # Collect and resolve modified files
    py_files, md_files, existing_files = collect_and_resolve_files(
        tool_name, tool_input, tool_response, project_root
    )
    
    # Run quality checks and collect errors
    all_errors = []
    
    # Run Python checks
    python_errors = run_python_checks(py_files, project_root)
    all_errors.extend(python_errors)
    
    # Run Markdown checks
    markdown_errors = run_markdown_checks(md_files)
    all_errors.extend(markdown_errors)
    
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
