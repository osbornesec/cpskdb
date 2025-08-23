"""Generate requirements.txt from pyproject.toml configuration."""

import tomllib
from pathlib import Path
# List import removed as it's not used in type hints


def generate_requirements(
    pyproject_path: Path, requirements_path: Path, include_dev: bool = False
) -> None:
    """Generate requirements.txt from pyproject.toml dependencies.

    Args:
        pyproject_path: Path to pyproject.toml file
        requirements_path: Path where requirements.txt should be written
        include_dev: Whether to include development dependencies

    Raises:
        FileNotFoundError: If pyproject.toml doesn't exist
        ValueError: If pyproject.toml is malformed
    """
    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

    # Read and parse pyproject.toml
    try:
        with open(pyproject_path, "rb") as f:
            config = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"Invalid TOML syntax in pyproject.toml: {e}") from e

    dependencies = []

    # Get production dependencies with validation
    project_config = config.get("project", {})
    if "dependencies" in project_config:
        prod_deps = project_config["dependencies"]
        if not isinstance(prod_deps, list):
            raise ValueError(f"project.dependencies must be a list, got {type(prod_deps)}")
        
        # Validate each dependency is a string
        for i, dep in enumerate(prod_deps):
            if not isinstance(dep, str):
                raise ValueError(f"project.dependencies[{i}] must be a string, got {type(dep)}")
        
        dependencies.extend(prod_deps)

    # Get development dependencies if requested
    if include_dev:
        optional_deps = project_config.get("optional-dependencies", {})
        if optional_deps and not isinstance(optional_deps, dict):
            raise ValueError(f"project.optional-dependencies must be a dict, got {type(optional_deps)}")
            
        dev_deps = optional_deps.get("dev", [])
        if dev_deps and not isinstance(dev_deps, list):
            raise ValueError(f"project.optional-dependencies.dev must be a list, got {type(dev_deps)}")
        
        # Validate each dev dependency is a string
        for i, dep in enumerate(dev_deps):
            if not isinstance(dep, str):
                raise ValueError(f"project.optional-dependencies.dev[{i}] must be a string, got {type(dep)}")
        
        dependencies.extend(dev_deps)
    
    # Remove duplicates while preserving order (first occurrence wins)
    unique_sorted = []
    seen = set()
    for dep in dependencies:
        if dep not in seen:
            unique_sorted.append(dep)
            seen.add(dep)

    # Write requirements.txt with validated unique dependencies
    requirements_path.parent.mkdir(parents=True, exist_ok=True)
    with open(requirements_path, "w", encoding="utf-8") as f:
        for dep in unique_sorted:
            f.write(f"{dep}\n")
