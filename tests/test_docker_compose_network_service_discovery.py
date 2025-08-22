"""
Test Qdrant Docker Compose service discovery scenarios.

This module implements service discovery testing with complex network topologies
and multi-service communication patterns.
"""

import subprocess
import tempfile
import time

import requests

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
    command: >
      sh -c "
        echo 'Test client starting...';
        while ! wget -q --spider http://qdrant:6333/healthz; do
          echo 'Waiting for Qdrant...';
          sleep 2;
        done;
        echo 'Qdrant accessible via service discovery';
        sleep 300;
      "
    depends_on:
      - qdrant

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(compose_content_complex, self.temp_dir)

        result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "up", "-d"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())
        time.sleep(10)

        logs_result = subprocess.run(
            ["docker", "logs", "test_client_complex"],
            capture_output=True,
            text=True,
        )

        if logs_result.returncode == 0:
            logs_content = logs_result.stdout + logs_result.stderr
            self.assertIn("Qdrant accessible via service discovery", logs_content)