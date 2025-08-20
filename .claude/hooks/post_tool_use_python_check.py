#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""
PostToolUse Hook for Python Quality Checks
Runs ruff and mypy after file modifications
"""

import json
import sys
import subprocess
from pathlib import Path

# Tools that modify files
FILE_MODIFICATION_TOOLS = [
    "Write",
    "Edit", 
    "MultiEdit",
    "NotebookEdit"
]

# Serena MCP tools that modify files
SERENA_MODIFICATION_TOOLS = [
    "mcp__serena__replace_symbol_body",
    "mcp__serena__insert_after_symbol",
    "mcp__serena__insert_before_symbol",
    "mcp__serena__write_memory",
]

def get_modified_files(tool_name, tool_input):
    """Extract file paths that were modified."""
    files = []
    
    if tool_name in FILE_MODIFICATION_TOOLS:
        # Standard file modification tools
        file_path = tool_input.get('file_path') or tool_input.get('path', '')
        if file_path:
            files.append(file_path)
    elif tool_name == "NotebookEdit":
        # Jupyter notebook edits
        notebook_path = tool_input.get('notebook_path', '')
        if notebook_path:
            files.append(notebook_path)
    elif tool_name in SERENA_MODIFICATION_TOOLS:
        # Serena MCP tools
        relative_path = tool_input.get('relative_path', '')
        if relative_path:
            files.append(relative_path)
    
    # Filter for Python files
    python_files = [f for f in files if f.endswith('.py')]
    return python_files

def run_ruff(file_path):
    """Run ruff linter and formatter on a Python file."""
    errors = []
    
    # Run ruff check (linting)
    try:
        result = subprocess.run(
            ['ruff', 'check', file_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            errors.append(f"Ruff linting issues:\n{result.stdout}")
    except subprocess.TimeoutExpired:
        errors.append(f"Ruff check timed out for {file_path}")
    except FileNotFoundError:
        errors.append("Ruff not found. Install with: pip install ruff")
    except Exception as e:
        errors.append(f"Ruff check error: {e}")
    
    # Run ruff format --check (formatting check)
    try:
        result = subprocess.run(
            ['ruff', 'format', '--check', file_path],
            capture_output=True,
            text=True,
            timeout=30
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

def run_mypy(file_path):
    """Run mypy type checker on a Python file."""
    errors = []
    
    try:
        result = subprocess.run(
            ['mypy', file_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            errors.append(f"Mypy type checking issues:\n{result.stdout}")
    except subprocess.TimeoutExpired:
        errors.append(f"Mypy timed out for {file_path}")
    except FileNotFoundError:
        errors.append("Mypy not found. Install with: pip install mypy")
    except Exception as e:
        errors.append(f"Mypy error: {e}")
    
    return errors

def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    
    tool_name = input_data.get('tool_name', '')
    tool_input = input_data.get('tool_input', {})
    tool_response = input_data.get('tool_response', {})
    
    # Check if this is a file modification tool
    if tool_name not in FILE_MODIFICATION_TOOLS and tool_name not in SERENA_MODIFICATION_TOOLS:
        # Not a file modification tool, exit normally
        sys.exit(0)
    
    # Check if the operation was successful
    if 'success' in tool_response and not tool_response['success']:
        # Operation failed, no need to run checks
        sys.exit(0)
    
    # Get modified Python files
    python_files = get_modified_files(tool_name, tool_input)
    
    if not python_files:
        # No Python files modified, exit normally
        sys.exit(0)
    
    # Run checks on each modified Python file
    all_errors = []
    
    for file_path in python_files:
        # Check if file exists
        if not Path(file_path).exists():
            continue
        
        # Run ruff checks
        ruff_errors = run_ruff(file_path)
        if ruff_errors:
            all_errors.append(f"\n=== Ruff issues in {file_path} ===")
            all_errors.extend(ruff_errors)
        
        # Run mypy checks
        mypy_errors = run_mypy(file_path)
        if mypy_errors:
            all_errors.append(f"\n=== Mypy issues in {file_path} ===")
            all_errors.extend(mypy_errors)
    
    # If there are any errors, report them to Claude
    if all_errors:
        error_message = "\n".join(all_errors)
        print(f"Python quality check failures detected:\n{error_message}", file=sys.stderr)
        # Exit code 2 will feed the errors back to Claude
        sys.exit(2)
    
    # All checks passed
    sys.exit(0)

if __name__ == "__main__":
    main()