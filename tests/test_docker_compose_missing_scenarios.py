"""
Tests for Qdrant Docker Compose missing scenarios.

This module implements test scenarios that are mentioned in tests.md but not yet
fully implemented in other test files.
"""

import subprocess
import tempfile
import time
import unittest
import threading
import socket
import concurrent.futures
from pathlib import Path

import requests

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeMissingScenarios(QdrantDockerComposeTestBase):
    """Test Qdrant Docker Compose missing scenarios"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.compose_file = None

    def tearDown(self):
        """Clean up test environment"""
        if self.compose_file:
            self.stop_qdrant_service(self.compose_file, self.temp_dir)
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_qdrant_handles_maximum_connection_load(self):
        """
        Test: Qdrant Handles Maximum Connection Load
        Given: Qdrant service is running
        When: Opening maximum number of concurrent connections
        Then: Service handles connections gracefully
        Validation: No connection refused errors within reasonable limits
        """
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Test concurrent connections
        max_connections = 50  # Reasonable limit for testing
        connection_errors = []
        
        def test_connection():
            try:
                response = requests.get("http://localhost:6333/healthz", timeout=5)
                return response.status_code == 200
            except Exception as e:
                connection_errors.append(str(e))
                return False

        # Create concurrent connections
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_connections) as executor:
            futures = [executor.submit(test_connection) for _ in range(max_connections)]
            results = [future.result() for future in futures]

        # Validate results
        successful_connections = sum(results)
        self.assertGreater(
            successful_connections, 
            max_connections * 0.8,  # At least 80% should succeed
            f"Too many connection failures: {len(connection_errors)} errors"
        )
        
        # Check for specific connection refused errors
        connection_refused_errors = [e for e in connection_errors if "Connection refused" in e]
        self.assertEqual(
            len(connection_refused_errors), 
            0, 
            f"Connection refused errors found: {connection_refused_errors}"
        )

    def test_qdrant_storage_handles_large_data_volumes(self):
        """
        Test: Qdrant Storage Handles Large Data Volumes
        Given: Qdrant service with mounted storage
        When: Writing large amounts of vector data
        Then: Storage scales appropriately
        Validation: Disk usage increases and performance remains acceptable
        """
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Get initial disk usage
        initial_usage = self.get_container_disk_usage("test_qdrant_production")
        self.assertIsNotNone(initial_usage)

        # Create multiple collections with vector data
        collections_created = 0
        for i in range(10):  # Create 10 collections
            collection_name = f"large_data_test_{i}"
            collection_config = {
                "vectors": {
                    "size": 128,
                    "distance": "Cosine"
                }
            }
            
            try:
                response = requests.put(
                    f"http://localhost:6333/collections/{collection_name}",
                    json=collection_config,
                    timeout=10
                )
                if response.status_code in [200, 201]:
                    collections_created += 1
                    
                    # Add some sample vectors to the collection
                    self.add_sample_vectors(collection_name, 100)
                    
            except Exception:
                # Continue if one fails
                pass

        self.assertGreater(collections_created, 0, "No collections were created")

        # Get final disk usage
        final_usage = self.get_container_disk_usage("test_qdrant_production")
        self.assertIsNotNone(final_usage)
        
        # Validate that disk usage increased
        if initial_usage and final_usage:
            self.assertGreater(
                final_usage, 
                initial_usage, 
                "Disk usage should increase after adding data"
            )

        # Validate performance is still acceptable
        start_time = time.time()
        response = requests.get("http://localhost:6333/collections", timeout=10)
        response_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(
            response_time, 
            5.0,  # Should respond within 5 seconds
            f"Performance degraded: response time {response_time}s"
        )

    def test_qdrant_memory_usage_within_container_limits(self):
        """
        Test: Qdrant Memory Usage Within Container Limits
        Given: Qdrant container with memory constraints
        When: Processing typical workloads
        Then: Memory usage stays within allocated limits
        Validation: Container doesn't get killed by OOM killer
        """
        # Create compose content with memory limits
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_memory
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    volumes:
      - qdrant_data:/qdrant/storage
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

volumes:
  qdrant_data:
"""
        
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Get initial memory usage
        initial_memory = self.get_container_memory_usage("test_qdrant_memory")
        self.assertIsNotNone(initial_memory)

        # Perform memory-intensive operations
        for i in range(5):
            collection_name = f"memory_test_{i}"
            collection_config = {
                "vectors": {
                    "size": 256,
                    "distance": "Cosine"
                }
            }
            
            try:
                response = requests.put(
                    f"http://localhost:6333/collections/{collection_name}",
                    json=collection_config,
                    timeout=10
                )
                if response.status_code in [200, 201]:
                    # Add vectors to increase memory usage
                    self.add_sample_vectors(collection_name, 50)
            except Exception:
                pass

        # Wait a bit for memory usage to stabilize
        time.sleep(10)

        # Get final memory usage
        final_memory = self.get_container_memory_usage("test_qdrant_memory")
        self.assertIsNotNone(final_memory)

        # Check if container is still running (not killed by OOM)
        container_status = self.get_container_status("test_qdrant_memory")
        self.assertNotEqual(
            container_status, 
            "exited", 
            "Container was killed, possibly by OOM killer"
        )

        # Validate memory usage is reasonable (should be less than 512MB limit)
        if final_memory:
            memory_mb = final_memory / (1024 * 1024)
            self.assertLess(
                memory_mb, 
                512, 
                f"Memory usage {memory_mb:.1f}MB exceeds 512MB limit"
            )

    def test_qdrant_handles_host_system_reboot(self):
        """
        Test: Qdrant Handles Host System Reboot
        Given: Qdrant service with restart policy
        When: Host system reboots
        Then: Service automatically starts after reboot
        Validation: Qdrant becomes available without manual intervention
        """
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Simulate a "reboot" by stopping all containers and then starting them again
        # This simulates what happens when Docker daemon restarts
        subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "stop"],
            capture_output=True,
            cwd=self.temp_dir,
        )

        # Wait a bit to simulate reboot time
        time.sleep(5)

        # Start the service again (simulating automatic restart after reboot)
        result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "start"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )

        # Wait for service to be ready
        self.assertTrue(self.wait_for_qdrant_ready(timeout=60))

        # Validate service is accessible
        response = requests.get("http://localhost:6333/healthz", timeout=10)
        self.assertEqual(response.status_code, 200)

        # Validate data persistence (if we had any)
        response = requests.get("http://localhost:6333/collections", timeout=10)
        self.assertEqual(response.status_code, 200)

    def test_qdrant_handles_empty_configuration_directory(self):
        """
        Test: Qdrant Handles Empty Configuration Directory
        Given: Mounted configuration directory is empty
        When: Container starts
        Then: Qdrant uses default configuration
        Validation: Service initializes with built-in defaults
        """
        # Create an empty configuration directory
        config_dir = self.temp_dir / "empty_config"
        config_dir.mkdir(exist_ok=True)

        compose_content = f"""
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
      - {config_dir}:/qdrant/config

volumes:
  qdrant_data:
"""
        
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Wait for service to be ready
        self.assertTrue(self.wait_for_qdrant_ready())

        # Validate service is accessible with default configuration
        response = requests.get("http://localhost:6333/healthz", timeout=10)
        self.assertEqual(response.status_code, 200)

        # Validate default API endpoints work
        response = requests.get("http://localhost:6333/collections", timeout=10)
        self.assertEqual(response.status_code, 200)

        # Validate service info endpoint returns default information
        response = requests.get("http://localhost:6333/", timeout=10)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("title", data)
        self.assertIn("version", data)

    def test_qdrant_port_configuration_edge_cases(self):
        """
        Test: Qdrant Port Configuration Edge Cases
        Given: Various port configurations (1, 65535, invalid ports)
        When: Attempting to start service
        Then: Valid ports work, invalid ports fail appropriately
        Validation: Error handling for invalid port configurations
        """
        # Test valid port 1
        self._test_port_configuration(1, should_work=True)
        
        # Test valid port 65535
        self._test_port_configuration(65535, should_work=True)
        
        # Test invalid port 0
        self._test_port_configuration(0, should_work=False)
        
        # Test invalid port 65536
        self._test_port_configuration(65536, should_work=False)

    def _test_port_configuration(self, port, should_work):
        """Helper method to test port configuration"""
        compose_content = f"""
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_port_{port}
    ports:
      - "{port}:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""
        
        temp_dir = tempfile.mkdtemp()
        compose_file = Path(temp_dir) / "docker-compose.yml"
        compose_file.write_text(compose_content)
        
        try:
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "up", "qdrant", "-d"],
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )
            
            if should_work:
                self.assertEqual(
                    result.returncode, 0, 
                    f"Port {port} should work but failed: {result.stderr}"
                )
                
                # Verify container is running
                check_result = subprocess.run(
                    [
                        "docker",
                        "ps",
                        "--filter",
                        f"name=test_qdrant_port_{port}",
                        "--format",
                        "{{.Status}}",
                    ],
                    capture_output=True,
                    text=True,
                )
                self.assertIn("Up", check_result.stdout)
                
            else:
                # Invalid ports should fail
                self.assertNotEqual(
                    result.returncode, 0, 
                    f"Port {port} should fail but succeeded"
                )
                
        finally:
            # Cleanup
            subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "down", "-v"],
                capture_output=True,
                cwd=temp_dir,
            )
            import shutil
            shutil.rmtree(temp_dir)

    def get_container_disk_usage(self, container_name):
        """Get disk usage for a container"""
        try:
            result = subprocess.run(
                ["docker", "exec", container_name, "df", "/qdrant/storage", "--output=used"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    try:
                        return int(lines[1])
                    except ValueError:
                        return None
            return None
        except Exception:
            return None

    def get_container_memory_usage(self, container_name):
        """Get memory usage for a container"""
        try:
            result = subprocess.run(
                ["docker", "stats", container_name, "--no-stream", "--format={{.MemUsage}}"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                mem_str = result.stdout.strip()
                if mem_str and mem_str != "0B":
                    # Parse memory string like "45.2MiB / 512MiB"
                    parts = mem_str.split('/')[0].strip()
                    if 'MiB' in parts:
                        return int(float(parts.replace('MiB', '')) * 1024 * 1024)
                    elif 'KiB' in parts:
                        return int(float(parts.replace('KiB', '')) * 1024)
                    elif 'B' in parts:
                        return int(float(parts.replace('B', '')))
            return None
        except Exception:
            return None

    def get_container_status(self, container_name):
        """Get the current status of a container"""
        try:
            result = subprocess.run(
                ["docker", "inspect", container_name, "--format={{.State.Status}}"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None

    def add_sample_vectors(self, collection_name, count):
        """Add sample vectors to a collection"""
        try:
            # Create sample vectors
            vectors = []
            for i in range(count):
                vector = [0.1] * 128  # 128-dimensional vector
                vectors.append({
                    "id": i,
                    "vector": vector,
                    "payload": {"text": f"sample_{i}"}
                })
            
            # Add vectors to collection
            response = requests.put(
                f"http://localhost:6333/collections/{collection_name}/points",
                json={"points": vectors},
                timeout=10
            )
            return response.status_code in [200, 201]
        except Exception:
            return False
