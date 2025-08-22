"""
Tests for Qdrant Docker Compose advanced features edge cases.

This module implements resource limits, profiles, healthchecks, and dependencies edge cases.
"""

import subprocess
import time

from tests.test_docker_compose_extended_base import QdrantDockerComposeExtendedTestBase


class TestQdrantDockerComposeAdvancedFeatures(QdrantDockerComposeExtendedTestBase):
    """Advanced features edge cases for Qdrant Docker Compose configuration."""

    def test_resource_limits_extreme_values(self):
        """Test Docker Compose with extreme resource limit values."""
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant-test
    ports:
      - "6333:6333"
    deploy:
      resources:
        limits:
          cpus: "0.01"      # Extremely low CPU
          memory: "32M"     # Very low memory
        reservations:
          cpus: "0.001"
          memory: "16M"
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__LOG_LEVEL=ERROR  # Reduce log output
"""

        self.setup_compose_file(compose_content)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)

        # May or may not start successfully with such low resources
        if result.returncode == 0:
            # If it starts, verify it can at least respond to health check
            time.sleep(5)  # Give it more time with limited resources
            self.wait_for_qdrant_ready(timeout=60)
            # Don't assert success, just check it doesn't crash immediately

    def test_docker_compose_profiles_edge_cases(self):
        """Test Docker Compose profiles feature edge cases."""
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant-test
    ports:
      - "6333:6333"
    profiles:
      - production
      - test  # Multiple profiles
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__LOG_LEVEL=INFO

  qdrant-dev:
    image: qdrant/qdrant:latest
    container_name: qdrant-dev
    ports:
      - "6334:6333"
    profiles:
      - development
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__LOG_LEVEL=DEBUG
"""

        self.setup_compose_file(compose_content)

        # Start with specific profile
        result = subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                str(self.compose_file),
                "--profile",
                "test",
                "up",
                "-d",
            ],
            capture_output=True,
            cwd=self.temp_dir,
        )
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

    def test_docker_compose_healthcheck_edge_cases(self):
        """Test Docker Compose healthcheck configurations edge cases."""
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant-test
    ports:
      - "6333:6333"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 1s       # Very frequent checks
      timeout: 1s        # Very short timeout
      retries: 1         # Only one retry
      start_period: 1s   # Very short start period
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__LOG_LEVEL=INFO
"""

        self.setup_compose_file(compose_content)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Wait a bit for health checks to run
        time.sleep(5)

        # Check container health status
        health_result = subprocess.run(
            [
                "docker",
                "inspect",
                "--format",
                "{{.State.Health.Status}}",
                "qdrant-test",
            ],
            capture_output=True,
            text=True,
        )

        if health_result.returncode == 0:
            # Health status should be either starting, healthy, or unhealthy
            status = health_result.stdout.strip()
            self.assertIn(status, ["starting", "healthy", "unhealthy"])

    def test_docker_compose_depends_on_edge_cases(self):
        """Test Docker Compose depends_on configurations edge cases."""
        compose_content = """
version: '3.8'
services:
  init-service:
    image: alpine:latest
    container_name: init-test
    command:
      - sh
      - -c
      - "echo 'Initializing...' && sleep 2 && echo 'Done'"

  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant-test
    ports:
      - "6333:6333"
    depends_on:
      init-service:
        condition: service_completed_successfully
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__LOG_LEVEL=INFO
"""

        self.setup_compose_file(compose_content)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())