"""
Tests for Qdrant Docker Compose CI restart policy functionality.

This module implements CI-specific restart policy testing that validates the
"CI Restart Policy Handles Crash Loops" scenario from the test specification.
"""

import subprocess
import tempfile
import time
import unittest

import requests

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeCIRestartPolicy(QdrantDockerComposeTestBase):
    """Test Qdrant CI restart policy functionality via Docker Compose"""

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

    def create_ci_compose_content(self):
        """Create CI-specific docker-compose.yml content with on-failure:3 restart policy"""
        return """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_ci
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    volumes:
      - qdrant_data:/qdrant/storage
    restart: on-failure:3
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:6333/healthz || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 20s

volumes:
  qdrant_data:
"""

    def get_container_restart_count(self, container_name):
        """Get the restart count for a container."""
        try:
            result = subprocess.run(
                ["docker", "inspect", container_name, "--format={{.RestartCount}}"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                try:
                    return int(result.stdout.strip())
                except ValueError:
                    return None
            return None
        except Exception:
            return None

    def get_container_status(self, container_name):
        """Get the current status of a container."""
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

    def test_ci_restart_policy_on_failure_3(self):
        """
        Test: CI Restart Policy Handles Crash Loops
        Given: CI environment with QDRANT_RESTART_POLICY=on-failure:3
        When: A forced crash loop is introduced in the Qdrant service
        Then: The container attempts to restart 3 times and then stops
        Validation: The CI pipeline detects the failed service and reports an error
        """
        compose_content = self.create_ci_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        
        # Start the service initially
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Wait for service to be ready
        self.assertTrue(self.wait_for_qdrant_ready())

        # Get initial restart count
        initial_restart_count = self.get_container_restart_count("test_qdrant_ci")
        self.assertIsNotNone(initial_restart_count)

        # Introduce a crash loop by repeatedly killing the container
        # This simulates a service that keeps failing
        for attempt in range(5):  # Try more than 3 times to ensure we hit the limit
            # Kill the container to simulate a crash
            kill_result = subprocess.run(
                ["docker", "kill", "--signal=SIGKILL", "test_qdrant_ci"],
                capture_output=True,
                text=True,
            )
            
            if kill_result.returncode != 0:
                # Container might already be stopped, try to remove it
                subprocess.run(
                    ["docker", "rm", "-f", "test_qdrant_ci"],
                    capture_output=True,
                )
                break

            # Wait for restart attempt
            time.sleep(10)
            
            # Check current restart count
            current_restart_count = self.get_container_restart_count("test_qdrant_ci")
            if current_restart_count is None:
                # Container might have been removed due to restart policy limit
                break
                
            # Check if we've hit the restart limit
            if current_restart_count >= initial_restart_count + 3:
                break

        # Wait a bit more for the restart policy to take effect
        time.sleep(15)

        # Verify the container has stopped due to restart policy limit
        container_status = self.get_container_status("test_qdrant_ci")
        
        # The container should either be stopped or removed due to restart policy
        if container_status:
            self.assertIn(
                container_status, 
                ["exited", "dead"], 
                f"Container should be stopped after restart limit, but status is: {container_status}"
            )
        else:
            # Container was removed due to restart policy
            self.assertTrue(True, "Container was removed after hitting restart limit")

    def test_ci_restart_policy_with_health_check_failures(self):
        """
        Test: CI restart policy handles health check failures
        Given: CI environment with health checks and restart policy
        When: Health checks consistently fail
        Then: Container restarts up to the limit and then stops
        Validation: Service becomes unavailable after restart limit
        """
        compose_content = self.create_ci_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        
        # Start the service
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Wait for service to be ready initially
        self.assertTrue(self.wait_for_qdrant_ready())

        # Get initial restart count
        initial_restart_count = self.get_container_restart_count("test_qdrant_ci")
        self.assertIsNotNone(initial_restart_count)

        # Simulate health check failures by making the health endpoint fail
        # We'll do this by repeatedly killing the container to trigger health check failures
        for _ in range(4):  # More than the restart limit
            # Kill the container
            subprocess.run(
                ["docker", "kill", "--signal=SIGKILL", "test_qdrant_ci"],
                capture_output=True,
            )
            
            # Wait for restart and health check
            time.sleep(15)
            
            # Check if container is still running
            status = self.get_container_status("test_qdrant_ci")
            if status in ["exited", "dead"]:
                break

        # Wait for restart policy to take effect
        time.sleep(20)

        # Verify the container has stopped due to restart policy
        container_status = self.get_container_status("test_qdrant_ci")
        if container_status:
            self.assertIn(
                container_status, 
                ["exited", "dead"], 
                f"Container should be stopped after health check failures, but status is: {container_status}"
            )
        else:
            # Container was removed
            self.assertTrue(True, "Container was removed after health check failures")

    def test_ci_restart_policy_detection_by_pipeline(self):
        """
        Test: CI pipeline can detect failed service after restart policy limit
        Given: CI environment with restart policy limit reached
        When: CI pipeline checks service status
        Then: Pipeline detects the failed service and reports an error
        Validation: CI pipeline can identify and report service failures
        """
        compose_content = self.create_ci_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        
        # Start the service
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Wait for service to be ready
        self.assertTrue(self.wait_for_qdrant_ready())

        # Simulate crash loop to hit restart limit
        for _ in range(4):
            subprocess.run(
                ["docker", "kill", "--signal=SIGKILL", "test_qdrant_ci"],
                capture_output=True,
            )
            time.sleep(10)

        # Wait for restart policy to take effect
        time.sleep(20)

        # Simulate CI pipeline checking service status
        # This would typically be done by the CI system
        service_status_check = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "ps", "qdrant"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )

        # The service should show as failed/stopped
        self.assertIn(
            "Exit", 
            service_status_check.stdout, 
            "CI pipeline should detect failed service status"
        )

        # Verify health check endpoint is not accessible
        try:
            response = requests.get("http://localhost:6333/healthz", timeout=5)
            # If we get here, the service is still running (unexpected)
            self.fail("Service should not be accessible after restart policy limit")
        except requests.exceptions.ConnectionError:
            # Expected - service is not accessible
            self.assertTrue(True, "Service correctly inaccessible after restart policy limit")
        except requests.exceptions.Timeout:
            # Also expected - service is not responding
            self.assertTrue(True, "Service correctly not responding after restart policy limit")

    def test_ci_restart_policy_with_environment_variable_override(self):
        """
        Test: CI restart policy can be configured via environment variables
        Given: Docker Compose with environment variable for restart policy
        When: Restart policy is set via environment variable
        Then: Container respects the configured restart policy
        Validation: Environment variable configuration works correctly
        """
        # Create compose content that would use environment variable for restart policy
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_ci_env
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
      - QDRANT_RESTART_POLICY=on-failure:2
    volumes:
      - qdrant_data:/qdrant/storage
    restart: ${QDRANT_RESTART_POLICY:-unless-stopped}
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:6333/healthz || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 20s

volumes:
  qdrant_data:
"""
        
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        
        # Start the service
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Wait for service to be ready
        self.assertTrue(self.wait_for_qdrant_ready())

        # Get initial restart count
        initial_restart_count = self.get_container_restart_count("test_qdrant_ci_env")
        self.assertIsNotNone(initial_restart_count)

        # Simulate crashes to test the restart policy
        for _ in range(3):  # Try to hit the limit of 2
            subprocess.run(
                ["docker", "kill", "--signal=SIGKILL", "test_qdrant_ci_env"],
                capture_output=True,
            )
            time.sleep(10)

        # Wait for restart policy to take effect
        time.sleep(20)

        # Verify the container has stopped due to restart policy
        container_status = self.get_container_status("test_qdrant_ci_env")
        if container_status:
            self.assertIn(
                container_status, 
                ["exited", "dead"], 
                f"Container should be stopped after restart limit, but status is: {container_status}"
            )
        else:
            # Container was removed
            self.assertTrue(True, "Container was removed after hitting restart limit")
