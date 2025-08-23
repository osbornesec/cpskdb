"""
Environment variable validation tests for Qdrant Docker Compose
"""

import subprocess
import tempfile
import time

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeEnvironmentValidation(QdrantDockerComposeTestBase):
    """Environment variable validation edge case tests"""

    def test_qdrant_invalid_environment_variable_values(self) -> None:
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
                        import requests  # type: ignore[import-untyped]

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
