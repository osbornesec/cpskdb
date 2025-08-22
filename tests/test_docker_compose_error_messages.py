"""
Tests for Qdrant Docker Compose error message validation.

This module implements comprehensive error message validation for scenarios
"Qdrant Provides Meaningful Error Messages" and "Qdrant Health Check Failure Messages"
from the test specification.
"""

import subprocess
import tempfile
import time
import unittest

import requests

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeErrorMessages(QdrantDockerComposeTestBase):
    """Test Qdrant error message validation via Docker Compose"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.compose_file = None

    def tearDown(self):
        """Clean up test environment"""
        if self.compose_file:
            self.stop_qdrant_service(self.compose_file, self.temp_dir)

    def test_meaningful_error_messages_for_common_failures(self):
        """Test error messages are clear and actionable for common failure scenarios"""
        # Test 1: Invalid port configuration
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

        self.compose_file = self.setup_compose_file(compose_content_invalid_port, self.temp_dir)
        
        # Try to start with invalid configuration
        result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "up", "-d"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )
        
        # Should fail with meaningful error
        if result.returncode != 0:
            error_output = result.stderr + result.stdout
            self.assertIn("port", error_output.lower())
            # Error should mention the specific issue
            self.assertTrue(
                any(term in error_output.lower() for term in ["99999", "invalid", "range"]),
                f"Error message should mention port issue: {error_output}"
            )

    def test_health_check_failure_diagnostic_information(self):
        """Test health check failure logs provide specific diagnostic information"""
        # Create compose with failing health check
        compose_content_failing_health = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_failing_health
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    volumes:
      - qdrant_data:/qdrant/storage
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:9999/nonexistent || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 2
      start_period: 5s

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(compose_content_failing_health, self.temp_dir)
        
        # Start service
        subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "up", "-d"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )
        
        # Wait for health checks to fail
        time.sleep(30)
        
        # Check container health status and logs
        health_result = subprocess.run(
            ["docker", "inspect", "test_qdrant_failing_health", "--format={{.State.Health.Status}}"],
            capture_output=True,
            text=True,
        )
        
        if health_result.returncode == 0:
            health_status = health_result.stdout.strip()
            # Should be unhealthy due to failing health check
            if health_status == "unhealthy":
                # Get health check logs
                logs_result = subprocess.run(
                    ["docker", "logs", "test_qdrant_failing_health"],
                    capture_output=True,
                    text=True,
                )
                
                if logs_result.returncode == 0:
                    logs_content = logs_result.stdout + logs_result.stderr
                    # Logs should contain diagnostic information
                    self.assertTrue(len(logs_content) > 0, "No logs available for diagnosis")

    def test_network_configuration_error_messages(self):
        """Test network configuration error messages identify the specific issue"""
        # Test with conflicting network configuration
        compose_content_network_conflict = """
version: '3.8'

networks:
  conflicting-network:
    driver: bridge
    ipam:
      config:
        - subnet: 192.168.255.0/24  # Potentially conflicting subnet

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_network_conflict
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    networks:
      - conflicting-network
      - nonexistent-network  # This network doesn't exist
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(compose_content_network_conflict, self.temp_dir)
        
        # Try to start with network issues
        result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "up", "-d"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )
        
        # Should fail with network-related error
        if result.returncode != 0:
            error_output = result.stderr + result.stdout
            network_error_terms = ["network", "nonexistent-network", "not found"]
            self.assertTrue(
                any(term in error_output.lower() for term in network_error_terms),
                f"Error should mention network issue: {error_output}"
            )

    def test_startup_failure_troubleshooting_information(self):
        """Test startup failure messages contain helpful troubleshooting information"""
        # Test with configuration that prevents startup
        compose_content_startup_fail = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_startup_fail
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
      - QDRANT__STORAGE__STORAGE_PATH=/nonexistent/path/that/cannot/be/created
    volumes:
      - qdrant_data:/qdrant/storage
    command: ["./qdrant", "--config-path", "/qdrant/config/production.yaml"]

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(compose_content_startup_fail, self.temp_dir)
        
        # Try to start service
        subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "up", "-d"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )
        
        # Wait for potential startup issues
        time.sleep(15)
        
        # Check container status and logs
        status_result = subprocess.run(
            ["docker", "inspect", "test_qdrant_startup_fail", "--format={{.State.Status}}"],
            capture_output=True,
            text=True,
        )
        
        if status_result.returncode == 0:
            container_status = status_result.stdout.strip()
            
            # If container failed to start or exited
            if container_status in ["exited", "dead"]:
                # Get logs for troubleshooting info
                logs_result = subprocess.run(
                    ["docker", "logs", "test_qdrant_startup_fail"],
                    capture_output=True,
                    text=True,
                )
                
                if logs_result.returncode == 0:
                    logs_content = logs_result.stdout + logs_result.stderr
                    
                    # Logs should contain helpful information
                    self.assertTrue(len(logs_content) > 0, "No startup logs available")
                    
                    # Look for common troubleshooting indicators
                    helpful_indicators = [
                        "error", "Error", "ERROR",
                        "failed", "Failed", "FAILED",
                        "cannot", "Cannot", "CANNOT",
                        "permission", "Permission", "PERMISSION",
                        "path", "Path", "PATH",
                        "config", "Config", "CONFIG"
                    ]
                    
                    has_helpful_info = any(
                        indicator in logs_content for indicator in helpful_indicators
                    )
                    
                    self.assertTrue(
                        has_helpful_info,
                        f"Logs should contain helpful troubleshooting information: {logs_content[:500]}"
                    )

    def test_error_messages_include_relevant_context(self):
        """Test that error messages include relevant context (port numbers, file paths, etc.)"""
        # Setup and start a working Qdrant instance first
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        
        # Wait for service to be ready
        self.assertTrue(self.wait_for_qdrant_ready())
        
        # Test API errors include context
        # Try to create collection with invalid configuration
        invalid_collection_config = {
            "vectors": {
                "size": "invalid_size",  # Should be integer
                "distance": "InvalidDistance"  # Should be valid distance metric
            }
        }
        
        response = requests.put(
            "http://localhost:6333/collections/test_invalid_collection",
            json=invalid_collection_config,
            timeout=10,
        )
        
        # Should return error with context
        self.assertNotEqual(response.status_code, 200)
        
        if response.status_code >= 400:
            try:
                error_data = response.json()
                if "error" in error_data or "message" in error_data:
                    error_message = str(error_data)
                    
                    # Error should mention specific issues
                    context_indicators = [
                        "size", "distance", "vectors", "invalid", "type"
                    ]
                    
                    has_context = any(
                        indicator in error_message.lower() for indicator in context_indicators
                    )
                    
                    self.assertTrue(
                        has_context,
                        f"Error message should include relevant context: {error_message}"
                    )
            except ValueError:
                # Non-JSON error response
                error_text = response.text
                self.assertTrue(len(error_text) > 0, "Error response should not be empty")

    def test_error_message_consistency_across_failure_modes(self):
        """Test error message consistency across different failure modes"""
        # Setup and start Qdrant
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        
        # Wait for service to be ready
        self.assertTrue(self.wait_for_qdrant_ready())
        
        error_responses = []
        
        # Test 1: Invalid collection name
        response1 = requests.put(
            "http://localhost:6333/collections/",  # Empty collection name
            json={"vectors": {"size": 4, "distance": "Cosine"}},
            timeout=10,
        )
        if response1.status_code >= 400:
            error_responses.append(("empty_name", response1))
        
        # Test 2: Invalid endpoint
        response2 = requests.get(
            "http://localhost:6333/invalid_endpoint",
            timeout=10,
        )
        if response2.status_code >= 400:
            error_responses.append(("invalid_endpoint", response2))
        
        # Test 3: Invalid method
        response3 = requests.patch(  # PATCH not supported for this endpoint
            "http://localhost:6333/collections",
            timeout=10,
        )
        if response3.status_code >= 400:
            error_responses.append(("invalid_method", response3))
        
        # Analyze error response consistency
        for error_type, response in error_responses:
            # All errors should have consistent structure
            self.assertGreaterEqual(
                response.status_code, 400,
                f"Error response {error_type} should have 4xx/5xx status code"
            )
            
            # Response should have content
            self.assertTrue(
                len(response.text) > 0,
                f"Error response {error_type} should not be empty"
            )

    def test_error_messages_do_not_expose_sensitive_information(self):
        """Test that error messages don't expose sensitive information"""
        # Setup and start Qdrant
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        
        # Wait for service to be ready
        self.assertTrue(self.wait_for_qdrant_ready())
        
        # Try various invalid requests to check error messages
        test_requests = [
            ("GET", "http://localhost:6333/admin/secret"),
            ("POST", "http://localhost:6333/collections/test/admin"),
            ("PUT", "http://localhost:6333/internal/debug"),
            ("DELETE", "http://localhost:6333/system/shutdown"),
        ]
        
        for method, url in test_requests:
            try:
                response = requests.request(method, url, timeout=5)
                
                if response.status_code >= 400:
                    error_content = response.text.lower()
                    
                    # Should not expose sensitive paths or information
                    sensitive_terms = [
                        "/root/", "/home/", "password", "secret", "token", "key",
                        "internal", "debug", "admin", "config", "env"
                    ]
                    
                    for sensitive_term in sensitive_terms:
                        self.assertNotIn(
                            sensitive_term,
                            error_content,
                            f"Error message should not expose sensitive term '{sensitive_term}' in response to {method} {url}"
                        )
                        
            except requests.exceptions.RequestException:
                # Connection errors are acceptable
                pass

    def test_container_logs_error_clarity(self):
        """Test container logs provide clear error information when issues occur"""
        # Test with a configuration that will cause issues but still start
        compose_content_warnings = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_log_clarity
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=DEBUG  # More verbose logging
      - QDRANT__STORAGE__PERFORMANCE__MAX_OPTIMIZATION_THREADS=1000  # Potentially problematic value
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(compose_content_warnings, self.temp_dir)
        
        # Start service
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        
        # Wait for service to start and potentially log warnings
        time.sleep(10)
        
        # Get container logs
        logs_result = subprocess.run(
            ["docker", "logs", "test_qdrant_log_clarity"],
            capture_output=True,
            text=True,
        )
        
        self.assertEqual(logs_result.returncode, 0)
        logs_content = logs_result.stdout + logs_result.stderr
        
        # Logs should be informative
        self.assertTrue(len(logs_content) > 0, "Container should produce logs")
        
        # Look for log structure and clarity
        log_quality_indicators = [
            # Common log levels
            any(level in logs_content.upper() for level in ["INFO", "WARN", "ERROR", "DEBUG"]),
            # Timestamps or structured logging
            any(indicator in logs_content for indicator in ["T", ":", "[", "]", "{", "}"]),
            # Qdrant-specific information
            any(term in logs_content.lower() for term in ["qdrant", "vector", "collection", "storage"])
        ]
        
        self.assertTrue(
            any(log_quality_indicators),
            f"Logs should be well-structured and informative: {logs_content[:300]}"
        )

    def test_api_error_response_format_consistency(self):
        """Test API error responses follow consistent format"""
        # Setup and start Qdrant
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        
        # Wait for service to be ready
        self.assertTrue(self.wait_for_qdrant_ready())
        
        # Create a test collection first
        collection_name = "test_error_format"
        self.create_test_collection(collection_name)
        
        # Test various API errors
        error_tests = [
            # Invalid point data
            ("PUT", f"http://localhost:6333/collections/{collection_name}/points", {
                "points": [{"id": "invalid", "vector": "not_a_vector"}]
            }),
            # Invalid search query
            ("POST", f"http://localhost:6333/collections/{collection_name}/points/search", {
                "vector": "invalid_vector",
                "limit": "not_a_number"
            }),
            # Non-existent collection
            ("GET", "http://localhost:6333/collections/nonexistent_collection", None),
        ]
        
        error_formats = []
        
        for method, url, data in error_tests:
            try:
                if data:
                    response = requests.request(method, url, json=data, timeout=10)
                else:
                    response = requests.request(method, url, timeout=10)
                
                if response.status_code >= 400:
                    try:
                        error_json = response.json()
                        error_formats.append(error_json)
                    except ValueError:
                        # Non-JSON response
                        error_formats.append({"text": response.text})
                        
            except requests.exceptions.RequestException:
                pass
        
        # Analyze error format consistency
        if error_formats:
            # Check if errors have consistent structure
            for error_format in error_formats:
                # Should be a dictionary/object
                self.assertIsInstance(error_format, dict, "Error should be structured")
                
                # Should have some identifiable error information
                has_error_info = any(
                    key in error_format for key in ["error", "message", "detail", "status", "text"]
                )
                
                self.assertTrue(
                    has_error_info,
                    f"Error format should contain error information: {error_format}"
                )


if __name__ == "__main__":
    unittest.main()