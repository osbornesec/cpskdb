"""
Tests for Qdrant Docker Compose configuration edge cases.

This module tests configuration-related edge cases including empty directories,
environment variable combinations, and rapid configuration changes.
"""

import subprocess
import tempfile
import time
import unittest

import requests  # type: ignore

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeConfigEdgeCases(QdrantDockerComposeTestBase):
    """Test Qdrant configuration edge cases via Docker Compose"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.compose_file = None

    def tearDown(self):
        """Clean up test environment"""
        if self.compose_file:
            self.stop_qdrant_service(self.compose_file, self.temp_dir)

    def test_empty_configuration_directory_handling(self):
        """Test Qdrant handles empty configuration directory scenario"""
        # Create compose with minimal configuration
        compose_content_minimal = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_empty_config
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_minimal, self.temp_dir
        )

        # Start service
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Wait for service to be ready
        self.assertTrue(self.wait_for_qdrant_ready())

        # Verify service starts with default configuration
        response = requests.get("http://localhost:6333/", timeout=30)
        self.assertEqual(response.status_code, 200)

        # Check telemetry works with minimal config
        telemetry_response = requests.get("http://localhost:6333/telemetry", timeout=30)
        self.assertEqual(telemetry_response.status_code, 200)

        # Stop service
        self.stop_qdrant_service(self.compose_file, self.temp_dir)

    def test_configuration_updates_through_environment_variables(self):
        """Test dynamic configuration updates via environment variables"""
        compose_content_env_update = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_config_update
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=WARN
      - QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS=2
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_env_update, self.temp_dir
        )

        # Start service
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Get initial logs
        _ = subprocess.run(
            ["docker", "logs", "test_qdrant_config_update"],
            capture_output=True,
            text=True,
        )

        # Stop service
        self.stop_qdrant_service(self.compose_file, self.temp_dir, remove_volumes=False)

        # Update environment variables
        compose_content_updated = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_config_update
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=DEBUG  # Changed from WARN
      - QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS=4  # Changed from 2
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        # Update compose file with new environment
        self.compose_file = self.setup_compose_file(
            compose_content_updated, self.temp_dir
        )

        # Restart with updated configuration
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Verify service responds after configuration change
        response = requests.get("http://localhost:6333/", timeout=30)
        self.assertEqual(response.status_code, 200)

        # Stop service
        self.stop_qdrant_service(self.compose_file, self.temp_dir)

    def test_unusual_network_configuration_scenarios(self):
        """Test unusual network configuration scenarios"""
        compose_content_unusual_network = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_unusual_network
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    volumes:
      - qdrant_data:/qdrant/storage
    networks:
      - custom_network
    dns:
      - 8.8.8.8
      - 8.8.4.4

networks:
  custom_network:
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 172.30.0.0/16

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_unusual_network, self.temp_dir
        )

        # Start service with custom network
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Wait for service to be ready
        self.assertTrue(self.wait_for_qdrant_ready())

        # Verify service works with custom network configuration
        response = requests.get("http://localhost:6333/", timeout=30)
        self.assertEqual(response.status_code, 200)

        # Stop service
        self.stop_qdrant_service(self.compose_file, self.temp_dir)

    def test_rapid_configuration_changes(self):
        """Test rapid configuration changes and service stability"""
        base_compose = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_rapid_changes
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL={log_level}
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        log_levels = ["INFO", "WARN", "DEBUG"]

        for i, log_level in enumerate(log_levels):
            compose_content = base_compose.format(log_level=log_level)
            self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)

            # Start/restart service with new configuration
            if i > 0:
                # Stop previous instance
                self.stop_qdrant_service(
                    self.compose_file, self.temp_dir, remove_volumes=False
                )

            result = self.start_qdrant_service(self.compose_file, self.temp_dir)
            self.assertEqual(result.returncode, 0)
            self.assertTrue(self.wait_for_qdrant_ready(max_wait=30))

            # Verify service responds after each configuration change
            response = requests.get("http://localhost:6333/", timeout=30)
            self.assertEqual(response.status_code, 200)

            # Brief pause between changes
            time.sleep(2)

        # Final cleanup
        self.stop_qdrant_service(self.compose_file, self.temp_dir)

    def test_edge_case_environment_variable_combinations(self):
        """Test edge case combinations of environment variables"""
        compose_content_complex_env = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_complex_env
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=TRACE  # Most verbose logging
      - QDRANT__STORAGE__OPTIMIZERS_OVERWRITE=true
      - QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS=1
      - QDRANT__STORAGE__WAL_CAPACITY_MB=32
      - QDRANT__STORAGE__WAL_SEGMENTS_AHEAD=0
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_complex_env, self.temp_dir
        )

        # Start service with complex environment configuration
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Wait longer for service due to verbose logging and optimizations
        self.assertTrue(self.wait_for_qdrant_ready(max_wait=90))

        # Verify service responds despite complex configuration
        response = requests.get("http://localhost:6333/", timeout=30)
        self.assertEqual(response.status_code, 200)

        # Test telemetry with complex configuration
        telemetry_response = requests.get("http://localhost:6333/telemetry", timeout=30)
        self.assertEqual(telemetry_response.status_code, 200)

        # Stop service
        self.stop_qdrant_service(self.compose_file, self.temp_dir)


if __name__ == "__main__":
    unittest.main()
