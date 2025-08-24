"""Tests for adding development dependencies to pyproject.toml."""

import tempfile
import tomllib
from pathlib import Path
from typing import Dict, Any

import pytest


class TestPyprojectDevDependencies:
    """Test suite for adding development dependencies to pyproject.toml."""

    @pytest.fixture
    def sample_pyproject_toml(self) -> str:
        """Sample pyproject.toml content with basic PEP 621 structure."""
        return """[build-system]
requires = ["setuptools>=61.2", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "cpskdb"
version = "0.1.0"
description = "Agentic RAG system for multi-product technical data with high accuracy, auditability, and data privacy"
requires-python = ">=3.11"
authors = [
    {name = "CPSKDB Maintainers", email = "maintainers@cpskdb.example.com"},
]
license = {text = "MIT"}
readme = "README.md"
keywords = ["rag", "ai", "vector-database", "fastapi", "langgraph", "qdrant"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]
dependencies = [
    # Core Framework
    "fastapi[standard]>=0.113.0,<0.116.0",
    "pydantic>=2.7.0,<3.0.0",
    
    # AI/ML Orchestration
    "langgraph>=0.3.27",
    "langchain>=0.2.0",
    "langchain-core>=0.2.38",
    
    # Vector Database
    "qdrant-client[fastembed]>=1.7.0",
    
    # LLM/Embedding Providers
    "voyageai>=0.3.2",
    "cohere>=5.15.0",
    
    # HTTP Client & Server
    "httpx[http2]>=0.25.0",
    "uvicorn[standard]>=0.26.0",
    
    # Configuration Management
    "python-dotenv>=1.0.0",
    "pyyaml>=6.0.0",
]
"""

    def test_add_dev_dependencies_to_existing_pep621_config(
        self, sample_pyproject_toml: str
    ):
        """Test adding dev dependencies to existing PEP 621 pyproject.toml."""
        # This test should fail initially since we haven't implemented the functionality
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(sample_pyproject_toml)
            f.flush()

            # This should add the dev dependencies
            from src.config.pyproject_manager import PyprojectManager

            manager = PyprojectManager(Path(f.name))
            manager.add_dev_dependencies()

            # Read the modified file
            with open(f.name, "rb") as modified_f:
                data = tomllib.load(modified_f)

            # Assertions
            assert "project" in data
            assert "optional-dependencies" in data["project"]
            assert "dev" in data["project"]["optional-dependencies"]

            dev_deps = data["project"]["optional-dependencies"]["dev"]
            assert any("pytest" in dep for dep in dev_deps)
            assert any("ruff" in dep for dep in dev_deps)
            assert any("mypy" in dep for dep in dev_deps)
            assert any("black" in dep for dep in dev_deps)

            # Verify existing dependencies remain unchanged
            assert "fastapi" in str(data["project"]["dependencies"])
            assert "langgraph" in str(data["project"]["dependencies"])

    def test_dev_dependencies_version_constraints(self, sample_pyproject_toml: str):
        """Test that dev dependencies have proper version constraints."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(sample_pyproject_toml)
            f.flush()

            from src.config.pyproject_manager import PyprojectManager

            manager = PyprojectManager(Path(f.name))
            manager.add_dev_dependencies()

            # Read the modified file
            with open(f.name, "rb") as modified_f:
                data = tomllib.load(modified_f)

            dev_deps = data["project"]["optional-dependencies"]["dev"]

            # Check that all dependencies have proper version constraints
            pytest_dep = next((dep for dep in dev_deps if "pytest" in dep), None)
            assert pytest_dep is not None
            assert (
                ">=" in pytest_dep and "<" in pytest_dep
            )  # Should have both lower and upper bounds

            ruff_dep = next((dep for dep in dev_deps if "ruff" in dep), None)
            assert ruff_dep is not None
            assert ">=" in ruff_dep

            mypy_dep = next((dep for dep in dev_deps if "mypy" in dep), None)
            assert mypy_dep is not None
            assert ">=" in mypy_dep

            black_dep = next((dep for dep in dev_deps if "black" in dep), None)
            assert black_dep is not None
            assert ">=" in black_dep

    def test_organize_dev_dependencies_by_groups(self, sample_pyproject_toml: str):
        """Test organizing dev dependencies by functional groups."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(sample_pyproject_toml)
            f.flush()

            from src.config.pyproject_manager import PyprojectManager

            manager = PyprojectManager(Path(f.name))
            manager.add_dev_dependencies_by_groups()

            # Read the modified file
            with open(f.name, "rb") as modified_f:
                data = tomllib.load(modified_f)

            optional_deps = data["project"]["optional-dependencies"]

            # Check functional groups exist
            assert "test" in optional_deps
            assert "lint" in optional_deps
            assert "type-check" in optional_deps
            assert "format" in optional_deps

            # Verify test group contents
            test_deps = optional_deps["test"]
            assert any("pytest" in dep for dep in test_deps)
            assert any("pytest-cov" in dep for dep in test_deps)
            assert any("pytest-asyncio" in dep for dep in test_deps)

            # Verify lint group contents
            lint_deps = optional_deps["lint"]
            assert any("ruff" in dep for dep in lint_deps)
            assert any("pre-commit" in dep for dep in lint_deps)

            # Verify type-check group contents
            type_deps = optional_deps["type-check"]
            assert any("mypy" in dep for dep in type_deps)

            # Verify format group contents
            format_deps = optional_deps["format"]
            assert any("black" in dep for dep in format_deps)

    def test_toml_syntax_validation_after_dev_deps_addition(
        self, sample_pyproject_toml: str
    ):
        """Test that TOML file remains valid after adding dev dependencies."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(sample_pyproject_toml)
            f.flush()

            from src.config.pyproject_manager import PyprojectManager

            manager = PyprojectManager(Path(f.name))
            manager.add_dev_dependencies()

            # Verify the file can be parsed without errors
            try:
                with open(f.name, "rb") as modified_f:
                    data = tomllib.load(modified_f)

                # Verify basic structure is intact
                assert "build-system" in data
                assert "project" in data
                assert "optional-dependencies" in data["project"]

                # Verify TOML structure is valid
                assert isinstance(data["project"]["optional-dependencies"], dict)
                assert isinstance(data["project"]["optional-dependencies"]["dev"], list)

            except tomllib.TOMLDecodeError as e:
                pytest.fail(f"Generated pyproject.toml has invalid TOML syntax: {e}")
