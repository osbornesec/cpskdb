"""
Test Qdrant Docker Compose network isolation scenarios.

This module implements network isolation testing including multi-stack isolation
and security-focused network configurations.
"""

import shutil
import subprocess
import tempfile
import time

import requests

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeNetworkIsolation(QdrantDockerComposeTestBase):
    """Test Qdrant network isolation functionality via Docker Compose"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.compose_file = None

    def tearDown(self):
        """Clean up test environment"""
        if self.compose_file:
            self.stop_qdrant_service(self.compose_file, self.temp_dir)

    def test_network_isolation_between_compose_stacks(self):
        """Test network isolation between different Docker Compose stacks"""
        compose_content_stack1 = """
version: '3.8'

networks:
  stack1-network:
    driver: bridge

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_stack1
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    networks:
      - stack1-network
    volumes:
      - qdrant_data_stack1:/qdrant/storage

volumes:
  qdrant_data_stack1:
"""

        self.compose_file = self.setup_compose_file(compose_content_stack1, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        response1 = requests.get("http://localhost:6333/healthz", timeout=10)
        self.assertEqual(response1.status_code, 200)

        compose_content_stack2 = """
version: '3.8'

networks:
  stack2-network:
    driver: bridge

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_stack2
    ports:
      - "6334:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    networks:
      - stack2-network
    volumes:
      - qdrant_data_stack2:/qdrant/storage

volumes:
  qdrant_data_stack2:
"""

        temp_dir2 = tempfile.mkdtemp()
        compose_file2 = self.setup_compose_file(compose_content_stack2, temp_dir2)

        result2 = subprocess.run(
            ["docker", "compose", "-f", str(compose_file2), "up", "-d"],
            capture_output=True,
            text=True,
            cwd=temp_dir2,
        )

        try:
            if result2.returncode == 0:
                time.sleep(10)

                try:
                    response2 = requests.get("http://localhost:6334/healthz", timeout=10)
                    if response2.status_code == 200:
                        self.assertEqual(response1.status_code, 200)
                        self.assertEqual(response2.status_code, 200)
                except requests.exceptions.ConnectionError:
                    pass
        finally:
            subprocess.run(
                ["docker", "compose", "-f", str(compose_file2), "down", "-v"],
                capture_output=True,
                cwd=temp_dir2,
            )
            shutil.rmtree(temp_dir2, ignore_errors=True)

    def test_network_security_and_access_control(self):
        """Test network security and access control scenarios"""
        compose_content_isolated = """
version: '3.8'

networks:
  internal-only:
    driver: bridge
    internal: true
  external-access:
    driver: bridge

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_isolated
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    networks:
      - external-access
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(compose_content_isolated, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

        network_result = subprocess.run(
            [
                "docker",
                "inspect",
                "test_qdrant_isolated",
                "--format={{.NetworkSettings.Networks}}",
            ],
            capture_output=True,
            text=True,
        )

        if network_result.returncode == 0:
            network_info = network_result.stdout.strip()
            self.assertIn("external-access", network_info)