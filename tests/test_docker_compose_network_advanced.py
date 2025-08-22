"""
Tests for Qdrant Docker Compose advanced network functionality.

This module implements advanced network testing scenarios including network
isolation, custom configurations, and complex topologies.
"""

import subprocess
import tempfile
import time
import unittest

import requests

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeNetworkAdvanced(QdrantDockerComposeTestBase):
    """Test Qdrant advanced network functionality via Docker Compose"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.compose_file = None

    def tearDown(self):
        """Clean up test environment"""
        if self.compose_file:
            self.stop_qdrant_service(self.compose_file, self.temp_dir)

    def test_network_configuration_errors_handling(self):
        """Test Qdrant network configuration errors with invalid network setups"""
        compose_content_invalid_network = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_invalid_network
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    networks:
      - nonexistent_network
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_invalid_network, self.temp_dir
        )

        # Should fail with network error
        result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "up", "-d"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )

        # Should fail due to missing network
        self.assertNotEqual(result.returncode, 0)
        error_output = result.stderr + result.stdout
        self.assertTrue(
            any(
                term in error_output.lower()
                for term in ["network", "not found", "nonexistent"]
            )
        )

    def test_accessible_from_host_development_environment(self):
        """Test Qdrant accessible from host development environment scenario"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

        # Test accessibility from host environment
        health_response = requests.get("http://localhost:6333/healthz", timeout=10)
        self.assertEqual(health_response.status_code, 200)

        api_response = requests.get("http://localhost:6333/", timeout=10)
        self.assertEqual(api_response.status_code, 200)

        collections_response = requests.get(
            "http://localhost:6333/collections", timeout=10
        )
        self.assertEqual(collections_response.status_code, 200)

        collection_config = {"vectors": {"size": 4, "distance": "Cosine"}}
        create_response = requests.put(
            "http://localhost:6333/collections/host_access_test",
            json=collection_config,
            timeout=10,
        )
        self.assertIn(create_response.status_code, [200, 201])

    def test_custom_network_driver_configurations(self):
        """Test custom network driver configurations"""
        compose_content_custom_bridge = """
version: '3.8'

networks:
  custom-bridge:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: br-qdrant-test
    ipam:
      driver: default
      config:
        - subnet: 172.25.0.0/16
          gateway: 172.25.0.1

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_custom_bridge
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    networks:
      custom-bridge:
        ipv4_address: 172.25.0.10
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_custom_bridge, self.temp_dir
        )
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

        inspect_result = subprocess.run(
            [
                "docker",
                "inspect",
                "test_qdrant_custom_bridge",
                "--format={{.NetworkSettings.Networks}}",
            ],
            capture_output=True,
            text=True,
        )

        if inspect_result.returncode == 0:
            network_info = inspect_result.stdout.strip()
            self.assertIn("custom-bridge", network_info)
            self.assertIn("172.25.0.10", network_info)

    def test_ipv6_network_configuration_support(self):
        """Test IPv6 network configuration support if available"""
        compose_content_ipv6 = """
version: '3.8'

networks:
  ipv6-network:
    driver: bridge
    enable_ipv6: true
    ipam:
      config:
        - subnet: 2001:db8::/32

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_ipv6
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    networks:
      - ipv6-network
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(compose_content_ipv6, self.temp_dir)

        result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "up", "-d"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )

        if result.returncode == 0:
            ready = self.wait_for_qdrant_ready(timeout=30)
            if ready:
                response = requests.get("http://localhost:6333/healthz", timeout=10)
                self.assertEqual(response.status_code, 200)
        else:
            error_output = result.stderr + result.stdout
            ipv6_related = any(
                term in error_output.lower()
                for term in ["ipv6", "inet6", "network", "subnet"]
            )
            if not ipv6_related:
                self.fail(f"Unexpected error (not IPv6-related): {error_output}")