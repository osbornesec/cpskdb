#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""
PostToolUse Hook for Python and Markdown Quality Checks
Runs ruff and mypy after Python file modifications
Runs markdownlint-cli2 after Markdown file modifications
Runs LanguageTool for grammar/style checking
Automatically commits changes to git for safety
Validates file size limits to prevent oversized files
"""

import os
import json
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Set

# Tools that modify files
FILE_MODIFICATION_TOOLS = ["Write", "Edit", "MultiEdit", "NotebookEdit"]

# Maximum lines of code (excluding comments and empty lines)
# Default 150 LOC is a conservative choice for high-quality, maintainable modules
MAX_LINES_OF_CODE = int(os.environ.get("MAX_LINES_OF_CODE", "150"))


def get_bool_env(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "on"}


def find_project_root() -> Optional[Path]:
    """
    Find the project root by searching upwards for a .claude directory.
    The project root is defined as the directory containing the .claude folder.
    """
    current_path = Path(__file__).parent.resolve()
    while current_path != current_path.parent:
        if (current_path / ".claude").exists():
            return current_path
        current_path = current_path.parent
    # Final check at the root directory
    if (current_path / ".claude").exists():
        return current_path
    # Try git root as a fallback
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(Path(__file__).parent.resolve()),
        )
        if result.returncode == 0:
            git_root = result.stdout.strip()
            if git_root:
                return Path(git_root)
    except Exception:
        pass
    return None


def _extract_paths_from_payload(payload: Any) -> List[str]:
    paths: List[str] = []
    if payload is None:
        return paths
    # Strings
    if isinstance(payload, str):
        paths.append(payload)
        return paths
    # Lists
    if isinstance(payload, list):
        for item in payload:
            paths.extend(_extract_paths_from_payload(item))
        return paths
    # Dicts
    if isinstance(payload, dict):
        candidate_keys = [
            "file_path",
            "path",
            "file",
            "newPath",
            "oldPath",
            "to",
            "from",
            "target",
            "source",
        ]
        list_like_keys = ["files", "file_paths", "paths", "edits", "changes", "patches"]
        for k in candidate_keys:
            if k in payload:
                paths.extend(_extract_paths_from_payload(payload[k]))
        for k in list_like_keys:
            if k in payload:
                paths.extend(_extract_paths_from_payload(payload[k]))
        return paths
    return paths


def get_modified_files(tool_name: str, tool_input: Dict[str, Any], tool_response: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Extract file paths that were modified from tool input/response."""
    files: List[str] = []

    if tool_name in FILE_MODIFICATION_TOOLS:
        # Standard file modification tools – collect from known shapes
        files.extend(_extract_paths_from_payload(tool_input))
        files.extend(_extract_paths_from_payload(tool_response))

    # Dedup and keep order roughly
    seen: Set[str] = set()
    deduped: List[str] = []
    for f in files:
        if not isinstance(f, str):
            continue
        f = f.strip()
        if not f:
            continue
        if f not in seen:
            seen.add(f)
            deduped.append(f)

    # Separate Python and Markdown-like files
    python_files = [f for f in deduped if f.endswith(".py")]
    markdown_exts = (".md", ".markdown", ".mdx")
    markdown_files = [f for f in deduped if f.endswith(markdown_exts)]

    return python_files, markdown_files


def count_lines_of_code(file_path: str) -> int:
    """Count lines of code excluding comments and empty lines."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        code_lines = 0
        in_multiline_string = False
        string_delimiter = None

        for line in lines:
            line_to_process = line.strip()
            if not line_to_process:
                continue

            while True:
                if in_multiline_string:
                    delimiter_pos = line_to_process.find(string_delimiter)
                    if delimiter_pos != -1:
                        in_multiline_string = False
                        string_delimiter = None
                        line_to_process = line_to_process[delimiter_pos + 3:]
                        if not line_to_process.strip():
                            break
                    else:
                        break  # Whole line is inside multiline string

                if line_to_process.startswith("#"):
                    break

                if '"""' in line_to_process or "'''" in line_to_process:
                    delimiter = '"""' if '"""' in line_to_process else "'''"
                    if line_to_process.count(delimiter) % 2 == 1:
                        in_multiline_string = True
                        string_delimiter = delimiter
                        # Process part of the line before the multiline string
                        line_to_process = line_to_process.split(delimiter)[0]

                if line_to_process.strip():
                    code_lines += 1
                break

        return code_lines
    except Exception:
        return 0  # Return 0 if file can't be read


def validate_file_size(file_path: str) -> List[str]:
    """Validate that file doesn't exceed maximum lines of code."""
    errors: List[str] = []

    if not Path(file_path).exists():
        return errors

    if get_bool_env("SKIP_SIZE_CHECK", False):
        return errors

    line_count = count_lines_of_code(file_path)
    if line_count > MAX_LINES_OF_CODE:
        errors.append(
            f"File size violation: {file_path} has {line_count} LOC "
            f"(max: {MAX_LINES_OF_CODE}). Please split this file into smaller, more manageable modules."
        )

    return errors


def run_ruff(file_path: str) -> List[str]:
    """Run ruff linter and formatter on a Python file."""
    errors: List[str] = []

    # Run ruff check (linting)
    try:
        result = subprocess.run(
            ["ruff", "check", file_path], capture_output=True, text=True, timeout=45
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
            timeout=45,
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
            ["mypy", file_path], capture_output=True, text=True, timeout=60
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
            ["mypy", scope], capture_output=True, text=True, timeout=120
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


def run_markdownlint(file_path: str) -> List[str]:
    """Run markdownlint-cli2 on a Markdown file."""
    errors: List[str] = []

    try:
        result = subprocess.run(
            ["npx", "--yes", "markdownlint-cli2", file_path],
            capture_output=True,
            text=True,
            timeout=90,
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
            print("Warning: Could not find project root for LanguageTool check.", file=sys.stderr)
            return errors  # Could not find project root

        # Use the filtered LanguageTool script if it exists
        script_path = project_root / "scripts" / "filter_language_issues.py"
        if not script_path.exists():
            print(f"Warning: LanguageTool script not found at {script_path}", file=sys.stderr)
            return errors  # Skip if script doesn't exist

        # Use the current Python interpreter for consistency and security
        python_cmd = sys.executable

        # Run the script with the file as argument to avoid embedding
        result = subprocess.run(
            [python_cmd, str(script_path), file_path],
            capture_output=True,
            text=True,
            timeout=45,
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


def auto_commit_changes(modified_files: List[str], tool_name: str) -> None:
    """Automatically commit file changes to git for safety."""
    try:
        project_root = find_project_root()
        if not project_root:
            return  # Could not find project root

        # Check if we're in a git repository
        git_check = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            cwd=str(project_root),
            timeout=10,
        )
        if git_check.returncode != 0:
            return  # Not a git repository, skip commit

        # Stage the modified files
        staged_files = []
        for file_path in modified_files:
            # Use the given path, which might be a symlink
            p = Path(file_path)
            if not p.is_absolute():
                p = project_root / p

            try:
                relative_path = p.relative_to(project_root)
            except ValueError:
                # File is outside project root, check if it's a symlink pointing inside
                if p.is_symlink():
                    try:
                        resolved_path = p.resolve()
                        try:
                            relative_path = resolved_path.relative_to(project_root)
                        except ValueError:
                            continue
                    except Exception:
                        continue
                else:
                    continue

            if not p.exists():
                continue

            stage_result = subprocess.run(
                ["git", "add", str(relative_path)],
                capture_output=True,
                cwd=str(project_root),
                timeout=10,
            )
            if stage_result.returncode == 0:
                staged_files.append(str(relative_path))

        if not staged_files:
            return  # No files successfully staged

        # Check if there are any staged changes
        status_check = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            capture_output=True,
            cwd=str(project_root),
            timeout=10,
        )
        if status_check.returncode == 0:
            return  # No changes to commit
        # Create commit message
        file_list = ', '.join(staged_files)
        # Truncate file list if too long
        if len(file_list) > 100:
            file_list = file_list[:97] + "..."
        
        commit_lines = [
            f"chore: auto-save changes from {tool_name}",
            "",
            "Automatic safety commit after file modification via post-tool hook.",
            f"Tool: {tool_name}",
            f"Files: {file_list}",
        ]
        commit_message = "\n".join(commit_lines)

        subprocess.run(
            ["git", "commit", "-m", commit_message],
            capture_output=True,
            cwd=str(project_root),
            timeout=30,
        )

    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"Git commit skipped due to error: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Unexpected error during git commit: {e}", file=sys.stderr)


def main() -> None:
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
    python_files, markdown_files = get_modified_files(tool_name, tool_input, tool_response)
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
    for file_path in [f for f in existing_files if f.endswith(".py")]:
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
    py_existing = [f for f in existing_files if f.endswith(".py")]
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
    for file_path in [f for f in existing_files if f.endswith((".md", ".markdown", ".mdx"))]:
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
                print(f"LanguageTool suggestions for {file_path}:\n" + "\n".join(lt_errors), file=sys.stderr)

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



if __name__ == "__main__":
    main()