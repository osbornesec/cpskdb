"""Tests for requirements.txt generation from pyproject.toml."""

import tempfile
import textwrap
from pathlib import Path

import pytest


def test_generate_requirements_production_only():
    """Test generating requirements.txt with production dependencies only."""
    # This test will fail initially (RED phase)
    # We need to create a requirements generator first

    # Create a temporary pyproject.toml
    pyproject_content = textwrap.dedent(
        """
        [project]
        name = "test-project"
        dependencies = [
            "fastapi>=0.113.0,<0.116.0",
            "pydantic>=2.7.0,<3.0.0",
            "httpx>=0.25.0",
        ]
        [project.optional-dependencies]
        dev = [
            "pytest>=8.0.0",
            "ruff>=0.1.0",
        ]
    """
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        pyproject_path = temp_path / "pyproject.toml"
        requirements_path = temp_path / "requirements.txt"

        # Write test pyproject.toml
        pyproject_path.write_text(pyproject_content)

        # Import and use our requirements generator (will fail initially)
        from src.requirements_generator import generate_requirements

        # Generate production requirements only
        generate_requirements(pyproject_path, requirements_path, include_dev=False)

        # Verify requirements.txt was created
        assert requirements_path.exists()

        # Read and verify content
        requirements_content = requirements_path.read_text().strip()
        expected_lines = [
            "fastapi>=0.113.0,<0.116.0",
            "httpx>=0.25.0",
            "pydantic>=2.7.0,<3.0.0",
        ]  # Expected in sorted order

        actual_lines = [
            line.strip() for line in requirements_content.split("\n") if line.strip()
        ]

        # Verify all production dependencies are present in correct order
        assert actual_lines == expected_lines

        # Verify dev dependencies are not present
        assert "pytest>=8.0.0" not in requirements_content
        assert "ruff>=0.1.0" not in requirements_content

        # Verify exact count (no extra dependencies)
        assert len(actual_lines) == len(expected_lines)


def test_generate_requirements_include_dev():
    """Test generating requirements.txt including development dependencies."""
    # Create a temporary pyproject.toml
    pyproject_content = textwrap.dedent(
        """
        [project]
        name = "test-project"
        dependencies = [
            "fastapi>=0.113.0,<0.116.0",
            "pydantic>=2.7.0,<3.0.0",
        ]
        [project.optional-dependencies]
        dev = [
            "pytest>=8.0.0",
            "ruff>=0.1.0",
            "mypy>=1.8.0",
        ]
    """
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        pyproject_path = temp_path / "pyproject.toml"
        requirements_path = temp_path / "requirements.txt"

        # Write test pyproject.toml
        pyproject_path.write_text(pyproject_content)

        # Import and use our requirements generator
        from src.requirements_generator import generate_requirements

        # Generate requirements including dev dependencies
        generate_requirements(pyproject_path, requirements_path, include_dev=True)

        # Verify requirements.txt was created
        assert requirements_path.exists()

        # Read and verify content
        requirements_content = requirements_path.read_text().strip()
        expected_lines = [
            "fastapi>=0.113.0,<0.116.0",
            "mypy>=1.8.0",
            "pydantic>=2.7.0,<3.0.0",
            "pytest>=8.0.0",
            "ruff>=0.1.0",
        ]  # Expected in sorted order (both prod and dev)

        actual_lines = [
            line.strip() for line in requirements_content.split("\n") if line.strip()
        ]

        # Verify all dependencies (prod + dev) are present in correct order
        assert actual_lines == expected_lines

        # Verify exact count
        assert len(actual_lines) == len(expected_lines)


def test_generate_requirements_missing_file():
    """Test error handling when pyproject.toml doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        pyproject_path = temp_path / "nonexistent.toml"
        requirements_path = temp_path / "requirements.txt"

        # Import our requirements generator
        from src.requirements_generator import generate_requirements

        # Expect FileNotFoundError when pyproject.toml doesn't exist
        with pytest.raises(FileNotFoundError) as exc_info:
            generate_requirements(pyproject_path, requirements_path)

        # Verify error message contains the expected path
        assert str(pyproject_path) in str(exc_info.value)
        assert "pyproject.toml not found" in str(exc_info.value)

        # Verify requirements.txt was not created
        assert not requirements_path.exists()


def test_generate_requirements_from_project_toml():
    """Test generating requirements.txt from the actual project pyproject.toml."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        requirements_path = temp_path / "requirements.txt"

        # Use the actual project pyproject.toml
        project_root = Path(__file__).parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"

        # Import our requirements generator
        from src.requirements_generator import generate_requirements

        # Generate production requirements
        generate_requirements(pyproject_path, requirements_path, include_dev=False)

        # Verify requirements.txt was created
        assert requirements_path.exists()

        # Read and verify some key dependencies are present
        requirements_content = requirements_path.read_text().strip()

        # Check for some expected production dependencies
        assert "fastapi" in requirements_content
        assert "pydantic" in requirements_content
        assert "langgraph" in requirements_content
        assert "qdrant-client" in requirements_content

        # Verify dev dependencies are not present
        assert "pytest" not in requirements_content
        assert "ruff" not in requirements_content
        assert "mypy" not in requirements_content
        assert "black" not in requirements_content
