"""
Tests for Qdrant Docker Compose container edge cases.

This module implements container-specific edge cases including naming,
environment variables, and restart behavior.
"""

import os
import subprocess

import requests  # type: ignore

from tests.test_docker_compose_extended_base import QdrantDockerComposeExtendedTestBase


class TestQdrantDockerComposeContainerEdgeCases(QdrantDockerComposeExtendedTestBase):
    """Container-specific edge cases for Qdrant Docker Compose configuration."""

    def test_extremely_long_container_name_edge_case(self):
        """Test Docker Compose behavior with extremely long container names."""
        # Create a very long container name (Docker has limits)
        long_name = "a" * 200  # Exceeds typical container name limits

        compose_content = f"""
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: {long_name}
    ports:
      - "6333:6333"
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__LOG_LEVEL=INFO
"""

        self.setup_compose_file(compose_content)

        # Should fail due to container name length
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertNotEqual(result.returncode, 0)

    def test_special_characters_in_environment_variables(self):
        """Test Docker Compose with special characters in environment variables."""
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant-test
    ports:
      - "6333:6333"
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__LOG_LEVEL=INFO
      - SPECIAL_VAR=value with spaces & symbols!@#$$%^&*()
      - UNICODE_VAR=测试中文字符
      - JSON_VAR={"key":"value","number":123}
"""

        self.setup_compose_file(compose_content)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

    def test_container_restart_with_data_integrity(self):
        """Test container restart and data integrity edge cases."""
        compose_content = f"""
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant-test
    ports:
      - "6333:6333"
    volumes:
      - {self.temp_dir}/qdrant_data:/qdrant/storage
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__LOG_LEVEL=INFO
"""

        self.setup_compose_file(compose_content)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

        # Create a collection and add data
        collection_name = "test_collection"
        collection_data = {"vectors": {"size": 4, "distance": "Cosine"}}

        response = requests.put(
            f"http://localhost:6333/collections/{collection_name}",
            json=collection_data,
            timeout=10,
        )
        self.assertEqual(response.status_code, 200)

        # Add some points
        points_data = {
            "points": [
                {
                    "id": 1,
                    "vector": [0.1, 0.2, 0.3, 0.4],
                    "payload": {"test": "data"},
                }
            ]
        }

        response = requests.put(
            f"http://localhost:6333/collections/{collection_name}/points",
            json=points_data,
            timeout=10,
        )
        self.assertEqual(response.status_code, 200)

        # Stop and completely remove container including volumes
        subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "down", "-v"],
            capture_output=True,
            cwd=self.temp_dir,
        )

        # Start again (volumes should persist)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Data should still be there
        self.verify_collection_exists(collection_name)

    def test_environment_variable_interpolation_edge_cases(self):
        """Test Docker Compose environment variable interpolation edge cases."""
        # Set environment variable for interpolation
        os.environ["QDRANT_TEST_PORT"] = "6333"
        os.environ["QDRANT_LOG_LEVEL"] = "INFO"

        try:
            compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant-test
    ports:
      - "${QDRANT_TEST_PORT:-6333}:6333"
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__LOG_LEVEL=${QDRANT_LOG_LEVEL:-DEBUG}
      - UNDEFINED_VAR=${UNDEFINED_VAR:-default_value}
"""

            self.setup_compose_file(compose_content)
            result = self.start_qdrant_service(self.compose_file, self.temp_dir)
            self.assertEqual(result.returncode, 0)

            self.assertTrue(self.wait_for_qdrant_ready())

        finally:
            # Clean up environment variables
            os.environ.pop("QDRANT_TEST_PORT", None)
            os.environ.pop("QDRANT_LOG_LEVEL", None)
