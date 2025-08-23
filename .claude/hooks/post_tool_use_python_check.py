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

This is the main entry point that uses the modular implementation.
"""

from python_check import main

if __name__ == "__main__":
    main()
