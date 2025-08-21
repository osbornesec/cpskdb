#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""
PostToolUse Hook for Python and Markdown Quality Checks
Runs ruff and mypy after Python file modifications
Runs markdownlint-cli2 after Markdown file modifications
Runs LanguageTool for grammar/style checking
"""

import json
import sys
import subprocess
from pathlib import Path

# Tools that modify files
FILE_MODIFICATION_TOOLS = ["Write", "Edit", "MultiEdit", "NotebookEdit"]

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
        file_path = tool_input.get("file_path") or tool_input.get("path", "")
        if file_path:
            files.append(file_path)
    elif tool_name == "NotebookEdit":
        # Jupyter notebook edits
        notebook_path = tool_input.get("notebook_path", "")
        if notebook_path:
            files.append(notebook_path)
    elif tool_name in SERENA_MODIFICATION_TOOLS:
        # Serena MCP tools
        relative_path = tool_input.get("relative_path", "")
        if relative_path:
            files.append(relative_path)

    # Separate Python and Markdown files
    python_files = [f for f in files if f.endswith(".py")]
    markdown_files = [f for f in files if f.endswith(".md")]

    return python_files, markdown_files


def run_ruff(file_path):
    """Run ruff linter and formatter on a Python file."""
    errors = []

    # Run ruff check (linting)
    try:
        result = subprocess.run(
            ["ruff", "check", file_path], capture_output=True, text=True, timeout=30
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
            ["ruff", "format", "--check", file_path],
            capture_output=True,
            text=True,
            timeout=30,
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
            ["mypy", file_path], capture_output=True, text=True, timeout=30
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


def run_markdownlint(file_path):
    """Run markdownlint-cli2 on a Markdown file."""
    errors = []

    try:
        result = subprocess.run(
            ["npx", "markdownlint-cli2", file_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            error_output = result.stderr if result.stderr.strip() else result.stdout
            errors.append(f"Markdownlint issues:\n{error_output}")
    except subprocess.TimeoutExpired:
        errors.append(f"Markdownlint timed out for {file_path}")
    except FileNotFoundError:
        errors.append("npx not found. Install Node.js and npm/npx")
    except Exception as e:
        errors.append(f"Markdownlint error: {e}")

    return errors


def run_languagetool(file_path):
    """Run LanguageTool filtered check on a file."""
    errors = []

    try:
        # Find project root (where .claude directory is)
        project_root = Path(__file__).parent
        # If we're in .claude/hooks, go up two levels
        if project_root.name == "hooks" and project_root.parent.name == ".claude":
            project_root = project_root.parent.parent

        # Use the filtered LanguageTool script we created
        script_path = project_root / "scripts" / "filter_language_issues.py"
        if not script_path.exists():
            return []  # Skip if script doesn't exist

        # Check if we're in a virtual environment with LanguageTool
        venv_python = project_root / ".venv" / "bin" / "python"
        if venv_python.exists():
            python_cmd = str(venv_python)
        else:
            python_cmd = "python3"

        # Create a temporary version of the script that only checks one file
        temp_script = f'''
import sys
sys.path.insert(0, "{script_path.parent}")
from filter_language_issues import check_text_filtered, language_tool_python
from pathlib import Path

file_path = "{file_path}"
try:
    tool = language_tool_python.LanguageTool("en-US")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    issues = check_text_filtered(content, tool, file_path)
    tool.close()
    
    if issues:
        for issue in issues[:3]:  # Limit to first 3 issues
            print(f"Line {{issue['line']}}: {{issue['message']}}")
            print(f"  Text: '{{issue['text']}}'")
            if issue['suggestions']:
                print(f"  Suggestions: {{', '.join(issue['suggestions'])}}")
except Exception as e:
    pass  # Silently skip LanguageTool errors
'''

        result = subprocess.run(
            [python_cmd, "-c", temp_script],
            capture_output=True,
            text=True,
            timeout=45,
            cwd=str(project_root),
        )

        if result.returncode == 0 and result.stdout.strip():
            errors.append(f"LanguageTool grammar/style suggestions:\n{result.stdout}")

    except subprocess.TimeoutExpired:
        errors.append(f"LanguageTool timed out for {file_path}")
    except Exception:
        # Silently skip LanguageTool errors to avoid breaking the hook
        pass

    return errors


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    tool_response = input_data.get("tool_response", {})

    # Check if this is a file modification tool
    if (
        tool_name not in FILE_MODIFICATION_TOOLS
        and tool_name not in SERENA_MODIFICATION_TOOLS
    ):
        # Not a file modification tool, exit normally
        sys.exit(0)

    # Check if the operation was successful
    if "success" in tool_response and not tool_response["success"]:
        # Operation failed, no need to run checks
        sys.exit(0)

    # Get modified Python and Markdown files
    python_files, markdown_files = get_modified_files(tool_name, tool_input)

    if not python_files and not markdown_files:
        # No Python or Markdown files modified, exit normally
        sys.exit(0)

    # Run checks on modified files
    all_errors = []

    # Check Python files
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

        # Run LanguageTool checks
        lt_errors = run_languagetool(file_path)
        if lt_errors:
            all_errors.append(f"\n=== LanguageTool issues in {file_path} ===")
            all_errors.extend(lt_errors)

    # Check Markdown files
    for file_path in markdown_files:
        # Check if file exists
        if not Path(file_path).exists():
            continue

        # Run markdownlint checks
        markdown_errors = run_markdownlint(file_path)
        if markdown_errors:
            all_errors.append(f"\n=== Markdownlint issues in {file_path} ===")
            all_errors.extend(markdown_errors)

        # Run LanguageTool checks
        lt_errors = run_languagetool(file_path)
        if lt_errors:
            all_errors.append(f"\n=== LanguageTool issues in {file_path} ===")
            all_errors.extend(lt_errors)

    # If there are any errors, report them to Claude
    if all_errors:
        error_message = "\n".join(all_errors)
        print(f"Quality check failures detected:\n{error_message}", file=sys.stderr)
        # Exit code 2 will feed the errors back to Claude
        sys.exit(2)

    # All checks passed
    sys.exit(0)


if __name__ == "__main__":
    main()
