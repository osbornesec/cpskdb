"""
Advanced edge cases and boundary condition tests for Qdrant Docker Compose
"""

import subprocess
import tempfile
import time
from pathlib import Path

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeAdvancedEdgeCases(QdrantDockerComposeTestBase):
    """Advanced edge cases and boundary condition tests"""

    def test_qdrant_volume_permission_errors(self):
        """Test: Qdrant Volume Mount Permission Errors"""
        with tempfile.TemporaryDirectory() as temp_dir:
            restricted_dir = Path(temp_dir) / "restricted_storage"
            restricted_dir.mkdir()
            restricted_dir.chmod(0o444)

            compose_content = f"""
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_permissions
    ports:
      - "6333:6333"
    volumes:
      - {restricted_dir}:/qdrant/storage
"""

            compose_file = self.setup_compose_file(compose_content, temp_dir)

            try:
                result = self.start_qdrant_service(compose_file, temp_dir)

                if result.returncode == 0:
                    time.sleep(5)
                    logs_result = subprocess.run(
                        ["docker", "logs", "test_qdrant_permissions"],
                        capture_output=True,
                        text=True,
                    )

                    logs_text = logs_result.stdout.lower() + logs_result.stderr.lower()
                    permission_indicators = [
                        "permission",
                        "denied",
                        "access",
                        "cannot write",
                        "read-only",
                    ]
                    self.assertTrue(
                        any(
                            indicator in logs_text
                            for indicator in permission_indicators
                        ),
                        f"Expected permission errors in logs: {logs_text[:500]}",
                    )

            finally:
                try:
                    restricted_dir.chmod(0o755)
                except Exception:
                    pass
                self.stop_qdrant_service(compose_file, temp_dir)

    def test_qdrant_invalid_environment_variable_values(self):
        """Test: Qdrant Invalid Environment Variable Values"""
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_invalid_env
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INVALID_LEVEL_12345
      - QDRANT__SERVICE__HTTP_PORT=invalid_port
    volumes:
      - qdrant_data:/qdrant/storage
volumes:
  qdrant_data:
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = self.setup_compose_file(compose_content, temp_dir)

            try:
                result = self.start_qdrant_service(compose_file, temp_dir)

                if result.returncode == 0:
                    time.sleep(5)
                    logs_result = subprocess.run(
                        ["docker", "logs", "test_qdrant_invalid_env"],
                        capture_output=True,
                        text=True,
                    )

                    logs_text = logs_result.stdout.lower() + logs_result.stderr.lower()

                    try:
                        import requests

                        response = requests.get(
                            "http://localhost:6333/healthz", timeout=5
                        )
                        if response.status_code != 200:
                            config_error_indicators = [
                                "invalid",
                                "error",
                                "config",
                                "parse",
                            ]
                            self.assertTrue(
                                any(
                                    indicator in logs_text
                                    for indicator in config_error_indicators
                                ),
                                f"Expected config error handling in logs: {logs_text[:500]}",
                            )
                    except requests.exceptions.RequestException as e:
                        # All HTTP-related errors including timeouts
                        self.fail(
                            f"HTTP request to http://localhost:6333/healthz failed: {e}"
                        )
                    except Exception:
                        config_error_indicators = [
                            "invalid",
                            "error",
                            "config",
                            "parse",
                            "failed",
                        ]
                        self.assertTrue(
                            any(
                                indicator in logs_text
                                for indicator in config_error_indicators
                            ),
                            f"Expected config error messages: {logs_text[:500]}",
                        )

            finally:
                self.stop_qdrant_service(compose_file, temp_dir)

    def test_qdrant_recovery_from_temporary_storage_issues(self):
        """Test: Qdrant Recovers from Temporary Storage Issues"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_dir = Path(temp_dir) / "qdrant_storage"
            storage_dir.mkdir()

            compose_content = f"""
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_storage_recovery
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    volumes:
      - {storage_dir}:/qdrant/storage
    restart: unless-stopped
"""

            compose_file = self.setup_compose_file(compose_content, temp_dir)

            try:
                result = self.start_qdrant_service(compose_file, temp_dir)
                self.assertEqual(
                    result.returncode, 0, f"Docker compose failed: {result.stderr}"
                )

                self.assertTrue(
                    self.wait_for_qdrant_ready(), "Qdrant service not ready"
                )
                self.create_test_collection("recovery_test")

                original_perms = storage_dir.stat().st_mode
                storage_dir.chmod(0o444)

                # Wait for container to detect permission change
                start_time = time.monotonic()
                timeout = 10
                while time.monotonic() - start_time < timeout:
                    # Check if container can detect the permission issue
                    logs_result = subprocess.run(
                        [
                            "docker",
                            "logs",
                            "--tail",
                            "20",
                            "test_qdrant_storage_recovery",
                        ],
                        capture_output=True,
                        text=True,
                        cwd=temp_dir,
                    )
                    if (
                        "permission" in logs_result.stdout.lower()
                        or "access" in logs_result.stdout.lower()
                    ):
                        break
                    time.sleep(0.5)

                storage_dir.chmod(original_perms)

                # Wait for container to recover
                start_time = time.monotonic()
                while time.monotonic() - start_time < timeout:
                    try:
                        if self.wait_for_qdrant_ready():
                            break
                    except Exception:
                        pass
                    time.sleep(0.5)

                self.assert_qdrant_healthy()
                self.verify_collection_exists("recovery_test")

            finally:
                try:
                    storage_dir.chmod(0o755)
                except Exception:
                    pass
                self.stop_qdrant_service(compose_file, temp_dir)
