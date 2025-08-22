"""
Integration and interaction tests for Qdrant Docker Compose configuration
"""

import subprocess
import tempfile
import time
import requests  # type: ignore

from tests.test_docker_compose_base import QdrantDockerComposeTestBase  # type: ignore


class TestQdrantDockerComposeIntegration(QdrantDockerComposeTestBase):
    """Integration and interaction tests for Qdrant Docker Compose configuration"""

    def test_qdrant_multi_service_docker_compose_integration(self):
        """Test: Qdrant Service Integrates with Docker Compose Stack"""
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
  test_client:
    image: nginx:alpine
    container_name: test_client_service
    networks:
      - rag-network
    depends_on:
      - qdrant
    command: >
      sh -c "
        echo 'Testing Qdrant connectivity...' &&
        sleep 10 &&
        wget --no-verbose --tries=3 --timeout=10 -O- http://qdrant:6333/healthz &&
        echo 'Qdrant connectivity test successful!' &&
        nginx -g 'daemon off;'
      "
volumes:
  qdrant_data:
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = self.setup_compose_file(compose_content, temp_dir)

            try:
                result = subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "up", "-d"],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir,
                )
                self.assertEqual(
                    result.returncode, 0, f"Docker compose failed: {result.stderr}"
                )

                time.sleep(15)
                self.assertTrue(
                    self.wait_for_qdrant_ready(), "Qdrant not accessible from host"
                )
                self.assert_qdrant_healthy()

                client_logs = subprocess.run(
                    ["docker", "logs", "test_client_service"],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(client_logs.returncode, 0)
                logs_text = client_logs.stdout.lower()
                self.assertTrue(
                    "connectivity test successful" in logs_text
                    or "healthz check passed" in logs_text,
                    f"Internal network connectivity failed. Logs: {client_logs.stdout}",
                )

            finally:
                self.stop_qdrant_service(compose_file, temp_dir)

    def test_qdrant_network_isolation_and_service_discovery(self):
        """Test: Qdrant Service Discovery Within Docker Network"""
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
                    capture_output=True,
                    text=True,
                    cwd=temp_dir,
                )
                self.assertEqual(
                    result.returncode, 0, f"Docker compose failed: {result.stderr}"
                )

                time.sleep(10)
                tester_logs = subprocess.run(
                    ["docker", "logs", "network_tester"], capture_output=True, text=True
                )
                self.assertEqual(tester_logs.returncode, 0)
                logs_text = tester_logs.stdout.lower()

                self.assertIn("testing dns resolution", logs_text)
                self.assertTrue(
                    "healthz check passed" in logs_text
                    or "network tests completed successfully" in logs_text,
                    f"Network connectivity tests failed. Logs: {tester_logs.stdout}",
                )

            finally:
                self.stop_qdrant_service(compose_file, temp_dir)

    def test_qdrant_production_like_configuration(self):
        """Test: Qdrant Production-like Configuration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            compose_file = self.setup_compose_file(
                self.create_production_compose_content(), temp_dir
            )

            try:
                result = self.start_qdrant_service(compose_file, temp_dir)
                self.assertEqual(
                    result.returncode, 0, f"Docker compose failed: {result.stderr}"
                )

                self.assertTrue(
                    self.wait_for_qdrant_ready(30), "Production service not ready"
                )
                self.assert_qdrant_healthy()

                import requests

                info_response = requests.get("http://localhost:6333/", timeout=10)
                self.assertEqual(info_response.status_code, 200)
                service_info = info_response.json()
                self.assertIn("title", service_info)
                self.assertIn("version", service_info)

                collection_data = {
                    "vectors": {"size": 384, "distance": "Cosine"},
                    "optimizers_config": {"default_segment_number": 2},
                }
                create_response = requests.put(
                    "http://localhost:6333/collections/production_test",
                    json=collection_data,
                    timeout=10,
                )
                self.assertIn(create_response.status_code, [200, 201])

            finally:
                self.stop_qdrant_service(compose_file, temp_dir)
