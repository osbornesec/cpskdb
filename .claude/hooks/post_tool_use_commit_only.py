#!/usr/bin/env python3
"""Simplified PostToolUse Hook for Auto-commits Only.

Only handles automatic commits after Write, Edit, and MultiEdit operations.
All quality checks are removed since pre-commit hooks handle those.

This script automatically commits changes made by file modification tools
for safety and version control purposes.
"""

import json
import sys
from pathlib import Path

from python_check.config import FILE_MODIFICATION_TOOLS, get_bool_env
from python_check.file_extractor import get_modified_files
from python_check.git_utils import auto_commit_changes
from python_check.utils import find_project_root


def parse_input() -> tuple[str, dict, dict]:
    """Parse and validate JSON input from stdin.

    Returns:
        tuple: (tool_name, tool_input, tool_response)

    Exits:
        1: If JSON is invalid
    """
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    tool_response = input_data.get("tool_response", {})

    return tool_name, tool_input, tool_response


def get_all_modified_files(
    tool_name: str, tool_input: dict, tool_response: dict, project_root: Path
) -> list[str]:
    """Get all modified files from tool data and resolve paths.

    Args:
        tool_name: Name of the tool that was used
        tool_input: Input data passed to the tool
        tool_response: Response data from the tool
        project_root: Project root directory path

    Returns:
        List of resolved file paths that exist

    Exits:
        0: If tool is not a file modification tool or operation failed
    """
    # Check if this is a file modification tool
    if tool_name not in FILE_MODIFICATION_TOOLS:
        # Not a file modification tool, exit normally
        sys.exit(0)

    # Check if the operation was successful
    if "success" in tool_response and not tool_response["success"]:
        # Operation failed, no need to commit
        sys.exit(0)

    # Get modified files (both Python and Markdown)
    python_files, markdown_files = get_modified_files(
        tool_name, tool_input, tool_response
    )
    all_modified_files = python_files + markdown_files

    # Deduplicate and filter out non-existent files
    unique_files = sorted(set(all_modified_files))
    existing_files: list[str] = []

    for f in unique_files:
        p = Path(f)
        abs_p = p if p.is_absolute() else (project_root / p)
        if abs_p.exists():
            existing_files.append(str(abs_p))

    return existing_files


def main() -> None:
    """Main entry point for the simplified post-tool use commit hook."""
    # Parse input from stdin
    tool_name, tool_input, tool_response = parse_input()

    # Find project root
    project_root = find_project_root() or Path.cwd()

    # Get all modified files
    modified_files = get_all_modified_files(
        tool_name, tool_input, tool_response, project_root
    )

    # Auto-commit is enabled by default for this simplified hook
    # but can be disabled with environment variable
    if get_bool_env("DISABLE_AUTO_COMMIT", False):
        sys.exit(0)

    # Commit changes if we have files to commit
    if modified_files:
        auto_commit_changes(modified_files, tool_name)

    # Always exit successfully - we don't want to interrupt the workflow
    sys.exit(0)


if __name__ == "__main__":
    main()
