"""
Test Qdrant Docker Compose service discovery scenarios.

This module implements service discovery testing with complex network topologies
and multi-service communication patterns.
"""

import shutil
import subprocess
import tempfile
import time

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeServiceDiscovery(QdrantDockerComposeTestBase):
    """Test Qdrant service discovery functionality via Docker Compose"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.compose_file = None

    def tearDown(self):
        """Clean up test environment"""
        if self.compose_file:
            self.stop_qdrant_service(self.compose_file, self.temp_dir)
        # Clean up temporary directory
        if hasattr(self, "temp_dir") and self.temp_dir:
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_service_discovery_complex_network_topologies(self):
        """Test service discovery with complex network topologies"""
        compose_content_complex = """
version: '3.8'

networks:
  frontend-net:
    driver: bridge
  backend-net:
    driver: bridge

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_complex
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    networks:
      - frontend-net
      - backend-net
    volumes:
      - qdrant_data:/qdrant/storage

  test-client:
    image: alpine:latest
    container_name: test_client_complex
    networks:
      - frontend-net
    volumes:
      - ./tests/test_scripts:/scripts
    command: ["/scripts/service_discovery_test.sh"]
    depends_on:
      - qdrant

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_complex, self.temp_dir
        )

        result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "up", "-d"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

        # Wait for test client to complete service discovery verification
        max_retries = 30
        for i in range(max_retries):
            client_status = subprocess.run(
                [
                    "docker",
                    "inspect",
                    "--format={{.State.Status}}",
                    "test_client_complex",
                ],
                capture_output=True,
                text=True,
            )
            if client_status.returncode == 0:
                status = client_status.stdout.strip()
                if status == "exited":
                    break
            time.sleep(1)

        logs_result = subprocess.run(
            ["docker", "logs", "test_client_complex"],
            capture_output=True,
            text=True,
        )

        if logs_result.returncode == 0:
            logs_content = logs_result.stdout + logs_result.stderr
            # Verify service discovery worked
            self.assertIn("Qdrant accessible via service discovery", logs_content)
            # Verify actual service discovery verification completed
            self.assertIn(
                "Service discovery successful - got service info", logs_content
            )
            self.assertTrue(
                "Service info validated with jq" in logs_content
                or "Service info contains expected title field" in logs_content
            )
            self.assertIn("Service discovery verification complete", logs_content)

            # Additional verification: check that client container exited successfully
            exit_code_result = subprocess.run(
                [
                    "docker",
                    "inspect",
                    "--format={{.State.ExitCode}}",
                    "test_client_complex",
                ],
                capture_output=True,
                text=True,
            )
            if exit_code_result.returncode == 0:
                exit_code = exit_code_result.stdout.strip()
                self.assertEqual(
                    exit_code,
                    "0",
                    "Test client should exit successfully after service discovery verification",
                )
        else:
            self.fail(f"Failed to get logs from test client: {logs_result.stderr}")
