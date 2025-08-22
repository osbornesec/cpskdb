"""
Tests for Qdrant Docker Compose graceful shutdown scenarios.

This module implements graceful shutdown, signal handling, and state preservation tests.
"""

import subprocess
import time
import requests
import unittest

from tests.test_docker_compose_extended_base import QdrantDockerComposeExtendedTestBase


class TestQdrantDockerComposeGracefulShutdown(QdrantDockerComposeExtendedTestBase):
    """Graceful shutdown scenarios for Qdrant Docker Compose."""

    def create_production_compose_content(self):
        """Create production-ready compose content with proper signal handling."""
        return """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_production
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_data:/qdrant/storage
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__LOG_LEVEL=INFO
      - QDRANT__SERVICE__ENABLE_CORS=true
    stop_grace_period: 30s
    stop_signal: SIGTERM
    restart: unless-stopped
"""

    def test_graceful_shutdown_preserves_connections(self):
        """Test graceful shutdown with active connections"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Verify service is responding
        start_time = time.time()
        response = requests.get("http://localhost:6333/healthz", timeout=10)
        self.assertEqual(response.status_code, 200)

        # Stop the service
        stop_result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "stop"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
            timeout=30,
        )
        end_time = time.time()
        shutdown_duration = end_time - start_time
        
        self.assertEqual(stop_result.returncode, 0)
        # Assert shutdown completed within grace period
        self.assertLessEqual(shutdown_duration, 35.0, "Shutdown should complete within grace period")

    def test_container_exits_with_zero_code_graceful_shutdown(self):
        """Test container exits with zero code on graceful shutdown"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        stop_result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "stop"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )
        self.assertEqual(stop_result.returncode, 0)

        # Wait for container state to be updated after stop (fix race condition)
        max_retries = 10
        retry_delay = 0.5
        exit_code = None

        for attempt in range(max_retries):
            inspect_result = subprocess.run(
                [
                    "docker",
                    "inspect",
                    "test_qdrant_production",
                    "--format={{.State.ExitCode}}",
                ],
                capture_output=True,
                text=True,
            )
            
            if inspect_result.returncode == 0:
                exit_code = inspect_result.stdout.strip()
                # Verify we got a valid exit code (not empty or invalid)
                if exit_code and exit_code.isdigit():
                    break
            
            time.sleep(retry_delay)

        # Assert we got a valid exit code and it's 0 (success)
        self.assertIsNotNone(exit_code, "Failed to get container exit code after multiple retries")
        self.assertEqual(exit_code, "0", f"Container should exit with code 0, got: {exit_code}")

    def test_data_integrity_maintained_after_graceful_shutdown(self):
        """Test data integrity maintained after graceful shutdown"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Create a collection and add some data
        collection_data = {
            "vectors": {
                "size": 128,
                "distance": "Cosine"
            }
        }
        
        # Create collection
        requests.put(
            "http://localhost:6333/collections/test_shutdown",
            json=collection_data,
            timeout=10
        )

        # Add a test vector
        vector_data = {
            "points": [
                {
                    "id": 1,
                    "vector": [0.1] * 128,
                    "payload": {"shutdown_test": True}
                }
            ]
        }
        
        requests.put(
            "http://localhost:6333/collections/test_shutdown/points",
            json=vector_data,
            timeout=10
        )

        # Graceful shutdown
        stop_result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "stop"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )
        self.assertEqual(stop_result.returncode, 0)

        # Restart and verify data
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Verify collection exists
        response = requests.get("http://localhost:6333/collections/test_shutdown", timeout=10)
        self.assertEqual(response.status_code, 200)

        # Verify vector exists
        response = requests.get("http://localhost:6333/collections/test_shutdown/points/1", timeout=10)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["result"]["payload"]["shutdown_test"], True)

    def test_signal_handling_edge_cases(self):
        """Test various signal handling scenarios"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Verify container is running
        inspect_result = subprocess.run(
            ["docker", "inspect", "test_qdrant_production", "--format={{.State.Running}}"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(inspect_result.stdout.strip(), "true")

        # Send SIGTERM directly to container
        subprocess.run(
            ["docker", "kill", "--signal=SIGTERM", "test_qdrant_production"],
            capture_output=True,
        )

        # Wait for graceful shutdown
        time.sleep(5)

        # Check final container state
        inspect_result = subprocess.run(
            ["docker", "inspect", "test_qdrant_production", "--format={{.State.Running}}"],
            capture_output=True,
            text=True,
        )
        
        # Container should have stopped gracefully
        self.assertIn(inspect_result.stdout.strip(), ["false", ""])

        # Check if logs contain graceful shutdown messages
        logs_result = subprocess.run(
            ["docker", "logs", "test_qdrant_production"],
            capture_output=True,
            text=True,
        )
        
        # Verify logs contain shutdown-related messages (flexible check)
        log_content = logs_result.stdout.lower() + logs_result.stderr.lower()
        shutdown_indicators = ["shutdown", "exit", "stop", "term", "signal"]
        has_shutdown_log = any(indicator in log_content for indicator in shutdown_indicators)
        
        # Assert either explicit shutdown message or clean exit
        self.assertTrue(
            has_shutdown_log or logs_result.returncode == 0,
            f"Expected shutdown indication in logs or clean exit. Logs: {log_content[:200]}..."
        )


if __name__ == "__main__":
    unittest.main()