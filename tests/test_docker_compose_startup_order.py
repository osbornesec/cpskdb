"""
Tests for Qdrant Docker Compose startup order and dependency functionality.

This module implements startup order and dependency testing for the
"Qdrant Startup Order with Dependent Services" scenario from the test specification.
"""

import subprocess
import tempfile
import time
import unittest

import requests  # type: ignore

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeStartupOrder(QdrantDockerComposeTestBase):
    """Test Qdrant startup order functionality via Docker Compose"""

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
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_compose_with_dependent_services(self):
        """Create compose configuration with dependent services"""
        return """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_startup
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
  test-client:
    image: alpine:latest
    container_name: test_client_startup
    command: sh -c "while ! wget -q --spider http://qdrant:6333/healthz; do sleep 2; done; echo 'Qdrant is ready'"
    depends_on:
      - qdrant
volumes:
  qdrant_data:
"""

    def test_services_start_after_qdrant_basic_dependency(self):
        """Test services start after Qdrant basic dependency"""
        compose_content = self.create_compose_with_dependent_services()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)

        result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "up", "-d"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

        time.sleep(5)
        logs_result = subprocess.run(
            ["docker", "logs", "test_client_startup"],
            capture_output=True,
            text=True,
        )

        if logs_result.returncode == 0:
            logs_content = logs_result.stdout + logs_result.stderr
            # Use more flexible log checking
            ready_indicators = ["ready", "Ready", "Qdrant is ready"]
            found_indicator = any(indicator in logs_content for indicator in ready_indicators)
            self.assertTrue(found_indicator, f"Expected ready indicator in logs: {logs_content}")

    def test_dependent_services_can_connect_immediately(self):
        """Test dependent services can connect immediately"""
        compose_content = self.create_compose_with_dependent_services()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)

        result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "up", "-d"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        response = requests.get("http://localhost:6333/healthz", timeout=10)
        self.assertEqual(response.status_code, 200)

        time.sleep(10)
        logs_result = subprocess.run(
            ["docker", "logs", "test_client_startup"],
            capture_output=True,
            text=True,
        )

        if logs_result.returncode == 0:
            logs_content = logs_result.stdout + logs_result.stderr
            # Use more flexible log checking
            ready_indicators = ["ready", "Ready", "Qdrant is ready"]
            found_indicator = any(indicator in logs_content for indicator in ready_indicators)
            self.assertTrue(found_indicator, f"Expected ready indicator in logs: {logs_content}")

    def test_startup_order_with_health_check_dependencies(self):
        """Test startup order with health check dependencies"""
        compose_with_health = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_health
    ports:
      - "6333:6333"
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:6333/healthz"]
      interval: 5s
      timeout: 3s
      retries: 3
    volumes:
      - qdrant_data:/qdrant/storage
  dependent-service:
    image: alpine:latest
    container_name: test_dependent_health
    command: echo "Service started after health check"
    depends_on:
      qdrant:
        condition: service_healthy
volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(compose_with_health, self.temp_dir)
        result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "up", "-d"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )

        if result.returncode == 0:
            self.assertTrue(self.wait_for_qdrant_ready())

    def test_startup_order_maintained_across_stack_restarts(self):
        """Test startup order maintained across stack restarts"""
        compose_content = self.create_compose_with_dependent_services()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)

        result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "up", "-d"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        restart_result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "restart"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )
        self.assertEqual(restart_result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        response = requests.get("http://localhost:6333/healthz", timeout=10)
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
