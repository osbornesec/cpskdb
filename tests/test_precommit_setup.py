"""Tests for pre-commit hooks setup."""
import os
import yaml
import pytest
import toml
import subprocess
import sys
from pathlib import Path


def _is_precommit_installed() -> bool:
    """Helper to check if pre-commit is installed."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pre_commit", "--version"],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


class TestPrecommitSetup:
    """Test suite for pre-commit hooks configuration and setup."""
    
    def test_precommit_config_file_exists_and_valid_yaml(self):
        """Test that .pre-commit-config.yaml exists and contains valid YAML structure."""
        # Arrange
        repo_root = Path(__file__).parent.parent
        config_file = repo_root / ".pre-commit-config.yaml"
        
        # Act & Assert
        assert config_file.exists(), f".pre-commit-config.yaml not found at {config_file}"
        
        # Verify it's valid YAML
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Verify basic structure
        assert isinstance(config_data, dict), "Configuration should be a dictionary"
        assert 'repos' in config_data, "Configuration should have 'repos' key"
        assert isinstance(config_data['repos'], list), "'repos' should be a list"
        assert len(config_data['repos']) > 0, "Should have at least one repository configured"
    
    def test_precommit_in_dev_dependencies(self):
        """Test that pre-commit is listed in development dependencies."""
        # Arrange
        repo_root = Path(__file__).parent.parent
        pyproject_file = repo_root / "pyproject.toml"
        
        # Act & Assert
        assert pyproject_file.exists(), "pyproject.toml should exist"
        
        with open(pyproject_file, 'r') as f:
            pyproject_data = toml.load(f)
        
        # Verify pre-commit is in dev dependencies
        assert 'project' in pyproject_data, "pyproject.toml should have 'project' section"
        assert 'optional-dependencies' in pyproject_data['project'], "Should have optional-dependencies"
        assert 'dev' in pyproject_data['project']['optional-dependencies'], "Should have 'dev' dependencies"
        
        dev_deps = pyproject_data['project']['optional-dependencies']['dev']
        pre_commit_deps = [dep for dep in dev_deps if dep.startswith('pre-commit')]
        assert len(pre_commit_deps) > 0, "pre-commit should be in dev dependencies"
    
    def test_git_repository_structure_supports_precommit(self):
        """Test that the git repository structure supports pre-commit installation."""
        # Arrange
        repo_root = Path(__file__).parent.parent
        git_dir = repo_root / ".git"
        config_file = repo_root / ".pre-commit-config.yaml"
        
        # Act & Assert
        assert git_dir.exists(), f".git directory not found at {git_dir}"
        assert git_dir.is_dir(), ".git should be a directory"
        assert config_file.exists(), f".pre-commit-config.yaml not found at {config_file}"
        
        # Verify git repository can support hooks
        hooks_dir = git_dir / "hooks"
        if hooks_dir.exists():
            assert hooks_dir.is_dir(), "hooks directory should be a directory"
    
    def test_precommit_config_includes_required_hooks(self):
        """Test that pre-commit configuration includes ruff, mypy, and standard hooks."""
        # Arrange
        repo_root = Path(__file__).parent.parent
        config_file = repo_root / ".pre-commit-config.yaml"
        
        # Act
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Assert - Extract all hook IDs from all repos
        all_hooks = []
        for repo in config_data['repos']:
            for hook in repo['hooks']:
                all_hooks.append(hook['id'])
        
        # Verify essential hooks are present (updated to include new hooks)
        required_hooks = {
            'ruff', 'ruff-format',  # Ruff linting and formatting
            'mypy',                  # Type checking
            'trailing-whitespace',   # Standard cleanup
            'end-of-file-fixer',    # Standard cleanup
            'check-yaml', 'check-toml',  # Config file validation
            'check-json', 'mixed-line-ending'  # Additional standard hooks
        }
        
        for hook in required_hooks:
            assert hook in all_hooks, f"Required hook '{hook}' not found in configuration"
    
    @pytest.mark.skipif(
        not _is_precommit_installed(),
        reason="pre-commit not installed - run 'pip install -e .[dev]' first"
    )
    def test_precommit_can_be_installed_and_executed(self):
        """Test that pre-commit can be installed and executed successfully."""
        repo_root = Path(__file__).parent.parent
        
        # Test that pre-commit command is available
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pre_commit", "--version"],
                capture_output=True,
                text=True,
                cwd=repo_root,
                timeout=30
            )
            assert result.returncode == 0, f"pre-commit not available: {result.stderr}"
            assert "pre-commit" in result.stdout.lower(), "Invalid pre-commit version output"
            
        except subprocess.TimeoutExpired:
            pytest.fail("pre-commit --version command timed out")
        except FileNotFoundError:
            pytest.fail("pre-commit command not found - ensure it's installed in the virtual environment")
    
    @pytest.mark.skipif(
        not _is_precommit_installed(),
        reason="pre-commit not installed - run 'pip install -e .[dev]' first"
    )
    def test_precommit_install_creates_hooks(self):
        """Test that 'pre-commit install' creates the git hooks."""
        repo_root = Path(__file__).parent.parent
        hooks_dir = repo_root / ".git" / "hooks"
        pre_commit_hook = hooks_dir / "pre-commit"
        
        # Run pre-commit install
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pre_commit", "install"],
                capture_output=True,
                text=True,
                cwd=repo_root,
                timeout=60
            )
            
            assert result.returncode == 0, f"pre-commit install failed: {result.stderr}"
            assert pre_commit_hook.exists(), f"Pre-commit hook not created at {pre_commit_hook}"
            assert pre_commit_hook.is_file(), "Pre-commit hook should be a file"
            
            # Verify the hook file contains pre-commit content
            with open(pre_commit_hook, 'r') as f:
                content = f.read()
            assert "pre-commit" in content.lower(), "Hook file should contain pre-commit references"
            
        except subprocess.TimeoutExpired:
            pytest.fail("pre-commit install command timed out")