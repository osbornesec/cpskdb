"""Test suite for development tool configuration in pyproject.toml."""

import tomllib
from pathlib import Path

import pytest


@pytest.fixture
def pyproject_path():
    """Return path to the project's pyproject.toml file."""
    return Path(__file__).parent.parent.parent / "pyproject.toml"


@pytest.fixture
def pyproject_data(pyproject_path):
    """Load and parse pyproject.toml data."""
    with open(pyproject_path, "rb") as f:
        return tomllib.load(f)


def test_ruff_section_exists_with_basic_configuration(pyproject_data):
    """Test that [tool.ruff] section exists with basic configuration."""
    # Test that [tool.ruff] section exists
    assert "tool" in pyproject_data, "Missing [tool] section in pyproject.toml"
    assert "ruff" in pyproject_data["tool"], (
        "Missing [tool.ruff] section in pyproject.toml"
    )

    ruff_config = pyproject_data["tool"]["ruff"]

    # Validate basic settings exist
    assert "line-length" in ruff_config, "Missing line-length setting in [tool.ruff]"
    assert "target-version" in ruff_config, (
        "Missing target-version setting in [tool.ruff]"
    )

    # Validate basic setting values
    line_length = ruff_config["line-length"]
    assert isinstance(line_length, int), "line-length must be an integer"
    assert 79 <= line_length <= 120, (
        f"line-length {line_length} should be between 79-120 characters"
    )

    target_version = ruff_config["target-version"]
    assert isinstance(target_version, str), "target-version must be a string"
    assert target_version.startswith("py3"), (
        f"target-version {target_version} should be Python 3.x"
    )


def test_mypy_section_exists_with_fastapi_configuration(pyproject_data):
    """Test that [tool.mypy] section exists with FastAPI/async-specific configuration."""
    # Test that [tool.mypy] section exists
    assert "tool" in pyproject_data, "Missing [tool] section in pyproject.toml"
    assert "mypy" in pyproject_data["tool"], (
        "Missing [tool.mypy] section in pyproject.toml"
    )

    mypy_config = pyproject_data["tool"]["mypy"]

    # Validate essential async/FastAPI settings
    assert "python_version" in mypy_config, (
        "Missing python_version setting in [tool.mypy]"
    )
    assert "strict" in mypy_config or "disallow_untyped_defs" in mypy_config, (
        "Missing strict type checking configuration"
    )

    # Validate Python version compatibility
    python_version = mypy_config["python_version"]
    assert isinstance(python_version, str), "python_version must be a string"
    assert python_version in [
        "3.11",
        "3.12",
    ], f"python_version {python_version} should match project requirements"

    # Check for async-friendly configuration (at least one should be present)
    async_friendly_options = [
        "strict_optional",
        "disallow_untyped_calls",
        "disallow_untyped_defs",
        "check_untyped_defs",
    ]
    has_async_config = any(opt in mypy_config for opt in async_friendly_options)
    assert has_async_config, "Missing async-friendly mypy configuration options"


def test_tool_sections_have_non_conflicting_configurations(pyproject_data):
    """Test that tool configurations don't conflict with each other."""
    assert "tool" in pyproject_data, "Missing [tool] section in pyproject.toml"

    # Test line-length consistency between ruff and any other formatter
    ruff_config = pyproject_data["tool"].get("ruff", {})
    black_config = pyproject_data["tool"].get("black", {})

    ruff_line_length = ruff_config.get("line-length")
    black_line_length = black_config.get("line-length")

    if ruff_line_length and black_line_length:
        assert ruff_line_length == black_line_length, (
            f"Line length mismatch: ruff={ruff_line_length}, black={black_line_length}"
        )

    # Test Python version consistency between tools
    ruff_version = ruff_config.get("target-version", "").replace("py", "")
    mypy_version = pyproject_data["tool"].get("mypy", {}).get("python_version", "")

    if ruff_version and mypy_version:
        # Convert versions to comparable format (e.g., "311" -> "3.11")
        if len(ruff_version) == 3:  # e.g., "311"
            ruff_comparable = f"{ruff_version[0]}.{ruff_version[1:]}"
        else:
            ruff_comparable = ruff_version

        assert ruff_comparable == mypy_version, (
            f"Python version mismatch: ruff={ruff_comparable}, mypy={mypy_version}"
        )

    # Test that project requires-python is compatible with tool configurations
    project_python = pyproject_data.get("project", {}).get("requires-python", "")
    if project_python and mypy_version:
        # Extract minimum version from requires-python (e.g., ">=3.11" -> "3.11")
        import re

        match = re.search(r"(\d+\.\d+)", project_python)
        if match:
            min_version = match.group(1)
            assert mypy_version >= min_version, (
                f"MyPy version {mypy_version} is below project minimum {min_version}"
            )


def test_development_tool_dependencies_match_configuration(pyproject_data):
    """Test that development tool dependencies support the configured features."""
    # Check that configured tools are in dev dependencies
    dev_deps = (
        pyproject_data.get("project", {})
        .get("optional-dependencies", {})
        .get("dev", [])
    )
    dep_names = [dep.split(">=")[0].split("==")[0] for dep in dev_deps]

    tool_config = pyproject_data.get("tool", {})

    # Test ruff dependency
    if "ruff" in tool_config:
        assert "ruff" in dep_names, (
            "ruff configured in [tool.ruff] but missing from dev dependencies"
        )

    # Test mypy dependency
    if "mypy" in tool_config:
        assert "mypy" in dep_names, (
            "mypy configured in [tool.mypy] but missing from dev dependencies"
        )

    # Test black dependency (if configured)
    if "black" in tool_config:
        assert "black" in dep_names, (
            "black configured in [tool.black] but missing from dev dependencies"
        )

    # Check version compatibility for key tools
    for dep in dev_deps:
        if dep.startswith("ruff>="):
            # Extract version requirement (e.g., "ruff>=0.1.0" -> "0.1.0")
            import re

            version_match = re.search(r">=(\d+\.\d+)", dep)
            if version_match:
                min_version = version_match.group(1)
                # Ensure minimum version supports modern features
                major, minor = map(int, min_version.split("."))
                assert major > 0 or minor >= 1, (
                    f"ruff version {min_version} too old for modern features"
                )


def test_fastapi_async_mypy_configuration_optimization(pyproject_data):
    """Test that mypy configuration is optimized for FastAPI/async patterns."""
    mypy_config = pyproject_data.get("tool", {}).get("mypy", {})

    # Test strict typing for FastAPI dependency injection
    assert mypy_config.get("disallow_untyped_defs") is True, (
        "disallow_untyped_defs should be True for FastAPI type safety"
    )

    # Test optional handling for async patterns
    assert mypy_config.get("strict_optional") is True, (
        "strict_optional should be True for proper async None handling"
    )

    # Test that additional async-friendly options are present
    recommended_async_options = {
        "check_untyped_defs": True,
        "disallow_any_generics": True,
        "warn_redundant_casts": True,
        "warn_unused_ignores": True,
    }

    missing_options = []
    for option, expected_value in recommended_async_options.items():
        if option not in mypy_config:
            missing_options.append(f"{option} (recommended: {expected_value})")

    # Allow some missing options but require at least half for async optimization
    if len(missing_options) > len(recommended_async_options) // 2:
        pytest.fail(f"Missing too many async-friendly mypy options: {missing_options}")

    # Test Python version is appropriate for modern async features
    python_version = mypy_config.get("python_version")
    if python_version:
        version_parts = python_version.split(".")
        if len(version_parts) >= 2:
            major, minor = int(version_parts[0]), int(version_parts[1])
            assert (major == 3 and minor >= 11) or major > 3, (
                f"Python {python_version} lacks modern async features (need 3.11+)"
            )
