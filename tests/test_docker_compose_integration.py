"""Integration and interaction tests for Qdrant Docker Compose configuration."""

import subprocess
import tempfile
import time

import requests

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeIntegration(QdrantDockerComposeTestBase):
    """Integration and interaction tests for Qdrant Docker Compose configuration."""

    def test_qdrant_multi_service_docker_compose_integration(self):
        """Test: Qdrant Service Integrates with Docker Compose Stack."""
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_integration
    ports:
      - "6333:6333"
  test_client:
    image: alpine:latest
    container_name: test_client_service
    command: sh -c "apk add --no-cache curl && sleep 5 && curl -f http://qdrant:6333/healthz && echo 'Connectivity test successful' || echo 'Connectivity test failed'"
    depends_on:
      - qdrant
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = self.setup_compose_file(compose_content, temp_dir)
            try:
                result = subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "up", "-d"],
                    check=False,
                    capture_output=True,
                    text=True,
                    cwd=temp_dir,
                )
                assert result.returncode == 0, f"Docker compose failed: {result.stderr}"

                time.sleep(15)
                assert self.wait_for_qdrant_ready(), "Qdrant not accessible from host"
                self.assert_qdrant_healthy()

                client_logs = subprocess.run(
                    ["docker", "logs", "test_client_service"],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                assert client_logs.returncode == 0
                logs_text = client_logs.stdout
                assert "Connectivity test successful" in logs_text or "healthz check passed" in logs_text.lower(), f"Internal network connectivity failed. Logs: {client_logs.stdout}"
            finally:
                self.stop_qdrant_service(compose_file, temp_dir)

    def test_qdrant_network_isolation_and_service_discovery(self):
        """Test: Qdrant Service Discovery Within Docker Network."""
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
            compose_file = self.setup_compose_file(compose_content, temp_dir)

            try:
                result = subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "up", "-d"],
                    check=False,
                    capture_output=True,
                    text=True,
                    cwd=temp_dir,
                )
                assert result.returncode == 0, f"Docker compose failed: {result.stderr}"

                time.sleep(10)
                tester_logs = subprocess.run(
                    ["docker", "logs", "network_tester"],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                assert tester_logs.returncode == 0
                logs_text = tester_logs.stdout.lower()

                assert "testing dns resolution" in logs_text, f"Expected 'testing dns resolution' in tester logs but it was not found. Logs: {tester_logs.stdout[:1000]!r}"
                assert "healthz check passed" in logs_text, f"Expected 'healthz check passed' in tester logs but it was not found. Logs: {tester_logs.stdout[:1000]!r}"
                assert "network tests completed successfully" in logs_text, f"Expected 'network tests completed successfully' in tester logs but it was not found. Logs: {tester_logs.stdout[:1000]!r}"

            finally:
                self.stop_qdrant_service(compose_file, temp_dir)

    def test_qdrant_production_like_configuration(self):
        """Test: Qdrant Production-like Configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = self.setup_compose_file(
                self.create_production_compose_content(), temp_dir
            )

            try:
                result = self.start_qdrant_service(compose_file, temp_dir)
                assert result.returncode == 0, f"Docker compose failed: {result.stderr}"

                assert self.wait_for_qdrant_ready(30), "Production service not ready"
                self.assert_qdrant_healthy()

                info_response = requests.get("http://localhost:6333/", timeout=10)
                assert info_response.status_code == 200
                service_info = info_response.json()
                assert "title" in service_info
                assert "version" in service_info

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

            finally:
                self.stop_qdrant_service(compose_file, temp_dir)
