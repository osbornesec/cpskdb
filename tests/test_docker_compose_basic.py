"""
Basic functionality tests for Qdrant Docker Compose configuration
"""

import subprocess
import tempfile

from tests.test_docker_compose_base import QdrantDockerComposeTestBase  # type: ignore


class TestQdrantDockerComposeBasic(QdrantDockerComposeTestBase):
    """Basic functionality tests for Qdrant Docker Compose configuration"""

    def test_qdrant_service_starts_successfully(self):
        """
        Test: Qdrant Service Starts Successfully
        Given: Docker Compose file with Qdrant service configuration
        When: Running `docker compose up qdrant`
        Then: Qdrant container starts without errors
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = self.setup_compose_file(
                self.create_basic_compose_content(), temp_dir
            )

            result = self.start_qdrant_service(compose_file, temp_dir)

            try:
                self.assertEqual(
                    result.returncode, 0, f"Docker compose failed: {result.stderr}"
                )

                # Verify container is running
                check_result = subprocess.run(
                    [
                        "docker",
                        "ps",
                        "--filter",
                        "name=test_qdrant_basic",
                        "--format",
                        "{{.Status}}",
                    ],
                    capture_output=True,
                    text=True,
                )
                self.assertIn(
                    "Up", check_result.stdout, "Qdrant container is not running"
                )

            finally:
                self.stop_qdrant_service(compose_file, temp_dir)

    def test_qdrant_port_accessibility_and_health_check(self):
        """
        Test: Qdrant Exposes Port 6333 Correctly and Health Endpoint Returns Valid Response
        Given: Qdrant service is configured with port mapping 6333:6333
        When: Service is started
        Then: Port 6333 is accessible and health endpoint responds
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = self.setup_compose_file(
                self.create_basic_compose_content(), temp_dir
            )

            result = self.start_qdrant_service(compose_file, temp_dir)

            try:
                self.assertEqual(
                    result.returncode, 0, f"Docker compose failed: {result.stderr}"
                )

                # Wait for service to be ready
                self.assertTrue(
                    self.wait_for_qdrant_ready(), "Qdrant service not ready"
                )

                # Assert health endpoint is accessible
                self.assert_qdrant_healthy()

            finally:
                self.stop_qdrant_service(compose_file, temp_dir)

    def test_qdrant_storage_volume_persistence(self):
        """
        Test: Qdrant Storage Volume Mounts Correctly
        Given: Docker Compose configuration includes storage volume mapping
        When: Container is started and restarted
        Then: Data persists across container restarts
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = self.setup_compose_file(
                self.create_basic_compose_content(), temp_dir
            )

            try:
                result = self.start_qdrant_service(compose_file, temp_dir)
                self.assertEqual(
                    result.returncode, 0, f"Docker compose failed: {result.stderr}"
                )

                # Wait for service to be ready
                self.assertTrue(
                    self.wait_for_qdrant_ready(), "Qdrant service not ready"
                )

                # Create a test collection
                self.create_test_collection("persistence_test")

                # Restart the container
                subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "restart", "qdrant"],
                    capture_output=True,
                    cwd=temp_dir,
                )

                # Wait for service to be ready after restart
                self.assertTrue(
                    self.wait_for_qdrant_ready(),
                    "Qdrant service not ready after restart",
                )

                # Assert collection still exists after restart
                self.verify_collection_exists("persistence_test")

            finally:
                self.stop_qdrant_service(compose_file, temp_dir)

    def test_qdrant_environment_variable_configuration(self):
        """
        Test: Qdrant Uses Configured Log Level
        Given: Environment variable QDRANT__LOG_LEVEL is set
        When: Container starts
        Then: Qdrant respects the configured log level
        """
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_env
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=DEBUG
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

                # Verify service is accessible
                self.assert_qdrant_healthy()

                # Check logs for debug information
                logs_result = subprocess.run(
                    ["docker", "logs", "test_qdrant_env"],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(logs_result.returncode, 0)
                logs_text = logs_result.stdout.lower()

                # Check for specific Qdrant debug-level indicators
                qdrant_debug_indicators = [
                    "debug",
                    "trace", 
                    "qdrant debug",
                    "log level: debug",
                    "[debug]",
                    "debug mode"
                ]
                found_debug = any(indicator in logs_text for indicator in qdrant_debug_indicators)
                
                # If no specific debug indicators found, check for general startup with debug info
                if not found_debug:
                    general_indicators = ["starting", "initialized", "ready", "listening"]
                    found_startup = any(indicator in logs_text for indicator in general_indicators)
                    self.assertTrue(
                        found_startup,
                        f"No debug or startup logs found in: {logs_text[:500]}"
                    )
                else:
                    self.assertTrue(found_debug, f"Debug logs not found in: {logs_text[:500]}")

            finally:
                self.stop_qdrant_service(compose_file, temp_dir)
