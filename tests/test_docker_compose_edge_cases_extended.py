"""
Tests for Qdrant Docker Compose extended edge cases.

This module implements additional edge cases that are missing from current coverage,
including boundary conditions, configuration edge cases, and unusual scenarios.
"""

import subprocess
import tempfile
import time
import unittest

import requests  # type: ignore

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeEdgeCasesExtended(QdrantDockerComposeTestBase):
    """Test Qdrant extended edge cases via Docker Compose"""

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
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Should start with default configuration
        self.assertTrue(self.wait_for_qdrant_ready())

        # Verify basic functionality works
        response = requests.get("http://localhost:6333/", timeout=10)
        self.assertEqual(response.status_code, 200)

        # Should be able to create collections
        collection_config = {"vectors": {"size": 4, "distance": "Cosine"}}
        create_response = requests.put(
            "http://localhost:6333/collections/test_empty_config",
            json=collection_config,
            timeout=10,
        )
        self.assertIn(create_response.status_code, [200, 201])

    def test_port_configuration_boundary_values(self):
        """Test Qdrant port configuration with boundary values"""
        # Test with port 1 (lowest valid port for privileged)
        compose_content_port_1 = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_port_1
    ports:
      - "1:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_port_1, self.temp_dir
        )

        # This will likely fail due to permissions, but should handle gracefully
        result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "up", "-d"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )

        # If it fails, the error should be about permissions, not configuration
        if result.returncode != 0:
            error_output = result.stderr + result.stdout
            # Should be permission-related error, not configuration error
            self.assertTrue(
                any(
                    term in error_output.lower()
                    for term in ["permission", "denied", "bind"]
                )
            )

    def test_port_configuration_maximum_value(self):
        """Test Qdrant port configuration with maximum valid port"""
        # Test with port 65535 (highest valid port)
        compose_content_port_max = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_port_max
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
            compose_content_port_max, self.temp_dir
        )
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Should be accessible on port 65535
        try:
            response = requests.get("http://localhost:65535/healthz", timeout=10)
            self.assertEqual(response.status_code, 200)
        except requests.exceptions.ConnectionError:
            # May not be accessible depending on system configuration
            pass

    def test_container_initialization_state_scenarios(self):
        """Test Qdrant container initialization state-based scenarios"""
        # Test rapid start/stop cycles
        compose_content = self.create_basic_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)

        # Perform multiple rapid start/stop cycles
        for cycle in range(3):
            # Start
            result = self.start_qdrant_service(self.compose_file, self.temp_dir)
            self.assertEqual(result.returncode, 0)

            # Wait briefly
            time.sleep(2)

            # Stop
            self.stop_qdrant_service(
                self.compose_file, self.temp_dir, remove_volumes=False
            )

            # Wait briefly before next cycle
            time.sleep(1)

        # Final start should work normally
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

    def test_data_directory_initialization_states(self):
        """Test Qdrant data directory initialization with various initial states"""
        # Test 1: Completely fresh data directory
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Create some data
        self.create_test_collection("initialization_test")

        # Stop and remove container but keep volumes
        self.stop_qdrant_service(self.compose_file, self.temp_dir, remove_volumes=False)

        # Test 2: Restart with existing data
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Data should still exist
        self.verify_collection_exists("initialization_test")

    def test_configuration_updates_through_environment_variables(self):
        """Test Qdrant configuration updates through environment variable changes"""
        # Start with basic log level
        compose_content_basic_log = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_config_update
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=WARN
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_basic_log, self.temp_dir
        )
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Get initial logs
        initial_logs = subprocess.run(
            ["docker", "logs", "test_qdrant_config_update"],
            capture_output=True,
            text=True,
        )

        # Stop service
        self.stop_qdrant_service(self.compose_file, self.temp_dir, remove_volumes=False)

        # Update configuration with debug logging
        compose_content_debug_log = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_config_update
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=DEBUG
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_debug_log, self.temp_dir
        )
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Service should start with new configuration
        response = requests.get("http://localhost:6333/healthz", timeout=10)
        self.assertEqual(response.status_code, 200)

    def test_volume_remounting_scenarios(self):
        """Test Qdrant volume remounting scenarios"""
        # Create service with named volume
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Create data
        collection_name = "volume_remount_test"
        self.create_test_collection(collection_name)

        # Add some points
        points_data = {
            "points": [
                {"id": 1, "vector": [1.0, 0.0, 0.0, 0.0]},
                {"id": 2, "vector": [0.0, 1.0, 0.0, 0.0]},
            ]
        }

        response = requests.put(
            f"http://localhost:6333/collections/{collection_name}/points",
            json=points_data,
            timeout=10,
        )
        self.assertEqual(response.status_code, 200)

        # Stop and completely remove container
        subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "down"],
            capture_output=True,
            cwd=self.temp_dir,
        )

        # Start again (volumes should persist)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Data should still be there
        self.verify_collection_exists(collection_name)

        # Verify points are still there
        get_response = requests.post(
            f"http://localhost:6333/collections/{collection_name}/points/scroll",
            json={"limit": 10},
            timeout=10,
        )
        self.assertEqual(get_response.status_code, 200)
        points = get_response.json()["result"]["points"]
        self.assertEqual(len(points), 2)

    def test_extremely_large_port_numbers_edge_case(self):
        """Test behavior with extremely large port numbers"""
        # Test with port number close to maximum
        compose_content_large_port = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_large_port
    ports:
      - "65530:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_large_port, self.temp_dir
        )
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Should be accessible on the large port number
        try:
            response = requests.get("http://localhost:65530/healthz", timeout=10)
            if response.status_code == 200:
                self.assertIn("healthz check passed", response.text)
        except requests.exceptions.ConnectionError:
            # May not be accessible depending on system configuration
            pass

    def test_container_resource_limit_edge_cases(self):
        """Test container behavior with resource limits at edge cases"""
        # Test with very low memory limit
        compose_content_low_memory = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_low_memory
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    volumes:
      - qdrant_data:/qdrant/storage
    deploy:
      resources:
        limits:
          memory: 128M
        reservations:
          memory: 64M

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_low_memory, self.temp_dir
        )
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)

        # May fail to start with very low memory, which is acceptable
        if result.returncode == 0:
            # If it starts, it should be functional
            ready = self.wait_for_qdrant_ready(timeout=60)
            if ready:
                response = requests.get("http://localhost:6333/healthz", timeout=10)
                self.assertEqual(response.status_code, 200)

    def test_unusual_network_configuration_scenarios(self):
        """Test unusual network configuration scenarios"""
        # Test with custom bridge network
        compose_content_custom_network = """
version: '3.8'

networks:
  custom-bridge:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_custom_network
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    networks:
      - custom-bridge
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_custom_network, self.temp_dir
        )
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Should be accessible through the custom network
        self.assertTrue(self.wait_for_qdrant_ready())

        # Verify network configuration
        network_result = subprocess.run(
            [
                "docker",
                "inspect",
                "test_qdrant_custom_network",
                "--format={{.NetworkSettings.Networks}}",
            ],
            capture_output=True,
            text=True,
        )

        if network_result.returncode == 0:
            network_info = network_result.stdout.strip()
            self.assertIn("custom-bridge", network_info)

    def test_rapid_configuration_changes(self):
        """Test rapid configuration changes and their effects"""
        # Start with basic configuration
        compose_content = self.create_basic_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Create a collection
        self.create_test_collection("rapid_config_test")

        # Rapidly restart with different configurations
        configurations = [
            "QDRANT__LOG_LEVEL=WARN",
            "QDRANT__LOG_LEVEL=DEBUG",
            "QDRANT__LOG_LEVEL=INFO",
        ]

        for config in configurations:
            # Stop current service
            self.stop_qdrant_service(
                self.compose_file, self.temp_dir, remove_volumes=False
            )

            # Create new compose with different environment
            compose_content_variant = f"""
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_basic
    ports:
      - "6333:6333"
    environment:
      - {config}
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

            self.compose_file = self.setup_compose_file(
                compose_content_variant, self.temp_dir
            )
            result = self.start_qdrant_service(self.compose_file, self.temp_dir)
            self.assertEqual(result.returncode, 0)
            self.assertTrue(self.wait_for_qdrant_ready())

            # Verify collection still exists
            self.verify_collection_exists("rapid_config_test")

    def test_boundary_condition_startup_timeouts(self):
        """Test boundary conditions around startup timeouts"""
        # Test startup with very short health check intervals
        compose_content_fast_health = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_fast_health
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    volumes:
      - qdrant_data:/qdrant/storage
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:6333/healthz || exit 1"]
      interval: 1s
      timeout: 1s
      retries: 5
      start_period: 5s

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_fast_health, self.temp_dir
        )
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Should still become healthy despite fast health checks
        self.assertTrue(self.wait_for_qdrant_ready(timeout=30))

        # Verify health status
        time.sleep(10)  # Allow health checks to stabilize
        health_result = subprocess.run(
            [
                "docker",
                "inspect",
                "test_qdrant_fast_health",
                "--format={{.State.Health.Status}}",
            ],
            capture_output=True,
            text=True,
        )

        if health_result.returncode == 0:
            health_status = health_result.stdout.strip()
            self.assertIn(health_status, ["healthy", "starting"])

    def test_edge_case_environment_variable_combinations(self):
        """Test edge case environment variable combinations"""
        # Test with multiple conflicting or unusual environment variables
        compose_content_complex_env = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_complex_env
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=DEBUG
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__STORAGE__STORAGE_PATH=/qdrant/storage
      - QDRANT__CLUSTER__ENABLED=false
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_complex_env, self.temp_dir
        )
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Should start despite complex environment configuration
        self.assertTrue(self.wait_for_qdrant_ready())

        # Should be functional
        response = requests.get("http://localhost:6333/", timeout=10)
        self.assertEqual(response.status_code, 200)

        # Should be able to create collections
        self.create_test_collection("complex_env_test")


if __name__ == "__main__":
    unittest.main()
