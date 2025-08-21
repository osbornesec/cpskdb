"""Test suite for README.md validation."""

import re
from pathlib import Path
import pytest


class TestREADMEStructure:
    """Test README.md file structure and content."""
    
    def test_readme_file_exists(self) -> None:
        """Test that README.md file exists in project root."""
        readme_path = Path(__file__).parent.parent / "README.md"
        assert readme_path.exists(), "README.md file must exist in project root"
    
    def test_readme_has_essential_sections(self) -> None:
        """Test that README contains all required sections."""
        readme_path = Path(__file__).parent.parent / "README.md"
        
        if not readme_path.exists():
            pytest.skip("README.md not present; skipping section checks")
            
        content = readme_path.read_text(encoding='utf-8')
        
        # Define required sections
        required_sections = [
            r"#\s+.*Agentic RAG System",  # Project title
            r"##\s+.*Features",           # Features section
            r"##\s+.*Architecture",       # Architecture section  
            r"##\s+.*Installation",       # Installation section
            r"##\s+.*Usage",              # Usage section
            r"##\s+.*Configuration",      # Configuration section
            r"##\s+.*API Documentation",  # API docs section
            r"##\s+.*Development",        # Development section
            r"##\s+.*Contributing",       # Contributing section
            r"##\s+.*License",            # License section
        ]
        
        for section_pattern in required_sections:
            assert re.search(section_pattern, content, re.IGNORECASE), \
                f"Required section not found: {section_pattern}"


class TestREADMEContent:
    """Test README.md content quality and accuracy."""
    
    def test_project_description_exists(self) -> None:
        """Test that project has clear description."""
        readme_path = Path(__file__).parent.parent / "README.md"
        
        if not readme_path.exists():
            pytest.skip("README.md not present; skipping description check")
            
        content = readme_path.read_text(encoding='utf-8')
        
        # Should mention key concepts
        key_concepts = [
            r"agentic.*rag",
            r"retrieval.*augmented.*generation", 
            r"multi.*product",
            r"technical.*data"
        ]
        
        description_found = False
        for concept in key_concepts:
            if re.search(concept, content, re.IGNORECASE):
                description_found = True
                break
        
        assert description_found, "README must contain clear project description with key concepts"
    
    def test_technology_stack_documented(self) -> None:
        """Test that technology stack is properly documented."""
        readme_path = Path(__file__).parent.parent / "README.md"
        
        if not readme_path.exists():
            pytest.skip("README.md not present; skipping tech stack check")
            
        content = readme_path.read_text(encoding='utf-8')
        
        # Required technologies from CLAUDE.md
        required_tech = [
            r"fastapi",
            r"langgraph", 
            r"qdrant",
            r"postgresql",
            r"redis",
            r"ollama"
        ]
        
        for tech in required_tech:
            assert re.search(tech, content, re.IGNORECASE), \
                f"Technology {tech} must be mentioned in README"
    
    def test_installation_instructions_exist(self) -> None:
        """Test that installation section has actual instructions."""
        readme_path = Path(__file__).parent.parent / "README.md"
        
        if not readme_path.exists():
            pytest.skip("README.md not present; skipping installation checks")
            
        content = readme_path.read_text(encoding='utf-8')
        
        # Should contain basic installation commands
        install_indicators = [
            r"git clone",
            r"pip install",
            r"docker.*compose",
            r"requirements\.txt"
        ]
        
        install_found = False
        for indicator in install_indicators:
            if re.search(indicator, content, re.IGNORECASE):
                install_found = True
                break
        
        assert install_found, "Installation section must contain actual installation commands"


class TestREADMEFormatting:
    """Test README.md Markdown formatting and syntax."""
    
    def test_code_blocks_have_language_specification(self) -> None:
        """Test that code blocks specify language for syntax highlighting."""
        readme_path = Path(__file__).parent.parent / "README.md"
        
        if not readme_path.exists():
            pytest.skip("README.md not present; skipping code block checks")
            
        content = readme_path.read_text(encoding='utf-8')
        
        # Find all code blocks
        code_block_pattern = r'```([A-Za-z0-9_+-]*)[ \t]*\n'
        matches = re.findall(code_block_pattern, content)
        
        # Should have code blocks with language specification
        assert len(matches) > 0, "README should contain code blocks with examples"
        
        # Check that major code blocks have language specified
        languages_found = [lang for lang in matches if lang]
        assert len(languages_found) >= 2, "Code blocks should specify language for syntax highlighting"
        
    def test_headers_follow_hierarchy(self) -> None:
        """Test that headers follow proper hierarchy (no skipping levels)."""
        readme_path = Path(__file__).parent.parent / "README.md"
        
        if not readme_path.exists():
            pytest.skip("README.md not present; skipping hierarchy checks")
            
        content = readme_path.read_text(encoding='utf-8')
        
        # Remove code blocks to avoid false positives
        content_without_code = re.sub(r'```[\s\S]*?```', '', content)
        
        # Extract headers and their levels
        header_pattern = r'^(#{1,6})\s+(.+)$'
        headers = []
        
        for line in content_without_code.split('\n'):
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
            prev_level = headers[i-1][0]
            
            # Level should not increase by more than 1
            if current_level > prev_level:
                assert current_level - prev_level <= 1, \
                    f"Header hierarchy violation: jumping from h{prev_level} to h{current_level}"