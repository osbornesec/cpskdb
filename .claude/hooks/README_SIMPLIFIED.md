# Simplified Claude Hooks Configuration

## Overview

The hooks have been simplified to focus only on automatic commits, with all quality checks moved to pre-commit hooks for better performance and integration.

## Current Configuration

### PreToolUse Hook: `pre_tool_use_protect_precommit.py`

**Purpose**: Protect ALL configuration files from being modified by Claude

**What it protects**:
- ✅ Pre-commit configuration (`.pre-commit-config.yaml`, `.git/hooks/`, etc.)
- ✅ Python tool configs (`pyproject.toml`, `ruff.toml`, `mypy.ini`, etc.)
- ✅ JS/TS tool configs (`.eslintrc`, `.prettierrc`, `tsconfig.json`, etc.)
- ✅ Build configs (`setup.py`, `setup.cfg`, `pytest.ini`, `tox.ini`)
- ✅ Related workflow files and cache directories

**Blocked operations**:
- ❌ Configuration file generation commands (`ruff --generate-config`, etc.)
- ❌ Direct config file manipulation (edit, move, copy, delete)
- ❌ Writing to any configuration files
- ❌ Scripts that modify configuration files

### PostToolUse Hook: `post_tool_use_commit_only.py`

**Purpose**: Automatically commit changes after Write, Edit, and MultiEdit operations

**What it does**:
- ✅ Auto-commits modified files for safety/version control
- ✅ Uses existing git utilities for reliable commit handling
- ✅ Exits gracefully on any errors (non-blocking)

**What it does NOT do** (moved to pre-commit hooks):
- ❌ No ruff formatting/linting 
- ❌ No mypy type checking
- ❌ No markdownlint validation
- ❌ No LanguageTool grammar checking
- ❌ No file size validation

## Benefits

1. **Faster**: Only commits, no quality checks during development
2. **Better Integration**: Pre-commit hooks handle quality at commit time
3. **Non-blocking**: Never interrupts workflow with quality failures
4. **Focused**: Single responsibility - just version control safety

## Environment Variables

- `DISABLE_AUTO_COMMIT=true` - Disables automatic commits entirely
- `GIT_TIMEOUT` - Timeout for git operations (default from config)

## Files Structure

```
.claude/hooks/
├── post_tool_use_commit_only.py       # Simplified commit-only hook (85 lines)
├── pre_tool_use_protect_precommit.py  # Comprehensive config protection (176 lines)
├── README_SIMPLIFIED.md               # This documentation
├── python_check/                      # Core utilities (simplified)
│   ├── __init__.py                    # Module exports
│   ├── config.py                      # Configuration constants
│   ├── file_extractor.py              # File path extraction
│   ├── git_utils.py                   # Git commit automation
│   └── utils.py                       # Project root discovery
└── settings.json.bak                  # Updated hook configuration
```

**Removed Files** (no longer needed):
- ❌ `post_tool_use_python_check.py` - Complex quality checking hook
- ❌ `post_tool_use_python_check_new.py` - Alternate version
- ❌ `python_check/main.py` - Quality checking main entry
- ❌ `python_check/python_checker.py` - Ruff/mypy quality checks
- ❌ `python_check/markdown_checker.py` - Markdown quality checks
- ❌ `python_check/size_validator.py` - File size validation
- ❌ `python_check/README.md` - Old documentation

When you're ready to enable hooks, copy `settings.json.bak` to `settings.json`.