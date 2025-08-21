#!/bin/bash
# LanguageTool Setup Script for CPSKDB Project

set -e

echo "Setting up LanguageTool for CPSKDB project..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment and install LanguageTool
echo "Installing LanguageTool..."
source .venv/bin/activate
pip install --upgrade language_tool_python

# Update requirements file
echo "Updating requirements.txt..."
pip freeze > requirements.txt

# Test installation
echo "Testing LanguageTool installation..."
python scripts/test_languagetool.py

echo "LanguageTool setup complete!"
echo ""
echo "To use LanguageTool:"
echo "1. Activate virtual environment: source .venv/bin/activate"
echo "2. Run test: python scripts/test_languagetool.py"
echo "3. Use in scripts: import language_tool_python"