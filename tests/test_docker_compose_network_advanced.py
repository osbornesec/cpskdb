"""Tests for Qdrant Docker Compose advanced network functionality.

This module implements advanced network testing scenarios including network
isolation, custom configurations, and complex topologies.
"""

import contextlib
import shutil
import subprocess
import tempfile

import requests  # type: ignore

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeNetworkAdvanced(QdrantDockerComposeTestBase):
    """Test Qdrant advanced network functionality via Docker Compose."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.compose_file = None

    def tearDown(self):
        """Clean up test environment."""
        if self.compose_file:
            with contextlib.suppress(Exception):
                self.stop_qdrant_service(self.compose_file, self.temp_dir)
        # Clean up temporary directory
        if hasattr(self, "temp_dir") and self.temp_dir:
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_network_configuration_errors_handling(self):
        """Test Qdrant network configuration errors with invalid network setups."""
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

        result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "up", "-d"],
            check=False,
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )

        assert result.returncode != 0
        error_output = result.stderr + result.stdout
        assert 'network "nonexistent_network" not found' in error_output.lower()

    def test_accessible_from_host_development_environment(self):
        """Test Qdrant accessible from host development environment scenario."""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        assert result.returncode == 0

        assert self.wait_for_qdrant_ready()

        health_response = requests.get("http://localhost:6333/healthz", timeout=10)
        assert health_response.status_code == 200

        api_response = requests.get("http://localhost:6333/", timeout=10)
        assert api_response.status_code == 200

        collections_response = requests.get(
            "http://localhost:6333/collections", timeout=10
        )
        assert collections_response.status_code == 200

        collection_config = {"vectors": {"size": 4, "distance": "Cosine"}}
        create_response = requests.put(
            "http://localhost:6333/collections/host_access_test",
            json=collection_config,
            timeout=10,
        )
        assert create_response.status_code in [200, 201]

    def test_custom_network_driver_configurations(self):
        """Test custom network driver configurations."""
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
        assert result.returncode == 0

        assert self.wait_for_qdrant_ready()

        inspect_result = subprocess.run(
            [
                "docker",
                "inspect",
                "test_qdrant_custom_bridge",
                "--format={{.NetworkSettings.Networks}}",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        if inspect_result.returncode == 0:
            network_info = inspect_result.stdout or ""
            assert "custom-bridge" in network_info
            assert "172.25.0.10" in network_info
