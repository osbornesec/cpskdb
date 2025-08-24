#!/usr/bin/env python3
"""PreToolUse Hook to Protect All Configuration Files.

Protects pre-commit, linting, formatting, type checking, and build configuration files
from being modified by Claude. This ensures all development tools remain stable.
"""

import json
import re
import sys

# All configuration files to protect
PROTECTED_CONFIG_FILES = [
    # Pre-commit configuration
    r"\.pre-commit-config\.ya?ml$",
    r"\.pre-commit-hooks\.ya?ml$",
    r"\.pre-commit$",
    r"\.pre-commit/",
    r"\.git/hooks/",
    # Python tool configurations
    r"pyproject\.toml$",
    r"setup\.cfg$",
    r"setup\.py$",
    r"ruff\.toml$",
    r"\.ruff\.toml$",
    r"\.ruff_cache",
    r"mypy\.ini$",
    r"\.mypy\.ini$",
    r"\.mypy_cache",
    r"\.black$",
    r"black\.toml$",
    r"\.flake8$",
    r"\.pylintrc$",
    r"pylintrc$",
    r"\.pylint\.d",
    r"\.isort\.cfg$",
    r"pytest\.ini$",
    r"tox\.ini$",
    # JS/TS configurations
    r"\.eslintrc",
    r"eslint\.config\.",
    r"\.prettierrc",
    r"prettier\.config\.",
    r"tsconfig\.json$",
    r"jsconfig\.json$",
    r"pyrightconfig\.json$",
    # Workflow files
    r"\.github/workflows/.*(pre-commit|quality|lint|format)",
]

# Bash commands that might interfere with configurations
BLOCKED_CONFIG_COMMANDS = [
    # Pre-commit commands
    (
        r"pre-commit\s+(install|uninstall|autoupdate|clean)",
        "Pre-commit management should be manual",
    ),
    (r"rm\s+.*\.git/hooks/", "Git hooks manipulation blocked"),
    (r"(mv|cp|chmod)\s+.*\.git/hooks/", "Git hooks changes blocked"),
    # Config file manipulation
    (
        r"(rm|mv|cp)\s+.*(pyproject\.toml|\.pre-commit-config\.|ruff\.toml|mypy\.ini)",
        "Config file changes blocked",
    ),
    (
        r"echo.*>.*(pyproject\.toml|\.pre-commit-config\.|ruff\.toml|mypy\.ini)",
        "Writing to config blocked",
    ),
    (r"(ruff|mypy|black).*--generate-config", "Config generation blocked"),
    # Cache manipulation
    (
        r"rm\s+-rf\s+\.(pre-commit|ruff_cache|mypy_cache)",
        "Removing tool caches blocked",
    ),
]

# Content patterns that indicate config file changes
DANGEROUS_CONFIG_PATTERNS = [
    # File modification patterns
    (
        r'open\(["\'].*(pyproject\.toml|\.pre-commit-config\.|ruff\.toml|mypy\.ini)["\'].*["\']w',
        "Script writes to config files",
    ),
    (
        r'Path\(["\'].*(pyproject\.toml|\.pre-commit-config\.|ruff\.toml)["\'].*\.write',
        "Script uses Path.write on config files",
    ),
    # Library manipulation
    (
        r"(yaml|toml|json)\.dump.*(pyproject|pre.*commit|ruff|mypy)",
        "Script modifies config via library",
    ),
    (
        r"subprocess.*(ruff|mypy|black).*--generate-config",
        "Script generates new config",
    ),
    (
        r"subprocess.*pre-commit.*(install|autoupdate)",
        "Script executes pre-commit management",
    ),
    # File operations
    (
        r"shutil\.(copy|move).*(pyproject\.toml|\.pre-commit-config\.|ruff\.toml|mypy\.ini)",
        "Script copies/moves config files",
    ),
    (
        r"os\.rename.*(pyproject\.toml|\.pre-commit-config\.|ruff\.toml)",
        "Script renames config files",
    ),
]


def is_protected_config_file(file_path) -> bool:
    """Check if a file path matches protected configuration patterns."""
    if not file_path:
        return False
    path_str = str(file_path)
    for pattern in PROTECTED_CONFIG_FILES:
        if re.search(pattern, path_str, re.IGNORECASE):
            return True
    return False


def check_config_bash_command(command):
    """Check if a bash command might interfere with configurations."""
    for pattern, reason in BLOCKED_CONFIG_COMMANDS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, reason
    return True, None


def check_content_for_config_changes(content):
    """Check if file content contains code that would modify configurations."""
    if not content:
        return True, None
    for pattern, reason in DANGEROUS_CONFIG_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
            return False, reason
    return True, None


def main() -> None:
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Check file modification tools
    if tool_name in ["Write", "Edit", "MultiEdit", "Delete"]:
        file_path = tool_input.get("file_path") or tool_input.get("path", "")

        if is_protected_config_file(file_path):
            sys.exit(0)

        # For Write and Edit operations, also check the content for dangerous patterns
        if tool_name in ["Write", "Edit", "MultiEdit"]:
            content = tool_input.get("content") or tool_input.get("new_string", "")

            # Check Python and shell scripts for config manipulation
            if file_path and (
                file_path.endswith((".py", ".sh", ".bash"))
            ):
                is_valid, reason = check_content_for_config_changes(content)
                if not is_valid:
                    sys.exit(0)

    # Check Bash commands for config interference
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        is_valid, reason = check_config_bash_command(command)

        if not is_valid:
            sys.exit(0)

    # Check Read operations to provide a warning (but don't block)
    if tool_name == "Read":
        file_path = tool_input.get("file_path", "")
        if is_protected_config_file(file_path):
            pass

    # Allow the tool to proceed
    sys.exit(0)


if __name__ == "__main__":
    main()
