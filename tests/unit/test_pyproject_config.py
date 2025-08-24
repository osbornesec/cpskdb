"""Tests for pyproject.toml configuration."""

import pathlib
import tomllib
from typing import Any

import pytest


class TestPyprojectConfig:
    """Test suite for pyproject.toml configuration validation."""

    @pytest.fixture
    def project_root(self) -> pathlib.Path:
        """Return the project root directory."""
        return pathlib.Path(__file__).parent.parent.parent

    @pytest.fixture
    def pyproject_path(self, project_root: pathlib.Path) -> pathlib.Path:
        """Return the path to pyproject.toml."""
        return project_root / "pyproject.toml"

    @pytest.fixture
    def pyproject_data(self, pyproject_path: pathlib.Path) -> dict[str, Any]:
        """Load and parse pyproject.toml data."""
        with pyproject_path.open("rb") as f:
            return tomllib.load(f)

    def test_pyproject_toml_exists(self, pyproject_path: pathlib.Path) -> None:
        """Test that pyproject.toml exists in project root."""
        assert pyproject_path.exists(), "pyproject.toml must exist in project root"
        assert pyproject_path.is_file(), "pyproject.toml must be a file"

    def test_build_system_configuration(self, pyproject_data: dict[str, Any]) -> None:
        """Test build-system section has correct configuration."""
        assert (
            "build-system" in pyproject_data
        ), "pyproject.toml must have [build-system] section"

        build_system = pyproject_data["build-system"]
        assert "requires" in build_system, "[build-system] must have 'requires' field"
        assert (
            "build-backend" in build_system
        ), "[build-system] must have 'build-backend' field"

        # Check setuptools requirement
        requires = build_system["requires"]
        assert isinstance(requires, list), "'requires' must be a list"
        setuptools_req = next(
            (req for req in requires if req.startswith("setuptools")), None
        )
        assert setuptools_req is not None, "setuptools must be in build requirements"
        assert (
            ">=61.2" in setuptools_req
        ), "setuptools must be >= 61.2 for PEP 621 support"

        # Check build backend
        assert (
            build_system["build-backend"] == "setuptools.build_meta"
        ), "build-backend must be setuptools.build_meta"

    def test_project_metadata_completeness(
        self, pyproject_data: dict[str, Any]
    ) -> None:
        """Test project section has all required metadata."""
        assert "project" in pyproject_data, "pyproject.toml must have [project] section"

        project = pyproject_data["project"]

        # Required fields
        assert "name" in project, "[project] must have 'name' field"
        assert "version" in project, "[project] must have 'version' field"
        assert "description" in project, "[project] must have 'description' field"
        assert (
            "requires-python" in project
        ), "[project] must have 'requires-python' field"

        # Check project name
        assert project["name"] == "cpskdb", "Project name must be 'cpskdb'"

        # Check description matches project purpose
        description = project["description"].lower()
        assert "rag" in description, "Description must mention RAG system"
        assert (
            "agentic" in description or "agent" in description
        ), "Description must mention agentic/agent capabilities"

    def test_python_version_requirement(self, pyproject_data: dict[str, Any]) -> None:
        """Test Python version requirement is >= 3.11."""
        project = pyproject_data["project"]
        python_req = project["requires-python"]

        assert (
            python_req == ">=3.11"
        ), f"Python requirement must be '>=3.11', got '{python_req}'"

    def test_project_authors_and_license(self, pyproject_data: dict[str, Any]) -> None:
        """Test authors and license are properly configured."""
        project = pyproject_data["project"]

        # Check authors
        if "authors" in project:
            authors = project["authors"]
            assert isinstance(authors, list), "authors must be a list"
            assert len(authors) > 0, "authors list must not be empty"

            # Check first author has name
            first_author = authors[0]
            assert "name" in first_author, "author must have 'name' field"
            assert isinstance(first_author["name"], str), "author name must be string"
            assert len(first_author["name"]) > 0, "author name must not be empty"

        # Check license
        if "license" in project:
            license_info = project["license"]
            assert isinstance(
                license_info, dict
            ), "license must be a dict with 'text' or 'file'"
            assert (
                "text" in license_info or "file" in license_info
            ), "license must have either 'text' or 'file' field"

    def test_project_keywords_and_classifiers(
        self, pyproject_data: dict[str, Any]
    ) -> None:
        """Test keywords and classifiers are appropriate for RAG system."""
        project = pyproject_data["project"]

        # Check keywords if present
        if "keywords" in project:
            keywords = project["keywords"]
            assert isinstance(keywords, list), "keywords must be a list"

            # Expected keywords for RAG system
            expected_keywords = {"rag", "ai", "vector", "fastapi", "langgraph"}
            keyword_set = {kw.lower() for kw in keywords}

            # At least some expected keywords should be present
            overlap = expected_keywords.intersection(keyword_set)
            assert (
                len(overlap) >= 2
            ), f"Keywords should include RAG-related terms, got {keywords}"

        # Check classifiers if present
        if "classifiers" in project:
            classifiers = project["classifiers"]
            assert isinstance(classifiers, list), "classifiers must be a list"

            # Check for Python version classifiers
            python_classifiers = [
                c for c in classifiers if "Programming Language :: Python :: 3.1" in c
            ]
            assert len(python_classifiers) >= 1, "Must include Python 3.11+ classifiers"

    def test_python_version_boundary_validation(
        self, pyproject_data: dict[str, Any]
    ) -> None:
        """Test Python version requirement excludes older versions."""
        project = pyproject_data["project"]
        python_req = project["requires-python"]

        # Parse the version requirement
        assert python_req.startswith(">="), "Python requirement must use >= operator"
        version_str = python_req[2:]  # Remove ">="
        version_parts = version_str.split(".")

        # Should be at least 3.11
        major = int(version_parts[0])
        minor = int(version_parts[1])

        assert major >= 3, "Python major version must be at least 3"
        assert (
            major == 3 and minor >= 11
        ), f"Python version must be at least 3.11, got {version_str}"

    def test_toml_syntax_validation(self, pyproject_path: pathlib.Path) -> None:
        """Test that pyproject.toml has valid TOML syntax."""
        import tomllib

        # Should be able to parse without exceptions
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)

        # Basic structure validation
        assert isinstance(data, dict), "TOML root must be a dictionary"
        assert len(data) > 0, "TOML file must not be empty"


class TestPyprojectDependencies:
    """Test suite for pyproject.toml production dependencies configuration."""

    @pytest.fixture
    def project_root(self) -> pathlib.Path:
        """Return the project root directory."""
        return pathlib.Path(__file__).parent.parent.parent

    @pytest.fixture
    def pyproject_path(self, project_root: pathlib.Path) -> pathlib.Path:
        """Return the path to pyproject.toml."""
        return project_root / "pyproject.toml"

    @pytest.fixture
    def pyproject_data(self, pyproject_path: pathlib.Path) -> dict[str, Any]:
        """Load and parse pyproject.toml data."""
        with pyproject_path.open("rb") as f:
            return tomllib.load(f)

    def test_core_dependencies_present(self, pyproject_data: dict[str, Any]) -> None:
        """Test that all required core dependencies are present."""
        project = pyproject_data["project"]
        assert "dependencies" in project, "project must have dependencies section"

        dependencies = project["dependencies"]
        assert isinstance(dependencies, list), "dependencies must be a list"
        assert len(dependencies) > 0, "dependencies list must not be empty"

        # Convert dependencies to set for easier checking (handle version constraints)
        dep_names = set()
        for dep in dependencies:
            # Extract package name (before any version constraint)
            name = (
                dep.split(">=")[0]
                .split("==")[0]
                .split("<")[0]
                .split("!=")[0]
                .split("~=")[0]
                .strip()
            )
            # Remove extras specification
            name = name.split("[")[0].strip()
            dep_names.add(name)

        # Required core dependencies for agentic RAG system
        required_deps = {
            "fastapi",
            "langgraph",
            "langchain",
            "qdrant-client",
            "pydantic",
            "voyageai",
            "cohere",
            "httpx",
            "uvicorn",
        }

        missing_deps = required_deps - dep_names
        assert not missing_deps, f"Missing required dependencies: {missing_deps}"

    def test_version_constraints_present(self, pyproject_data: dict[str, Any]) -> None:
        """Test that all dependencies have version constraints."""
        project = pyproject_data["project"]
        dependencies = project["dependencies"]

        # All dependencies should have some version constraint
        for dep in dependencies:
            has_constraint = any(op in dep for op in [">=", "==", "<", "!=", "~=", ">"])
            assert has_constraint, f"Dependency '{dep}' must have a version constraint"

    def test_semantic_version_constraints(self, pyproject_data: dict[str, Any]) -> None:
        """Test that version constraints follow semantic versioning."""
        project = pyproject_data["project"]
        dependencies = project["dependencies"]

        for dep in dependencies:
            # Check that versions look like semantic versions (x.y.z pattern)
            import re

            if any(op in dep for op in [">=", "==", "<", "!=", "~="]):
                versions = re.findall(r"(\d+)\.(\d+)\.(\d+)", dep)
                assert (
                    len(versions) > 0
                ), f"Dependency '{dep}' should have semantic version (x.y.z)"

    def test_critical_version_requirements(
        self, pyproject_data: dict[str, Any]
    ) -> None:
        """Test that critical dependencies have appropriate version requirements."""
        project = pyproject_data["project"]
        dependencies = project["dependencies"]

        # Find specific critical dependencies and check their versions
        for dep in dependencies:
            dep_lower = dep.lower()

            # FastAPI should be >= 0.113.0
            if dep_lower.startswith("fastapi"):
                assert (
                    ">=0.113" in dep or ">=0.114" in dep or ">=0.115" in dep
                ), f"FastAPI should be >= 0.113.0, got: {dep}"

            # LangGraph should be >= 0.3.27
            elif dep_lower.startswith("langgraph"):
                assert ">=0.3" in dep, f"LangGraph should be >= 0.3.27, got: {dep}"

            # Pydantic should be >= 2.7.0 and < 3.0.0
            elif dep_lower.startswith("pydantic"):
                assert ">=2." in dep, f"Pydantic should be >= 2.7.0, got: {dep}"

    def test_extras_specifications(self, pyproject_data: dict[str, Any]) -> None:
        """Test that dependencies with extras are properly specified."""
        project = pyproject_data["project"]
        dependencies = project["dependencies"]

        # Check for expected extras
        extras_found = {}
        for dep in dependencies:
            if "[" in dep and "]" in dep:
                # Extract package name and extras
                name = dep.split("[")[0].strip()
                extras_part = dep.split("[")[1].split("]")[0]
                extras_found[name] = extras_part

        # FastAPI should have [standard] extra
        if "fastapi" in extras_found:
            assert (
                "standard" in extras_found["fastapi"]
            ), f"FastAPI should include [standard] extra, got: {extras_found.get('fastapi', 'none')}"

        # Qdrant-client should have [fastembed] extra if present
        if "qdrant-client" in extras_found:
            assert (
                "fastembed" in extras_found["qdrant-client"]
            ), "Qdrant-client should include [fastembed] extra"

    def test_configuration_dependencies_present(
        self, pyproject_data: dict[str, Any]
    ) -> None:
        """Test that configuration management dependencies are present."""
        project = pyproject_data["project"]
        dependencies = project["dependencies"]

        # Convert dependencies to set for checking
        dep_names = set()
        for dep in dependencies:
            name = (
                dep.split(">=")[0]
                .split("==")[0]
                .split("<")[0]
                .split("!=")[0]
                .split("~=")[0]
                .strip()
            )
            name = name.split("[")[0].strip()
            dep_names.add(name)

        # Required configuration dependencies
        config_deps = {"python-dotenv", "pyyaml"}

        missing_config = config_deps - dep_names
        assert (
            not missing_config
        ), f"Missing configuration dependencies: {missing_config}"
