"""
Test suite for Qdrant Docker Compose configuration
Following TDD methodology for Task 99 - Configure Qdrant service (port 6333)
"""

import subprocess
import tempfile
import time
import unittest
from pathlib import Path

import requests  # type: ignore

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerCompose(QdrantDockerComposeTestBase):
    """Test cases for Qdrant service Docker Compose configuration"""

    def test_qdrant_service_starts_successfully(self):
        """Test: Qdrant Service Starts Successfully"""
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

            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "up", "qdrant", "-d"],
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

            try:
                assert result.returncode == 0, f"Docker compose failed: {result.stderr}"

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
                subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "down"],
                    capture_output=True,
                    cwd=temp_dir,
                )

    def test_qdrant_port_accessibility_and_health_check(self):
        """Test: Qdrant Exposes Port 6333 Correctly and Health Endpoint Returns Valid Response"""
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

            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "up", "qdrant", "-d"],
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

            try:
                assert result.returncode == 0, f"Docker compose failed: {result.stderr}"
                time.sleep(5)

                response = requests.get("http://localhost:6333/healthz", timeout=10)
                assert response.status_code == 200, (
                    f"Health check failed: {response.status_code}"
                )
                assert "healthz check passed" in response.text, (
                    f"Unexpected health response: {response.text}"
                )

            finally:
                subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "down"],
                    capture_output=True,
                    cwd=temp_dir,
                )

    def test_qdrant_storage_volume_persistence(self):
        """Test: Qdrant Storage Volume Mounts Correctly"""
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
                time.sleep(5)

                test_data = {"vectors": {"size": 4, "distance": "Cosine"}}
                create_response = requests.put(
                    "http://localhost:6333/collections/test_collection",
                    json=test_data,
                    timeout=10,
                )
                assert create_response.status_code in [200, 201], (
                    f"Failed to create collection: {create_response.status_code}"
                )

                subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "restart", "qdrant"],
                    capture_output=True,
                    cwd=temp_dir,
                )
                time.sleep(5)

                get_response = requests.get(
                    "http://localhost:6333/collections/test_collection", timeout=10
                )
                assert get_response.status_code == 200, (
                    f"Collection not found after restart: {get_response.status_code}"
                )

                collection_info = get_response.json()
                assert (
                    collection_info["result"]["config"]["params"]["vectors"]["size"]
                    == 4
                )

            finally:
                subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "down", "-v"],
                    capture_output=True,
                    cwd=temp_dir,
                )
