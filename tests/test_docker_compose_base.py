"""
Base test functionality for Docker Compose Qdrant tests
"""

import subprocess
import time
import unittest
from pathlib import Path

import requests  # type: ignore


class QdrantDockerComposeTestBase(unittest.TestCase):
    """Base class for Qdrant Docker Compose tests"""

    @staticmethod
    def create_basic_compose_content():
        """Create basic docker-compose.yml content for Qdrant"""
        return """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_basic
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

    @staticmethod
    def create_production_compose_content():
        """Create production-like docker-compose.yml content"""
        return """
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

volumes:
  qdrant_data:
  qdrant_snapshots:
"""

    def setup_compose_file(self, compose_content, temp_dir):
        """Setup docker-compose file in temporary directory"""
        compose_file = Path(temp_dir) / "docker-compose.yml"
        compose_file.write_text(compose_content)
        return compose_file

    def start_qdrant_service(self, compose_file, temp_dir, service_name="qdrant"):
        """Start Qdrant service using docker-compose"""
        result = subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "up", service_name, "-d"],
            capture_output=True,
            text=True,
            cwd=temp_dir,
        )
        return result

    def stop_qdrant_service(self, compose_file, temp_dir, remove_volumes=True):
        """Stop and cleanup Qdrant service"""
        cmd = ["docker", "compose", "-f", str(compose_file), "down"]
        if remove_volumes:
            cmd.append("-v")
        subprocess.run(cmd, capture_output=True, cwd=temp_dir)

    def wait_for_qdrant_ready(self, timeout=30):
        """Wait for Qdrant service to be ready"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get("http://localhost:6333/healthz", timeout=5)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        return False

    def assert_qdrant_healthy(self):
        """Assert that Qdrant service is healthy"""
        response = requests.get("http://localhost:6333/healthz", timeout=10)
        self.assertEqual(response.status_code, 200)
        
        # Handle both JSON and plain text responses
        try:
            json_data = response.json()
            if "status" in json_data:
                self.assertIn(json_data.get("status"), ["ok", "healthy"])
            else:
                # Check for any truthy health indicator
                self.assertTrue(any(json_data.values()), "Health check JSON should contain truthy values")
        except (ValueError, requests.exceptions.JSONDecodeError):
            # Fallback to text response - check for common health indicators
            response_text = response.text.lower()
            health_indicators = ["ok", "health", "ready"]
            self.assertTrue(
                any(indicator in response_text for indicator in health_indicators),
                f"Health check response should contain health indicators. Got: {response.text[:100]}"
            )

    def create_test_collection(self, collection_name="test_collection", vector_size=4):
        """Create a test collection in Qdrant"""
        test_data = {"vectors": {"size": vector_size, "distance": "Cosine"}}
        response = requests.put(
            f"http://localhost:6333/collections/{collection_name}",
            json=test_data,
            timeout=10,
        )
        self.assertIn(response.status_code, [200, 201])
        return response

    def verify_collection_exists(self, collection_name="test_collection"):
        """Verify that a collection exists and is accessible"""
        response = requests.get(
            f"http://localhost:6333/collections/{collection_name}", timeout=10
        )
        self.assertEqual(response.status_code, 200)
        return response

    def create_snapshot(self, collection_name="test_collection"):
        """Create a snapshot via Qdrant API and return the response"""
        try:
            response = requests.post(
                f"http://localhost:6333/collections/{collection_name}/snapshots",
                timeout=30,
            )
            self.assertIn(
                response.status_code,
                [200, 201],
                f"Snapshot creation failed with status {response.status_code}: {response.text}",
            )
        except requests.exceptions.RequestException as e:
            self.fail(f"Failed to create snapshot: {e}")
        return response

    def list_snapshots_host_dir(self, host_dir):
        """List snapshot files in the host directory"""
        snapshots_path = Path(host_dir) / "snapshots"
        if not snapshots_path.exists():
            return []
        return list(snapshots_path.glob("*.snapshot"))

    def measure_startup_time(self, compose_file, temp_dir):
        """Measure container startup time using time.monotonic()"""
        start_time = time.monotonic()
        result = self.start_qdrant_service(compose_file, temp_dir)
        if result.returncode == 0:
            # Wait for service to be ready
            ready = self.wait_for_qdrant_ready(timeout=60)
            end_time = time.monotonic()
            startup_time = end_time - start_time
            return startup_time, ready
        return None, False

    def measure_api_latency(self, endpoint="/healthz", num_requests=5):
        """Measure average API response times"""
        latencies = []
        for _ in range(num_requests):
            start_time = time.monotonic()
            try:
                response = requests.get(f"http://localhost:6333{endpoint}", timeout=10)
                end_time = time.monotonic()
                if response.status_code in [
                    200,
                    404,
                ]:  # 404 is acceptable for some endpoints
                    latencies.append(end_time - start_time)
            except requests.exceptions.RequestException:
                pass
        return sum(latencies) / len(latencies) if latencies else None
