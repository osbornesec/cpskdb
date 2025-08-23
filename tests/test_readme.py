"""Test suite for README.md validation."""

import re
from pathlib import Path
import pytest


@pytest.fixture(scope="module")
def readme_content() -> str:
    """Load README.md once for all tests; skip suite if absent."""
    readme_path = Path(__file__).parent.parent / "README.md"
    if not readme_path.exists():
        pytest.skip("README.md not present; skipping README validation suite")
    return readme_path.read_text(encoding="utf-8")


class TestREADMEStructure:
    """Test README.md file structure and content."""

    def test_readme_file_exists(self, readme_content: str) -> None:
        """Test that README.md file exists in project root."""
        assert readme_content is not None

    def test_readme_has_essential_sections(self, readme_content: str) -> None:
        """Test that README contains all required sections."""
        content = readme_content

        # Define required sections
        required_sections = [
            r"#\s+.*Agentic RAG System",  # Project title
            r"##\s+.*Features",  # Features section
            r"##\s+.*Architecture",  # Architecture section
            r"##\s+.*Installation",  # Installation section
            r"##\s+.*Usage",  # Usage section
            r"##\s+.*Configuration",  # Configuration section
            r"##\s+.*API Documentation",  # API docs section
            r"##\s+.*Development",  # Development section
            r"##\s+.*Contributing",  # Contributing section
            r"##\s+.*License",  # License section
        ]

        # Pre-compile regex patterns for better performance
        compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in required_sections]
        
        for i, compiled_pattern in enumerate(compiled_patterns):
            assert compiled_pattern.search(content), f"Required section not found: {required_sections[i]}"


class TestREADMEContent:
    """Test README.md content quality and accuracy."""

    def test_project_description_exists(self, readme_content: str) -> None:
        """Test that project has clear description."""
        content = readme_content

        # Should mention key concepts
        key_concepts = [
            r"agentic.*rag",
            r"retrieval.*augmented.*generation",
            r"multi.*product",
            r"technical.*data",
        ]

        description_found = False
        for concept in key_concepts:
            if re.search(concept, content, re.IGNORECASE):
                description_found = True
                break

        assert (
            description_found
        ), "README must contain clear project description with key concepts"

    def test_technology_stack_documented(self, readme_content: str) -> None:
        """Test that technology stack is properly documented."""
        content = readme_content

        # Required technologies from CLAUDE.md
        required_tech = [
            r"fastapi",
            r"langgraph",
            r"qdrant",
            r"postgresql",
            r"redis",
            r"ollama",
        ]

        for tech in required_tech:
            assert re.search(
                tech, content, re.IGNORECASE
            ), f"Technology {tech} must be mentioned in README"

    def test_installation_instructions_exist(self, readme_content: str) -> None:
        """Test that installation section has actual instructions."""
        content = readme_content

        # Should contain basic installation commands (including make install)
        install_indicators = [
            r"git clone",
            r"(?:pip|pipx|uv)\s+install",
            r"(?:poetry\s+install|pip\s+install\s+-r\s+requirements\.txt|pip\s+install\s+\.)",
            r"docker.*compose",
            r"(?:sudo\s+)?(?:g?make\s+)?install",  # Added make install support
        ]

        install_found = False
        for indicator in install_indicators:
            if re.search(indicator, content, re.IGNORECASE):
                install_found = True
                break

        assert (
            install_found
        ), "Installation section must contain actual installation commands"


class TestREADMEFormatting:
    """Test README.md Markdown formatting and syntax."""

    def test_code_blocks_have_language_specification(self, readme_content: str) -> None:
        """Test that code blocks specify language for syntax highlighting."""
        content = readme_content

        # Parse fences with a state machine to avoid misclassifying closing fences
        lines = content.split("\n")
        opening_blocks: list[tuple[int, str, str]] = []
        in_block = False
        for i, line in enumerate(lines):
            # Support both backticks (```) and tildes (~~~) for code fences
            if line.startswith("```") or line.startswith("~~~"):
                if not in_block:
                    # Opening fence - handle both ``` and ~~~
                    if line.startswith("```"):
                        lang_match = re.match(r"```([A-Za-z0-9_+-]*)[ \t]*$", line)
                    else:
                        lang_match = re.match(r"~~~([A-Za-z0-9_+-]*)[ \t]*$", line)
                    lang = lang_match.group(1) if lang_match else ""
                    opening_blocks.append((i + 1, line, lang))
                    in_block = True
                else:
                    # Closing fence
                    in_block = False

        # Should have code blocks with language specification
        assert (
            len(opening_blocks) > 0
        ), "README should contain code blocks with examples"

        # Check that all opening blocks have language specified
        missing = [
            (line_num, line_content)
            for line_num, line_content, lang in opening_blocks
            if not lang
        ]
        assert not missing, f"All fenced code blocks must declare a language: {missing}"

    def test_headers_follow_hierarchy(self, readme_content: str) -> None:
        """Test that headers follow proper hierarchy (no skipping levels)."""
        content = readme_content

        # Remove code blocks to avoid false positives
        content_without_code = re.sub(r"```[\s\S]*?```", "", content)

        # Extract headers and their levels
        header_pattern = r"^(#{1,6})\s+(.+)$"
        headers = []

        for line in content_without_code.split("\n"):
            match = re.match(header_pattern, line)
            if match:
                level = len(match.group(1))
                text = match.group(2)
                headers.append((level, text))

        # Should have at least one h1 header
        h1_headers = [h for h in headers if h[0] == 1]
        assert len(h1_headers) >= 1, "README should have at least one h1 header"

        # Check hierarchy (no skipping levels)
        for i in range(1, len(headers)):
            current_level = headers[i][0]
            prev_level = headers[i - 1][0]

            # Level should not increase by more than 1
            if current_level > prev_level:
                assert (
                    current_level - prev_level <= 1
                ), f"Header hierarchy violation: jumping from h{prev_level} to h{current_level}"
