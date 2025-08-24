"""Tests for Qdrant Docker Compose boundary conditions.

This module tests boundary conditions including port limits, resource limits,
and timeout scenarios.
"""

import subprocess
import tempfile
import unittest

import requests  # type: ignore

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeBoundaryConditions(QdrantDockerComposeTestBase):
    """Test Qdrant boundary conditions via Docker Compose."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.compose_file = None

    def tearDown(self):
        """Clean up test environment."""
        if self.compose_file:
            self.stop_qdrant_service(self.compose_file, self.temp_dir)

    def test_port_configuration_boundary_values(self):
        """Test Qdrant with boundary port values."""
        # Test with port 1024 (minimum non-privileged port)
        compose_content_boundary = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_port_boundary
    ports:
      - "1024:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_boundary, self.temp_dir
        )

        # Start service
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        assert result.returncode == 0

        # Wait for service to be ready
        assert self.wait_for_qdrant_ready(port=1024, max_wait=60)

        # Verify service responds on boundary port
        response = requests.get("http://localhost:1024/", timeout=30)
        assert response.status_code == 200

        # Test telemetry endpoint
        telemetry_response = requests.get("http://localhost:1024/telemetry", timeout=30)
        assert telemetry_response.status_code == 200

        # Stop service
        self.stop_qdrant_service(self.compose_file, self.temp_dir)

    def test_port_configuration_maximum_value(self):
        """Test Qdrant with maximum valid port value."""
        # Test with port 65535 (maximum port value)
        compose_content_max_port = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_max_port
    ports:
      - "65535:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_max_port, self.temp_dir
        )

        # Start service
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        assert result.returncode == 0

        # Wait for service to be ready
        assert self.wait_for_qdrant_ready(port=65535, max_wait=60)

        # Stop service
        self.stop_qdrant_service(self.compose_file, self.temp_dir)

    def test_extremely_large_port_numbers_edge_case(self):
        """Test extremely large port numbers that should fail gracefully."""
        # Test with port number beyond valid range (should fail gracefully)
        compose_content_invalid_port = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_invalid_port
    ports:
      - "99999:6333"  # Invalid port number
    environment:
      - QDRANT__LOG_LEVEL=INFO
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_invalid_port, self.temp_dir
        )

        # This should fail with appropriate error
        result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "up", "-d"],
            check=False,
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )

        # Docker should reject invalid port configuration
        assert result.returncode != 0
        assert "invalid" in result.stderr.lower()

    def test_container_resource_limit_edge_cases(self):
        """Test edge cases with container resource limits."""
        compose_content_resource_limits = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_resource_limits
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    volumes:
      - qdrant_data:/qdrant/storage
    deploy:
      resources:
        limits:
          cpus: '0.1'  # Very low CPU limit
          memory: 128M  # Very low memory limit
        reservations:
          cpus: '0.05'
          memory: 64M

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_resource_limits, self.temp_dir
        )

        # Start service with resource constraints
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        assert result.returncode == 0

        # Service should start but may be slow due to constraints
        assert self.wait_for_qdrant_ready(max_wait=120)

        # Check that service responds despite resource constraints
        response = requests.get("http://localhost:6333/", timeout=60)
        assert response.status_code == 200

        # Stop service
        self.stop_qdrant_service(self.compose_file, self.temp_dir)

    def test_boundary_condition_startup_timeouts(self):
        """Test boundary conditions for service startup timeouts."""
        compose_content_slow_start = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_slow_start
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=DEBUG  # More verbose logging may slow startup
      - QDRANT__STORAGE__OPTIMIZERS_OVERWRITE=true
    volumes:
      - qdrant_data:/qdrant/storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/"]
      interval: 5s
      timeout: 3s
      retries: 20
      start_period: 30s

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_slow_start, self.temp_dir
        )

        # Start service
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        assert result.returncode == 0

        # Test with very short timeout (should fail)
        ready_fast = self.wait_for_qdrant_ready(max_wait=1)
        if not ready_fast:
            # This is expected for slow startup scenarios
            pass

        # Test with reasonable timeout (should succeed)
        assert self.wait_for_qdrant_ready(max_wait=60)

        # Stop service
        self.stop_qdrant_service(self.compose_file, self.temp_dir)


if __name__ == "__main__":
    unittest.main()
