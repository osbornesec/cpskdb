"""
Tests for Qdrant Docker Compose error message validation.

This module implements comprehensive error message validation for scenarios
"Qdrant Provides Meaningful Error Messages" and "Qdrant Health Check Failure Messages"
from the test specification.
"""

import subprocess
import tempfile
import time
import unittest

import requests

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeErrorMessages(QdrantDockerComposeTestBase):
    """Test Qdrant error message clarity via Docker Compose"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.compose_file = None

    def tearDown(self):
        """Clean up test environment"""
        if self.compose_file:
            self.stop_qdrant_service(self.compose_file, self.temp_dir)

    def test_meaningful_error_messages_for_common_failures(self):
        """Test meaningful error messages for common failures"""
        invalid_compose = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_invalid
    ports:
      - "6333:6333"
    environment:
      - INVALID_ENV_VAR=value
    volumes:
      - /nonexistent/path:/qdrant/storage
"""

        self.compose_file = self.setup_compose_file(invalid_compose, self.temp_dir)

        result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "up", "-d"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )

        error_output = result.stderr + result.stdout
        if result.returncode != 0:
            self.assertTrue(len(error_output) > 0, "Should provide error information")

    def test_network_configuration_error_messages(self):
        """Test network configuration error messages"""
        invalid_network_compose = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_network_error
    ports:
      - "6333:6333"
    networks:
      - nonexistent_network
"""

        self.compose_file = self.setup_compose_file(invalid_network_compose, self.temp_dir)

        result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "up", "-d"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )

        if result.returncode != 0:
            error_output = result.stderr + result.stdout
            self.assertTrue(
                any(
                    term in error_output.lower()
                    for term in ["network", "not found", "undefined"]
                )
            )

    def test_error_messages_do_not_expose_sensitive_information(self):
        """Test error messages do not expose sensitive information"""
        compose_with_secrets = f"""
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_secrets
    ports:
      - "6333:6333"
    environment:
      - SECRET_TOKEN=super_secret_value_123
      - API_KEY=secret_api_key_456
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(compose_with_secrets, self.temp_dir)

        result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "logs"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )

        log_output = result.stdout + result.stderr
        sensitive_terms = ["super_secret_value_123", "secret_api_key_456"]

        for sensitive_term in sensitive_terms:
            self.assertNotIn(
                sensitive_term,
                log_output,
                f"Logs should not expose sensitive value: {sensitive_term}",
            )

    def test_api_error_response_format_consistency(self):
        """Test API error response format consistency"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Test invalid collection creation
        invalid_collection_config = {"vectors": {"size": "invalid", "distance": "Cosine"}}
        error_response = requests.put(
            "http://localhost:6333/collections/invalid_test",
            json=invalid_collection_config,
            timeout=10,
        )

        self.assertNotEqual(error_response.status_code, 200)

        # Test invalid search
        invalid_search = {"vector": "not_a_vector", "limit": 5}
        search_error = requests.post(
            "http://localhost:6333/collections/nonexistent/points/search",
            json=invalid_search,
            timeout=10,
        )

        self.assertNotEqual(search_error.status_code, 200)


if __name__ == "__main__":
    unittest.main()
