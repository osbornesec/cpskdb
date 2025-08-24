"""Error handling and edge case tests for Qdrant Docker Compose configuration."""

import subprocess
import tempfile
import time

from tests.test_docker_compose_base import QdrantDockerComposeTestBase  # type: ignore


class TestQdrantDockerComposeErrors(QdrantDockerComposeTestBase):
    """Error handling and edge case tests for Qdrant Docker Compose configuration."""

    def test_qdrant_port_conflict_error_handling(self):
        """Test: Qdrant Handles Port Conflicts
        Given: Port 6333 already in use by another service
        When: Starting Qdrant service
        Then: Clear error about port conflict.
        """
        # Start a dummy service on port 6333 first
        dummy_container = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--rm",
                "--name",
                "dummy_port_blocker",
                "-p",
                "6333:80",
                "nginx:alpine",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        try:
            assert dummy_container.returncode == 0, "Failed to start dummy container"
            time.sleep(3)

            compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_port_conflict
    ports:
      - "6333:6333"
"""

            with tempfile.TemporaryDirectory() as temp_dir:
                compose_file = self.setup_compose_file(compose_content, temp_dir)

                result = self.start_qdrant_service(compose_file, temp_dir)

                # Should fail with port conflict error
                assert result.returncode != 0, "Expected failure due to port conflict"
                error_output = result.stderr.lower()
                port_conflict_indicators = [
                    "port",
                    "bind",
                    "address already in use",
                    "6333",
                ]
                assert any(indicator in error_output for indicator in port_conflict_indicators), f"Expected port conflict error, got: {result.stderr}"

                self.stop_qdrant_service(compose_file, temp_dir)

        finally:
            subprocess.run(
                ["docker", "stop", "dummy_port_blocker"],
                check=False,
                capture_output=True,
            )

    def test_qdrant_invalid_image_error_handling(self):
        """Test: Qdrant Handles Invalid Image Tag
        Given: Qdrant service configured with non-existent image tag
        When: Attempting to start service
        Then: Docker reports image not found error.
        """
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:nonexistent-tag-12345
    container_name: test_qdrant_invalid_image
    ports:
      - "6333:6333"
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = self.setup_compose_file(compose_content, temp_dir)

            result = self.start_qdrant_service(compose_file, temp_dir)

            try:
                # Should fail with image not found error
                assert result.returncode != 0, "Expected failure due to invalid image"
                error_output = result.stderr.lower()
                image_error_indicators = [
                    "pull",
                    "not found",
                    "manifest unknown",
                    "image",
                ]
                assert any(indicator in error_output for indicator in image_error_indicators), f"Expected image error, got: {result.stderr}"

            finally:
                self.stop_qdrant_service(compose_file, temp_dir)

    def test_qdrant_malformed_compose_config_error(self):
        """Test: Qdrant Handles Malformed Docker Compose Configuration
        Given: Docker Compose file with syntax errors in Qdrant section
        When: Running `docker compose up`
        Then: Clear error message about configuration issues.
        """
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_malformed
    ports:
      - "6333:6333"
    environment:
      - INVALID_SYNTAX_HERE
    volumes:
      - qdrant_data:/qdrant/storage
    # Missing closing bracket or invalid YAML structure
    malformed_section: {
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = self.setup_compose_file(compose_content, temp_dir)

            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "config"],
                check=False,
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

            # Should fail with configuration error
            assert result.returncode != 0, "Expected failure due to malformed config"
            error_output = result.stderr.lower()
            config_error_indicators = ["yaml", "syntax", "invalid", "error", "parse"]
            assert any(indicator in error_output for indicator in config_error_indicators), f"Expected configuration error, got: {result.stderr}"
