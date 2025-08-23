#!/usr/bin/env python3
"""
PostToolUse Hook for Python and Markdown Quality Checks

Runs ruff and mypy after Python file modifications.
Runs markdownlint-cli2 after Markdown file modifications.
Runs LanguageTool for grammar/style checking.

Auto-commit functionality is available but disabled by default.
To enable, set the `AUTO_COMMIT` environment variable to `true`.

This script is the main entry point and uses the modular implementation
in the `python_check` directory.

Requirements:
  - ruff
  - mypy
  - markdownlint-cli2
  - languagetool-python
"""

from python_check import main

if __name__ == "__main__":
    main()
