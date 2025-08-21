#!/bin/bash
# LanguageTool Setup Script for CPSKDB Project

set -euo pipefail

echo "Setting up LanguageTool for CPSKDB project..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment and install LanguageTool
echo "Installing LanguageTool..."
# shellcheck source=.venv/bin/activate disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
# Install a specific version to keep determinism; keep this in sync with requirements.txt
python -m pip install "language_tool_python==2.9.4"

# Optionally update a lock file instead of clobbering requirements.txt
if [ "${UPDATE_REQUIREMENTS_LOCK:-0}" = "1" ]; then
  echo "Updating requirements.lock..."
  python -m pip freeze > requirements.lock
fi

# Test installation
echo "Testing LanguageTool installation..."
python scripts/test_languagetool.py

echo "LanguageTool setup complete!"
echo ""
echo "To use LanguageTool:"
echo "1. Activate virtual environment: source .venv/bin/activate"
echo "2. Run test: python scripts/test_languagetool.py"
echo "3. Use in scripts: import language_tool_python"
echo "4. When done: deactivate"