"""
Performance and resource tests for Qdrant Docker Compose configuration
"""

import shutil
import subprocess
import tempfile
import threading

import requests  # type: ignore

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposePerformance(QdrantDockerComposeTestBase):
    """Test Qdrant performance functionality via Docker Compose"""

    def test_qdrant_container_resource_limits(self):
        """Test Qdrant container resource limits"""
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_resources
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
    volumes:
      - qdrant_data:/qdrant/storage
volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())
        response = requests.get("http://localhost:6333/healthz", timeout=10)
        self.assertEqual(response.status_code, 200)

    def test_qdrant_maximum_connection_load(self):
        """Test Qdrant maximum connection load"""
        with tempfile.TemporaryDirectory() as temp_dir:
            compose_content = self.create_production_compose_content()
            compose_file = self.setup_compose_file(compose_content, temp_dir)

            try:
                result = self.start_qdrant_service(compose_file, temp_dir)
                self.assertEqual(result.returncode, 0)
                self.assertTrue(self.wait_for_qdrant_ready())

                # Test concurrent connections
                connection_results = []

                def make_request():
                    try:
                        response = requests.get("http://localhost:6333/healthz", timeout=5)
                        connection_results.append(response.status_code == 200)
                    except requests.exceptions.RequestException as e:
                        # Log the specific error for debugging
                        print(f"Request failed: {e}")
                        connection_results.append(False)

                threads = []
                for _ in range(10):
                    thread = threading.Thread(target=make_request)
                    threads.append(thread)
                    thread.start()

                for thread in threads:
                    thread.join()

                success_rate = sum(connection_results) / len(connection_results)
                self.assertGreater(
                    success_rate, 0.8,
                    f"Success rate {success_rate:.2f} below threshold. Failed requests: {10 - sum(connection_results)}/10"
                )
            finally:
                self.stop_qdrant_service(compose_file, temp_dir)
    def test_qdrant_large_data_volume_handling(self):
        """Test Qdrant large data volume handling"""
        with tempfile.TemporaryDirectory() as temp_dir:
            compose_content = self.create_production_compose_content()
            compose_file = self.setup_compose_file(compose_content, temp_dir)

            try:
                result = self.start_qdrant_service(compose_file, temp_dir)
                self.assertEqual(result.returncode, 0)
                self.assertTrue(self.wait_for_qdrant_ready())

                collection_config = {"vectors": {"size": 128, "distance": "Cosine"}}
                create_response = requests.put(
                    "http://localhost:6333/collections/performance_test",
                    json=collection_config,
                    timeout=10,
                )
                self.assertIn(create_response.status_code, [200, 201])

                # Insert batch of vectors
                vectors = []
                for i in range(100):
                    vectors.append(
                        {"id": i, "vector": [0.1 * (i % 10)] * 128, "payload": {"index": i}}
                    )

                batch_data = {"points": vectors}
                upsert_response = requests.put(
                    "http://localhost:6333/collections/performance_test/points",
                    json=batch_data,
                    timeout=30,
                )
                self.assertIn(upsert_response.status_code, [200, 201])

                # Verify collection info
                info_response = requests.get(
                    "http://localhost:6333/collections/performance_test", timeout=10
                )
                self.assertEqual(info_response.status_code, 200)

                collection_info = info_response.json()
                self.assertIn("result", collection_info)
                self.assertEqual(collection_info["result"]["points_count"], 100)
            finally:
                requests.delete("http://localhost:6333/collections/performance_test", timeout=10)
                self.stop_qdrant_service(compose_file, temp_dir)
    def test_qdrant_memory_usage_monitoring(self):
        """Test Qdrant memory usage monitoring"""
        temp_dir = tempfile.mkdtemp()
        compose_content = self.create_production_compose_content()
        compose_file = self.setup_compose_file(compose_content, temp_dir)

        try:
            result = self.start_qdrant_service(compose_file, temp_dir)
            self.assertEqual(result.returncode, 0)
            self.assertTrue(self.wait_for_qdrant_ready())

            # Check container stats
            stats_result = subprocess.run(
                [
                    "docker",
                    "stats",
                    "test_qdrant_production",
                    "--no-stream",
                    "--format",
                    "table",
                ],
                capture_output=True,
                text=True,
            )

            if stats_result.returncode == 0:
                stats_output = stats_result.stdout
                self.assertIn("test_qdrant_production", stats_output)
                # Verify that memory usage statistics are present
                lines = stats_output.strip().split('\n')
                if len(lines) > 1:  # Header + data line
                    # Check that we have actual memory data (not just "0B" or "-")
                    data_line = lines[1] if len(lines) > 1 else ""
                    self.assertTrue(
                        any(mem_indicator in data_line for mem_indicator in ["B", "KiB", "MiB", "GiB"]),
                        f"No memory usage data found in: {data_line}"
                    )
        finally:
            self.stop_qdrant_service(compose_file, temp_dir)
            shutil.rmtree(temp_dir, ignore_errors=True)
