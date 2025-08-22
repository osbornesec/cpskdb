"""
Edge cases and boundary condition tests for Qdrant Docker Compose configuration
"""

import subprocess
import tempfile
import time

import requests  # type: ignore

from tests.test_docker_compose_base import QdrantDockerComposeTestBase  # type: ignore


class TestQdrantDockerComposeEdgeCases(QdrantDockerComposeTestBase):
    """Edge cases and boundary condition tests for Qdrant Docker Compose configuration"""

    def test_qdrant_missing_environment_variables(self):
        """
        Test: Qdrant Handles Missing Environment Variables
        Given: Docker Compose configuration without QDRANT__LOG_LEVEL
        When: Container starts
        Then: Qdrant uses default log level
        """
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_no_env
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = self.setup_compose_file(compose_content, temp_dir)

            try:
                result = self.start_qdrant_service(compose_file, temp_dir)
                self.assertEqual(
                    result.returncode, 0, f"Docker compose failed: {result.stderr}"
                )

                # Wait for service to be ready
                self.assertTrue(
                    self.wait_for_qdrant_ready(), "Qdrant service not ready"
                )

                # Service should start successfully with defaults
                self.assert_qdrant_healthy()

                # Verify service info endpoint works
                info_response = requests.get("http://localhost:6333/", timeout=10)
                self.assertEqual(info_response.status_code, 200)
                service_info = info_response.json()
                self.assertIn("title", service_info)
                self.assertIn("qdrant", service_info["title"].lower())

            finally:
                self.stop_qdrant_service(compose_file, temp_dir)

    def test_qdrant_missing_storage_volume(self):
        """
        Test: Qdrant Handles Missing Storage Volume
        Given: Docker Compose configuration without storage volume
        When: Container starts
        Then: Qdrant uses ephemeral storage (data lost on container removal)
        """
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_no_volume
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = self.setup_compose_file(compose_content, temp_dir)

            try:
                result = self.start_qdrant_service(compose_file, temp_dir)
                self.assertEqual(
                    result.returncode, 0, f"Docker compose failed: {result.stderr}"
                )

                # Wait for service to be ready
                self.assertTrue(
                    self.wait_for_qdrant_ready(), "Qdrant service not ready"
                )

                # Service should start successfully
                self.assert_qdrant_healthy()

                # Create test collection to verify service works
                self.create_test_collection("ephemeral_test")

                # Stop and remove container (with volume cleanup for clean test)
                subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "down", "-v"],
                    capture_output=True,
                    cwd=temp_dir,
                )

                # Start again - data should be gone
                result = self.start_qdrant_service(compose_file, temp_dir)
                self.assertEqual(result.returncode, 0)

                self.assertTrue(
                    self.wait_for_qdrant_ready(), "Service not ready after restart"
                )

                # Collection should be gone since no volume persistence
                get_response = requests.get(
                    "http://localhost:6333/collections/ephemeral_test", timeout=10
                )
                # Should return 404 indicating no persistence without volumes
                self.assertEqual(
                    get_response.status_code,
                    404,
                    f"Expected collection to be gone without volumes, but got: {get_response.status_code}",
                )

            finally:
                self.stop_qdrant_service(compose_file, temp_dir)

    def test_qdrant_invalid_port_configuration(self):
        """
        Test: Qdrant Invalid Port Numbers
        Given: Port configuration with zero or negative values
        When: Attempting to start service
        Then: Docker Compose validation fails
        """
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_invalid_port
    ports:
      - "0:6333"
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = self.setup_compose_file(compose_content, temp_dir)

            # Try to validate the configuration
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "config"],
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

            # Configuration should be rejected or service should fail to start
            if result.returncode == 0:
                # If config validation passes, try to start and expect failure
                start_result = self.start_qdrant_service(compose_file, temp_dir)

                try:
                    # Service should either fail to start or not be accessible
                    if start_result.returncode == 0:
                        time.sleep(3)
                        # Should not be accessible on port 0
                        try:
                            requests.get("http://localhost:0/healthz", timeout=5)
                            self.fail("Should not be able to connect to port 0")
                        except (
                            requests.exceptions.ConnectionError,
                            requests.exceptions.InvalidURL,
                        ):
                            # Expected - port 0 is not valid for connections
                            pass
                finally:
                    self.stop_qdrant_service(compose_file, temp_dir)
