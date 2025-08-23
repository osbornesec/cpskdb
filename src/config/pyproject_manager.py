"""PyprojectManager for managing pyproject.toml configuration."""

import tomllib
from pathlib import Path
from typing import Dict, List, Any


class PyprojectManager:
    """Manager for pyproject.toml file operations."""

    # Default dev dependencies with semantic versioning
    DEFAULT_DEV_DEPENDENCIES = [
        "pytest>=8.0.0,<9.0.0",
        "ruff>=0.1.0,<0.2.0",
        "mypy>=1.8.0,<2.0.0",
        "black>=23.0.0,<24.0.0",
    ]

    def __init__(self, pyproject_path: Path):
        """Initialize with path to pyproject.toml file."""
        self.pyproject_path = pyproject_path
    
    def _append_toml_section(self, section_header: str, section_content: str) -> None:
        """Helper to append a TOML section if it doesn't exist.
        
        Args:
            section_header: The section header like '[project.optional-dependencies]'
            section_content: The content to append
        """
        # Read current content
        with open(self.pyproject_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check if section exists by parsing TOML
        try:
            with open(self.pyproject_path, "rb") as f:
                config = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise ValueError(f"Invalid TOML syntax in pyproject.toml: {e}") from e
        
        # Parse section path (e.g., 'project.optional-dependencies')
        parts = section_header.strip('[]').split('.')
        current = config
        section_exists = True
        
        try:
            for part in parts:
                current = current[part]
        except KeyError:
            section_exists = False
        
        if not section_exists:
            content += "\n" + section_content + "\n"
            with open(self.pyproject_path, "w", encoding="utf-8") as f:
                f.write(content)

    def add_dev_dependencies(self, custom_deps: List[str] = None) -> None:
        """Add development dependencies to pyproject.toml.

        Args:
            custom_deps: Optional custom dev dependencies. If None, uses defaults.
        """
        dev_deps = (
            custom_deps if custom_deps is not None else self.DEFAULT_DEV_DEPENDENCIES
        )

        # Validate that the file exists and is readable
        if not self.pyproject_path.exists():
            raise FileNotFoundError(
                f"pyproject.toml not found at {self.pyproject_path}"
            )

        # Write the dev dependencies
        self._write_toml_with_dev_deps(dev_deps)

    def add_dev_dependencies_by_groups(self) -> None:
        """Add development dependencies organized by functional groups."""
        # Validate that the file exists and is readable
        if not self.pyproject_path.exists():
            raise FileNotFoundError(
                f"pyproject.toml not found at {self.pyproject_path}"
            )

        # Define dependency groups
        groups = {
            "test": [
                "pytest>=8.0.0,<9.0.0",
                "pytest-cov>=4.0.0,<5.0.0",
                "pytest-asyncio>=0.21.0,<0.22.0",
            ],
            "lint": [
                "ruff>=0.1.0,<0.2.0",
                "pre-commit>=3.4.0,<4.0.0",
            ],
            "type-check": [
                "mypy>=1.8.0,<2.0.0",
            ],
            "format": [
                "black>=23.0.0,<24.0.0",
            ],
        }

        self._write_toml_with_dependency_groups(groups)

    def _write_toml_with_dev_deps(self, dev_deps: List[str]) -> None:
        """Write pyproject.toml with dev dependencies added.

        Args:
            dev_deps: List of development dependency strings.
        """
        # Read original content
        with open(self.pyproject_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Format dependencies for TOML without trailing comma
        formatted_deps = ",\n    ".join(f'"{dep}"' for dep in dev_deps)
        
        dev_deps_section = f"""[project.optional-dependencies]
dev = [
    {formatted_deps}
]"""
        
        self._append_toml_section("project.optional-dependencies", dev_deps_section)

    def _write_toml_with_dependency_groups(self, groups: Dict[str, List[str]]) -> None:
        """Write pyproject.toml with dependency groups added.

        Args:
            groups: Dictionary of group names to dependency lists.
        """
        # Read original content
        with open(self.pyproject_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Build the section content
        section_lines = ["[project.optional-dependencies]"]
        
        for group_name, deps in groups.items():
            formatted_deps = ",\n    ".join(f'"{dep}"' for dep in deps)
            group_section = f"{group_name} = [\n    {formatted_deps}\n]"
            section_lines.append(group_section)
        
        groups_section = "\n".join(section_lines)
        self._append_toml_section("project.optional-dependencies", groups_section)
