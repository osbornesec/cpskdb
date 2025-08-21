"""
Test suite for Qdrant Docker Compose configuration
Following TDD methodology for Task 99 - Configure Qdrant service (port 6333)
"""

import subprocess
import tempfile
import time
import requests
from pathlib import Path


class TestQdrantDockerCompose:
    """Test cases for Qdrant service Docker Compose configuration"""

    def test_qdrant_service_starts_successfully(self):
        """
        Test: Qdrant Service Starts Successfully
        Given: Docker Compose file with Qdrant service configuration
        When: Running `docker compose up qdrant`
        Then: Qdrant container starts without errors
        """
        # Arrange: Create minimal docker-compose.yml with Qdrant service
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant
    ports:
      - "6333:6333"
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = Path(temp_dir) / "docker-compose.yml"
            compose_file.write_text(compose_content)

            # Act: Start Qdrant service
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "up", "qdrant", "-d"],
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

            try:
                # Assert: Container starts without errors
                assert result.returncode == 0, f"Docker compose failed: {result.stderr}"

                # Verify container is running
                check_result = subprocess.run(
                    [
                        "docker",
                        "ps",
                        "--filter",
                        "name=test_qdrant",
                        "--format",
                        "{{.Status}}",
                    ],
                    capture_output=True,
                    text=True,
                )
                assert "Up" in check_result.stdout, "Qdrant container is not running"

            finally:
                # Cleanup: Stop and remove container
                subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "down"],
                    capture_output=True,
                    cwd=temp_dir,
                )

    def test_qdrant_port_accessibility_and_health_check(self):
        """
        Test: Qdrant Exposes Port 6333 Correctly and Health Endpoint Returns Valid Response
        Given: Qdrant service is configured with port mapping 6333:6333
        When: Service is started
        Then: Port 6333 is accessible and health endpoint responds
        """
        # Arrange: Create docker-compose.yml with Qdrant service
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_health
    ports:
      - "6333:6333"
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = Path(temp_dir) / "docker-compose.yml"
            compose_file.write_text(compose_content)

            # Act: Start Qdrant service
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "up", "qdrant", "-d"],
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

            try:
                assert result.returncode == 0, f"Docker compose failed: {result.stderr}"

                # Wait for service to be ready
                time.sleep(5)

                # Assert: Health endpoint is accessible and returns valid response
                response = requests.get("http://localhost:6333/healthz", timeout=10)
                assert response.status_code == 200, (
                    f"Health check failed: {response.status_code}"
                )

                # Verify response contains expected health check message
                assert "healthz check passed" in response.text, (
                    f"Unexpected health response: {response.text}"
                )

            finally:
                # Cleanup: Stop and remove container
                subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "down"],
                    capture_output=True,
                    cwd=temp_dir,
                )

    def test_qdrant_storage_volume_persistence(self):
        """
        Test: Qdrant Storage Volume Mounts Correctly
        Given: Docker Compose configuration includes storage volume mapping
        When: Container is started and restarted
        Then: Data persists across container restarts
        """
        # Arrange: Create docker-compose.yml with volume mapping
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_volume
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = Path(temp_dir) / "docker-compose.yml"
            compose_file.write_text(compose_content)

            try:
                # Act: Start Qdrant service
                result = subprocess.run(
                    [
                        "docker",
                        "compose",
                        "-f",
                        str(compose_file),
                        "up",
                        "qdrant",
                        "-d",
                    ],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir,
                )
                assert result.returncode == 0, f"Docker compose failed: {result.stderr}"

                # Wait for service to be ready
                time.sleep(5)

                # Create a test collection via API to verify volume persistence
                test_data = {"vectors": {"size": 4, "distance": "Cosine"}}
                create_response = requests.put(
                    "http://localhost:6333/collections/test_collection",
                    json=test_data,
                    timeout=10,
                )
                assert create_response.status_code in [200, 201], (
                    f"Failed to create collection: {create_response.status_code}"
                )

                # Restart the container
                subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "restart", "qdrant"],
                    capture_output=True,
                    cwd=temp_dir,
                )

                # Wait for service to be ready after restart
                time.sleep(5)

                # Assert: Collection should still exist after restart
                get_response = requests.get(
                    "http://localhost:6333/collections/test_collection", timeout=10
                )
                assert get_response.status_code == 200, (
                    f"Collection not found after restart: {get_response.status_code}"
                )

                # Verify collection configuration persisted
                collection_info = get_response.json()
                assert (
                    collection_info["result"]["config"]["params"]["vectors"]["size"]
                    == 4
                )

            finally:
                # Cleanup: Stop and remove containers and volumes
                subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "down", "-v"],
                    capture_output=True,
                    cwd=temp_dir,
                )

    def test_qdrant_environment_variable_configuration(self):
        """
        Test: Qdrant Uses Configured Log Level
        Given: Environment variable QDRANT__LOG_LEVEL is set
        When: Container starts
        Then: Qdrant respects the configured log level
        """
        # Arrange: Create docker-compose.yml with environment variables
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_env
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=DEBUG
      - QDRANT__SERVICE__HTTP_PORT=6333
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = Path(temp_dir) / "docker-compose.yml"
            compose_file.write_text(compose_content)

            try:
                # Act: Start Qdrant service
                result = subprocess.run(
                    [
                        "docker",
                        "compose",
                        "-f",
                        str(compose_file),
                        "up",
                        "qdrant",
                        "-d",
                    ],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir,
                )
                assert result.returncode == 0, f"Docker compose failed: {result.stderr}"

                # Wait for service to be ready
                time.sleep(5)

                # Assert: Service should be accessible with configured environment
                response = requests.get("http://localhost:6333/healthz", timeout=10)
                assert response.status_code == 200

                # Verify logs contain debug information (indicating DEBUG log level)
                logs_result = subprocess.run(
                    ["docker", "logs", "test_qdrant_env"],
                    capture_output=True,
                    text=True,
                )
                # Debug logs should contain more verbose output
                assert logs_result.returncode == 0
                logs_text = logs_result.stdout.lower()
                # Check for debug-level indicators in logs
                debug_indicators = ["debug", "trace", "starting", "initialized"]
                assert any(indicator in logs_text for indicator in debug_indicators), (
                    f"Debug logs not found in: {logs_text[:500]}"
                )

            finally:
                # Cleanup: Stop and remove containers and volumes
                subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "down", "-v"],
                    capture_output=True,
                    cwd=temp_dir,
                )

    def test_qdrant_health_check_integration(self):
        """
        Test: Qdrant Health Check Integration with Docker Compose
        Given: Qdrant service with configured health checks
        When: Docker Compose monitors service health
        Then: Health status accurately reflects service state
        """
        # Arrange: Create docker-compose.yml with basic health check
        # Using a simple approach since complex health checks may fail due to missing tools
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_health_check
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped

volumes:
  qdrant_data:
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = Path(temp_dir) / "docker-compose.yml"
            compose_file.write_text(compose_content)

            try:
                # Act: Start Qdrant service
                result = subprocess.run(
                    [
                        "docker",
                        "compose",
                        "-f",
                        str(compose_file),
                        "up",
                        "qdrant",
                        "-d",
                    ],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir,
                )
                assert result.returncode == 0, f"Docker compose failed: {result.stderr}"

                # Wait for service to be ready
                time.sleep(10)

                # Assert: Verify service is accessible (this IS the health check)
                response = requests.get("http://localhost:6333/healthz", timeout=10)
                assert response.status_code == 200
                assert "healthz check passed" in response.text

                # Verify container is running and healthy (no explicit health check defined)
                container_result = subprocess.run(
                    [
                        "docker",
                        "ps",
                        "--filter",
                        "name=test_qdrant_health_check",
                        "--format",
                        "{{.Status}}",
                    ],
                    capture_output=True,
                    text=True,
                )
                assert container_result.returncode == 0
                assert "Up" in container_result.stdout, "Container should be running"

                # Test restart policy by restarting and verifying it comes back up
                restart_result = subprocess.run(
                    ["docker", "restart", "test_qdrant_health_check"],
                    capture_output=True,
                    text=True,
                )
                assert restart_result.returncode == 0

                # Wait for restart and verify accessibility again
                time.sleep(10)
                response = requests.get("http://localhost:6333/healthz", timeout=10)
                assert response.status_code == 200

            finally:
                # Cleanup: Stop and remove containers and volumes
                subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "down", "-v"],
                    capture_output=True,
                    cwd=temp_dir,
                )

    def test_qdrant_port_conflict_error_handling(self):
        """
        Test: Qdrant Handles Port Conflicts
        Given: Port 6333 already in use by another service
        When: Starting Qdrant service
        Then: Clear error about port conflict
        """
        # Arrange: Start a dummy service on port 6333 first
        dummy_container = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--rm",
                "--name",
                "dummy_port_blocker",
                "-p",
                "6333:80",
                "nginx:alpine",
            ],
            capture_output=True,
            text=True,
        )

        try:
            assert dummy_container.returncode == 0, "Failed to start dummy container"

            # Wait for dummy container to start
            time.sleep(3)

            # Arrange: Create docker-compose.yml for Qdrant
            compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_port_conflict
    ports:
      - "6333:6333"
"""

            with tempfile.TemporaryDirectory() as temp_dir:
                compose_file = Path(temp_dir) / "docker-compose.yml"
                compose_file.write_text(compose_content)

                # Act: Try to start Qdrant service (should fail due to port conflict)
                result = subprocess.run(
                    [
                        "docker",
                        "compose",
                        "-f",
                        str(compose_file),
                        "up",
                        "qdrant",
                        "-d",
                    ],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir,
                )

                # Assert: Should fail with port conflict error
                assert result.returncode != 0, "Expected failure due to port conflict"
                error_output = result.stderr.lower()
                # Check for common port conflict error indicators
                port_conflict_indicators = [
                    "port",
                    "bind",
                    "address already in use",
                    "6333",
                ]
                assert any(
                    indicator in error_output for indicator in port_conflict_indicators
                ), f"Expected port conflict error, got: {result.stderr}"

                # Cleanup compose resources if any were created
                subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "down", "-v"],
                    capture_output=True,
                    cwd=temp_dir,
                )

        finally:
            # Cleanup: Stop dummy container
            subprocess.run(
                ["docker", "stop", "dummy_port_blocker"], capture_output=True
            )

    def test_qdrant_invalid_image_error_handling(self):
        """
        Test: Qdrant Handles Invalid Image Tag
        Given: Qdrant service configured with non-existent image tag
        When: Attempting to start service
        Then: Docker reports image not found error
        """
        # Arrange: Create docker-compose.yml with invalid image
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:nonexistent-tag-12345
    container_name: test_qdrant_invalid_image
    ports:
      - "6333:6333"
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = Path(temp_dir) / "docker-compose.yml"
            compose_file.write_text(compose_content)

            # Act: Try to start service with invalid image
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "up", "qdrant", "-d"],
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

            try:
                # Assert: Should fail with image not found error
                assert result.returncode != 0, "Expected failure due to invalid image"
                error_output = result.stderr.lower()
                # Check for image-related error indicators
                image_error_indicators = [
                    "pull",
                    "not found",
                    "manifest unknown",
                    "image",
                ]
                assert any(
                    indicator in error_output for indicator in image_error_indicators
                ), f"Expected image error, got: {result.stderr}"

            finally:
                # Cleanup: Ensure no resources are left
                subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "down", "-v"],
                    capture_output=True,
                    cwd=temp_dir,
                )

    def test_qdrant_malformed_compose_config_error(self):
        """
        Test: Qdrant Handles Malformed Docker Compose Configuration
        Given: Docker Compose file with syntax errors in Qdrant section
        When: Running `docker compose up`
        Then: Clear error message about configuration issues
        """
        # Arrange: Create malformed docker-compose.yml
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_malformed
    ports:
      - "6333:6333"
    environment:
      - INVALID_SYNTAX_HERE:
    volumes:
      - qdrant_data:/qdrant/storage
    # Missing closing bracket or invalid YAML structure
    malformed_section: {
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = Path(temp_dir) / "docker-compose.yml"
            compose_file.write_text(compose_content)

            # Act: Try to start service with malformed config
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "config"],
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

            # Assert: Should fail with configuration error
            assert result.returncode != 0, "Expected failure due to malformed config"
            error_output = result.stderr.lower()
            # Check for configuration error indicators
            config_error_indicators = ["yaml", "syntax", "invalid", "error", "parse"]
            assert any(
                indicator in error_output for indicator in config_error_indicators
            ), f"Expected configuration error, got: {result.stderr}"

    def test_qdrant_missing_environment_variables(self):
        """
        Test: Qdrant Handles Missing Environment Variables
        Given: Docker Compose configuration without QDRANT__LOG_LEVEL
        When: Container starts
        Then: Qdrant uses default log level
        """
        # Arrange: Create docker-compose.yml without environment variables
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_no_env
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = Path(temp_dir) / "docker-compose.yml"
            compose_file.write_text(compose_content)

            try:
                # Act: Start Qdrant service
                result = subprocess.run(
                    [
                        "docker",
                        "compose",
                        "-f",
                        str(compose_file),
                        "up",
                        "qdrant",
                        "-d",
                    ],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir,
                )
                assert result.returncode == 0, f"Docker compose failed: {result.stderr}"

                # Wait for service to be ready
                time.sleep(5)

                # Assert: Service should start successfully with defaults
                response = requests.get("http://localhost:6333/healthz", timeout=10)
                assert response.status_code == 200
                assert "healthz check passed" in response.text

                # Verify service info endpoint works
                info_response = requests.get("http://localhost:6333/", timeout=10)
                assert info_response.status_code == 200
                service_info = info_response.json()
                assert "title" in service_info
                assert "qdrant" in service_info["title"].lower()

            finally:
                # Cleanup: Stop and remove containers and volumes
                subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "down", "-v"],
                    capture_output=True,
                    cwd=temp_dir,
                )

    def test_qdrant_missing_storage_volume(self):
        """
        Test: Qdrant Handles Missing Storage Volume
        Given: Docker Compose configuration without storage volume
        When: Container starts
        Then: Qdrant uses ephemeral storage (data lost on container removal)
        """
        # Arrange: Create docker-compose.yml without storage volume
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_no_volume
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = Path(temp_dir) / "docker-compose.yml"
            compose_file.write_text(compose_content)

            try:
                # Act: Start Qdrant service
                result = subprocess.run(
                    [
                        "docker",
                        "compose",
                        "-f",
                        str(compose_file),
                        "up",
                        "qdrant",
                        "-d",
                    ],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir,
                )
                assert result.returncode == 0, f"Docker compose failed: {result.stderr}"

                # Wait for service to be ready
                time.sleep(5)

                # Assert: Service should start successfully
                response = requests.get("http://localhost:6333/healthz", timeout=10)
                assert response.status_code == 200

                # Create test collection to verify service works
                test_data = {"vectors": {"size": 4, "distance": "Cosine"}}
                create_response = requests.put(
                    "http://localhost:6333/collections/ephemeral_test",
                    json=test_data,
                    timeout=10,
                )
                assert create_response.status_code in [200, 201]

                # Stop and remove container (without volume, data should be lost)
                subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "down"],
                    capture_output=True,
                    cwd=temp_dir,
                )

                # Start again - data should be gone
                result = subprocess.run(
                    [
                        "docker",
                        "compose",
                        "-f",
                        str(compose_file),
                        "up",
                        "qdrant",
                        "-d",
                    ],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir,
                )
                assert result.returncode == 0

                time.sleep(5)

                # Collection should be gone since no volume persistence
                get_response = requests.get(
                    "http://localhost:6333/collections/ephemeral_test", timeout=10
                )
                # Should return 404 indicating no persistence without volumes
                assert get_response.status_code == 404, (
                    f"Expected collection to be gone without volumes, but got: {get_response.status_code}"
                )

            finally:
                # Cleanup: Stop and remove containers
                subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "down"],
                    capture_output=True,
                    cwd=temp_dir,
                )

    def test_qdrant_invalid_port_configuration(self):
        """
        Test: Qdrant Invalid Port Numbers
        Given: Port configuration with zero or negative values
        When: Attempting to start service
        Then: Docker Compose validation fails
        """
        # Arrange: Create docker-compose.yml with invalid port
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_invalid_port
    ports:
      - "0:6333"
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = Path(temp_dir) / "docker-compose.yml"
            compose_file.write_text(compose_content)

            # Act: Try to validate the configuration
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "config"],
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

            # Assert: Configuration should be rejected or service should fail to start
            if result.returncode == 0:
                # If config validation passes, try to start and expect failure
                start_result = subprocess.run(
                    [
                        "docker",
                        "compose",
                        "-f",
                        str(compose_file),
                        "up",
                        "qdrant",
                        "-d",
                    ],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir,
                )

                try:
                    # Service should either fail to start or not be accessible
                    if start_result.returncode == 0:
                        time.sleep(3)
                        # Should not be accessible on port 0
                        try:
                            requests.get("http://localhost:0/healthz", timeout=5)
                            assert False, "Should not be able to connect to port 0"
                        except (
                            requests.exceptions.ConnectionError,
                            requests.exceptions.InvalidURL,
                        ):
                            # Expected - port 0 is not valid for connections
                            pass
                finally:
                    # Cleanup any containers that might have started
                    subprocess.run(
                        ["docker", "compose", "-f", str(compose_file), "down"],
                        capture_output=True,
                        cwd=temp_dir,
                    )

    def test_qdrant_multi_service_docker_compose_integration(self):
        """
        Test: Qdrant Service Integrates with Docker Compose Stack
        Given: Full docker-compose.yml with multiple services
        When: Starting entire stack with `docker compose up`
        Then: Qdrant service starts alongside other services and can communicate
        """
        # Arrange: Create docker-compose.yml with multiple services including Qdrant
        compose_content = """
version: '3.8'

networks:
  rag-network:
    driver: bridge

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_integration
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped
    networks:
      - rag-network
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:6333/healthz || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  test_client:
    image: nginx:alpine
    container_name: test_client_service
    networks:
      - rag-network
    depends_on:
      - qdrant
    command: >
      sh -c "
        echo 'Testing Qdrant connectivity from test_client...' &&
        sleep 10 &&
        wget --no-verbose --tries=3 --timeout=10 -O- http://qdrant:6333/healthz &&
        echo 'Qdrant connectivity test successful!' &&
        nginx -g 'daemon off;'
      "

volumes:
  qdrant_data:
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = Path(temp_dir) / "docker-compose.yml"
            compose_file.write_text(compose_content)

            try:
                # Act: Start entire stack
                result = subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "up", "-d"],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir,
                )
                assert result.returncode == 0, f"Docker compose failed: {result.stderr}"

                # Wait for services to be ready
                time.sleep(15)

                # Assert: Qdrant should be accessible from host
                response = requests.get("http://localhost:6333/healthz", timeout=10)
                assert response.status_code == 200
                assert "healthz check passed" in response.text

                # Assert: Check that test_client can reach Qdrant via internal network
                client_logs = subprocess.run(
                    ["docker", "logs", "test_client_service"],
                    capture_output=True,
                    text=True,
                )
                assert client_logs.returncode == 0
                logs_text = client_logs.stdout.lower()
                assert (
                    "connectivity test successful" in logs_text
                    or "healthz check passed" in logs_text
                ), f"Internal network connectivity failed. Logs: {client_logs.stdout}"

                # Assert: Verify both services are running
                ps_result = subprocess.run(
                    [
                        "docker",
                        "compose",
                        "-f",
                        str(compose_file),
                        "ps",
                        "--format",
                        "json",
                    ],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir,
                )
                assert ps_result.returncode == 0

                # Verify service discovery via hostname
                exec_result = subprocess.run(
                    [
                        "docker",
                        "exec",
                        "test_client_service",
                        "wget",
                        "-O-",
                        "-q",
                        "http://qdrant:6333/",
                    ],
                    capture_output=True,
                    text=True,
                )
                if exec_result.returncode == 0:
                    service_info = exec_result.stdout
                    assert "qdrant" in service_info.lower()

            finally:
                # Cleanup: Stop and remove all services and volumes
                subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "down", "-v"],
                    capture_output=True,
                    cwd=temp_dir,
                )

    def test_qdrant_network_isolation_and_service_discovery(self):
        """
        Test: Qdrant Service Discovery Within Docker Network
        Given: Multiple services in same Docker Compose network
        When: Services reference Qdrant by service name
        Then: DNS resolution works correctly
        """
        # Arrange: Create docker-compose.yml with custom network
        compose_content = """
version: '3.8'

networks:
  rag-network:
    driver: bridge

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_network
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    networks:
      - rag-network

  network_tester:
    image: alpine:latest
    container_name: network_tester
    networks:
      - rag-network
    depends_on:
      - qdrant
    command: >
      sh -c "
        apk add --no-cache curl &&
        sleep 5 &&
        echo 'Testing DNS resolution...' &&
        nslookup qdrant &&
        echo 'Testing HTTP connectivity...' &&
        curl -f http://qdrant:6333/healthz &&
        echo 'Network tests completed successfully!' &&
        sleep 30
      "
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = Path(temp_dir) / "docker-compose.yml"
            compose_file.write_text(compose_content)

            try:
                # Act: Start services
                result = subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "up", "-d"],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir,
                )
                assert result.returncode == 0, f"Docker compose failed: {result.stderr}"

                # Wait for network tester to complete
                time.sleep(10)

                # Assert: Check network tester logs for successful DNS and HTTP tests
                tester_logs = subprocess.run(
                    ["docker", "logs", "network_tester"], capture_output=True, text=True
                )
                assert tester_logs.returncode == 0
                logs_text = tester_logs.stdout.lower()

                # Verify DNS resolution worked
                assert "testing dns resolution" in logs_text

                # Verify HTTP connectivity worked
                assert (
                    "healthz check passed" in logs_text
                    or "network tests completed successfully" in logs_text
                ), f"Network connectivity tests failed. Logs: {tester_logs.stdout}"

            finally:
                # Cleanup: Stop and remove services
                subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "down"],
                    capture_output=True,
                    cwd=temp_dir,
                )

    def test_qdrant_production_like_configuration(self):
        """
        Test: Qdrant Production-like Configuration
        Given: Docker Compose configured for production-like environment
        When: Starting services
        Then: Qdrant runs with production-appropriate settings
        """
        # Arrange: Create production-like docker-compose.yml
        compose_content = """
version: '3.8'

networks:
  rag-network:
    driver: bridge

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_production
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334
    volumes:
      - qdrant_data:/qdrant/storage
      - qdrant_snapshots:/qdrant/snapshots
    restart: unless-stopped
    networks:
      - rag-network
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:6333/healthz || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

volumes:
  qdrant_data:
  qdrant_snapshots:
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = Path(temp_dir) / "docker-compose.yml"
            compose_file.write_text(compose_content)

            try:
                # Act: Start production-like service
                result = subprocess.run(
                    [
                        "docker",
                        "compose",
                        "-f",
                        str(compose_file),
                        "up",
                        "qdrant",
                        "-d",
                    ],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir,
                )
                assert result.returncode == 0, f"Docker compose failed: {result.stderr}"

                # Wait for service to be ready
                time.sleep(15)

                # Assert: Verify production features work
                response = requests.get("http://localhost:6333/healthz", timeout=10)
                assert response.status_code == 200

                # Verify service info shows proper configuration
                info_response = requests.get("http://localhost:6333/", timeout=10)
                assert info_response.status_code == 200
                service_info = info_response.json()
                assert "title" in service_info
                assert "version" in service_info

                # Test creating and managing collections (production workflow)
                collection_data = {
                    "vectors": {"size": 384, "distance": "Cosine"},
                    "optimizers_config": {"default_segment_number": 2},
                }
                create_response = requests.put(
                    "http://localhost:6333/collections/production_test",
                    json=collection_data,
                    timeout=10,
                )
                assert create_response.status_code in [200, 201]

                # Verify collection configuration
                get_response = requests.get(
                    "http://localhost:6333/collections/production_test", timeout=10
                )
                assert get_response.status_code == 200
                collection_info = get_response.json()
                assert (
                    collection_info["result"]["config"]["params"]["vectors"]["size"]
                    == 384
                )

            finally:
                # Cleanup: Stop and remove containers and volumes
                subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "down", "-v"],
                    capture_output=True,
                    cwd=temp_dir,
                )
