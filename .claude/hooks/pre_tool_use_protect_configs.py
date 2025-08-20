#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""
PreToolUse Hook to Protect Linting/Formatting/Type Checking Configs
Blocks modifications to configuration files for code quality tools
"""

import json
import sys
import re

# Configuration files to protect
PROTECTED_CONFIG_FILES = [
    # Claude Code hooks and settings - HIGHEST PRIORITY
    r"\.claude/settings\.json$",
    r"\.claude/settings\.local\.json$",
    r"\.claude/hooks/",
    r"\.claude/.*\.py$",  # Any Python file in .claude directory
    
    # Ruff configurations
    r"ruff\.toml$",
    r"\.ruff\.toml$",
    r"pyproject\.toml$",  # Often contains ruff config
    r"\.ruff_cache",
    # Mypy configurations
    r"mypy\.ini$",
    r"\.mypy\.ini$",
    r"setup\.cfg$",  # Can contain mypy config
    r"\.mypy_cache",
    # Black configurations
    r"\.black$",
    r"black\.toml$",
    # Flake8 configurations
    r"\.flake8$",
    r"setup\.cfg$",
    r"tox\.ini$",
    # Pylint configurations
    r"\.pylintrc$",
    r"pylintrc$",
    r"\.pylint\.d",
    # isort configurations
    r"\.isort\.cfg$",
    # Pre-commit configurations
    r"\.pre-commit-config\.yaml$",
    # ESLint (for JS/TS)
    r"\.eslintrc",
    r"eslint\.config\.",
    # Prettier (for JS/TS)
    r"\.prettierrc",
    r"prettier\.config\.",
    # TypeScript configurations
    r"tsconfig\.json$",
    r"jsconfig\.json$",
    # Pyright configurations
    r"pyrightconfig\.json$",
    # General Python project configs that might contain tool settings
    r"setup\.py$",
    r"pytest\.ini$",
    r"tox\.ini$",
]

# Bash commands that might change configurations
BLOCKED_CONFIG_COMMANDS = [
    # Commands that generate new config files
    (r"ruff\s+.*--generate-config", "Generating new ruff config blocked"),
    (r"mypy\s+.*--install-types", "Installing mypy types could affect type checking"),
    (r"black\s+.*--config", "Changing black config blocked"),
    (r"pylint\s+.*--generate-rcfile", "Generating pylint config blocked"),
    (r"eslint\s+.*--init", "ESLint initialization blocked"),
    # Commands that might overwrite configs
    (
        r"echo.*>.*\.(ruff|mypy|black|flake8|pylint|eslint|prettier)",
        "Writing to config file blocked",
    ),
    (
        r"cat.*>.*\.(ruff|mypy|black|flake8|pylint|eslint|prettier)",
        "Writing to config file blocked",
    ),
    (
        r"printf.*>.*\.(ruff|mypy|black|flake8|pylint|eslint|prettier)",
        "Writing to config file blocked",
    ),
    # Moving or copying config files
    (
        r"(mv|cp)\s+.*\.(ruff|mypy|black|flake8|pylint|eslint|prettier)",
        "Moving/copying config files blocked",
    ),
    (r"(mv|cp)\s+.*pyproject\.toml", "Moving/copying pyproject.toml blocked"),
    (r"(mv|cp)\s+.*pyrightconfig\.json", "Moving/copying pyrightconfig.json blocked"),
    # Removing config files
    (
        r"rm\s+.*\.(ruff|mypy|black|flake8|pylint|eslint|prettier)",
        "Removing config files blocked",
    ),
    (r"rm\s+.*pyproject\.toml", "Removing pyproject.toml blocked"),
    (r"rm\s+.*pyrightconfig\.json", "Removing pyrightconfig.json blocked"),
]


def is_protected_config(file_path):
    """Check if a file path matches protected configuration patterns."""
    if not file_path:
        return False

    # Normalize the path
    path_str = str(file_path)

    for pattern in PROTECTED_CONFIG_FILES:
        if re.search(pattern, path_str, re.IGNORECASE):
            return True
    return False


def check_bash_command(command):
    """Check if a bash command might modify configuration files."""
    for pattern, reason in BLOCKED_CONFIG_COMMANDS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, reason
    return True, None


def check_file_content_for_config_changes(content):
    """Check if file content contains code that would modify config files."""
    if not content:
        return True, None

    # Patterns that indicate config file modification in scripts
    dangerous_patterns = [
        # Python patterns
        (
            r'open\(["\'].*\.(ruff|mypy|black|flake8|pylint|eslint|prettier).*["\'].*["\']w',
            "Script attempts to write to config files",
        ),
        (
            r'open\(["\'].*pyproject\.toml["\'].*["\']w',
            "Script attempts to write to pyproject.toml",
        ),
        (
            r'open\(["\'].*pyrightconfig\.json["\'].*["\']w',
            "Script attempts to write to pyrightconfig.json",
        ),
        (
            r'Path\(["\'].*\.(ruff|mypy|black|flake8|pylint)["\'].*\.write',
            "Script uses Path.write to modify config files",
        ),
        # Shell script patterns
        (
            r"echo.*>.*\.(ruff|mypy|black|flake8|pylint|eslint|prettier)",
            "Script redirects output to config file",
        ),
        (
            r"cat.*>.*\.(ruff|mypy|black|flake8|pylint|eslint|prettier)",
            "Script redirects cat to config file",
        ),
        (
            r"printf.*>.*\.(ruff|mypy|black|flake8|pylint|eslint|prettier)",
            "Script redirects printf to config file",
        ),
        (
            r"sed.*-i.*\.(ruff|mypy|black|flake8|pylint|eslint|prettier)",
            "Script uses sed to modify config file in-place",
        ),
        (r"ruff.*--generate-config", "Script generates new ruff config"),
        (r"pylint.*--generate-rcfile", "Script generates new pylint config"),
        # File operation patterns
        (
            r"shutil\.copy.*\.(ruff|mypy|black|flake8|pylint)",
            "Script copies to config file",
        ),
        (
            r"shutil\.move.*\.(ruff|mypy|black|flake8|pylint)",
            "Script moves to config file",
        ),
        (
            r"os\.rename.*\.(ruff|mypy|black|flake8|pylint)",
            "Script renames to config file",
        ),
        (
            r"subprocess.*ruff.*--generate-config",
            "Script runs command to generate config",
        ),
        # JSON/TOML manipulation
        (r"toml\.dump.*pyproject", "Script modifies pyproject.toml via toml library"),
        (
            r"json\.dump.*pyrightconfig",
            "Script modifies pyrightconfig.json via json library",
        ),
    ]

    for pattern, reason in dangerous_patterns:
        if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
            return False, reason

    return True, None


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Check file modification tools
    if tool_name in ["Write", "Edit", "MultiEdit", "Delete"]:
        file_path = tool_input.get("file_path") or tool_input.get("path", "")

        if is_protected_config(file_path):
            output = {
                "decision": "block",
                "reason": f"Modification of linting/formatting/type checking configuration file '{file_path}' is blocked. These configurations should remain stable to ensure consistent code quality checks.",
            }
            print(json.dumps(output))
            sys.exit(0)

        # For Write and Edit operations, also check the content for dangerous patterns
        if tool_name in ["Write", "Edit", "MultiEdit"]:
            content = tool_input.get("content") or tool_input.get("new_string", "")

            # Only check Python and shell scripts
            if file_path and (
                file_path.endswith(".py")
                or file_path.endswith(".sh")
                or file_path.endswith(".bash")
            ):
                is_valid, reason = check_file_content_for_config_changes(content)
                if not is_valid:
                    output = {
                        "decision": "block",
                        "reason": f"Script creation blocked: {reason}. Scripts that modify configuration files are not allowed.",
                    }
                    print(json.dumps(output))
                    sys.exit(0)

    # Check ALL Serena MCP tools that could modify files
    if tool_name.startswith("mcp__serena__"):
        # Tools that directly modify files
        modification_tools = [
            "mcp__serena__replace_symbol_body",
            "mcp__serena__insert_after_symbol",
            "mcp__serena__insert_before_symbol",
            "mcp__serena__replace_regex",
            "mcp__serena__write_file",
            "mcp__serena__edit_file",
            "mcp__serena__delete_file",
            "mcp__serena__rename_file",
            "mcp__serena__move_file",
        ]

        if tool_name in modification_tools:
            # Check for relative_path or file_path parameters
            file_path = (
                tool_input.get("relative_path")
                or tool_input.get("file_path")
                or tool_input.get("path", "")
            )

            if is_protected_config(file_path):
                output = {
                    "decision": "block",
                    "reason": f"Modification of configuration file '{file_path}' via Serena MCP tool '{tool_name}' is blocked. Linting/formatting/type checking configs should remain stable.",
                }
                print(json.dumps(output))
                sys.exit(0)

            # Also check for destination in rename/move operations
            dest_path = (
                tool_input.get("destination")
                or tool_input.get("dest_path")
                or tool_input.get("new_path", "")
            )
            if dest_path and is_protected_config(dest_path):
                output = {
                    "decision": "block",
                    "reason": f"Creating/overwriting configuration file '{dest_path}' via Serena MCP is blocked. Config files should remain stable.",
                }
                print(json.dumps(output))
                sys.exit(0)

    # Check Bash commands
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        is_valid, reason = check_bash_command(command)

        if not is_valid:
            output = {
                "decision": "block",
                "reason": f"Command blocked: {reason}. Configuration files for linting/formatting/type checking should not be modified.",
            }
            print(json.dumps(output))
            sys.exit(0)

    # Check Read operations to provide a warning (but don't block)
    if tool_name == "Read":
        file_path = tool_input.get("file_path", "")
        if is_protected_config(file_path):
            print(
                f"Note: Reading protected config file '{file_path}'. Modifications to this file will be blocked.",
                file=sys.stderr,
            )

    # Allow the tool to proceed
    sys.exit(0)


if __name__ == "__main__":
    main()
