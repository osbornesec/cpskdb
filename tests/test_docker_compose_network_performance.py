"""Test Qdrant Docker Compose network performance scenarios.

This module implements network performance testing including load testing,
connectivity edge cases, and failover scenarios.
"""

import subprocess
import tempfile
import threading
import time

import requests

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeNetworkPerformance(QdrantDockerComposeTestBase):
    """Test Qdrant network performance functionality via Docker Compose."""

    # Production container name constant
    QDRANT_CONTAINER_NAME = "test_qdrant_production"

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.compose_file = None

    def tearDown(self):
        """Clean up test environment."""
        if self.compose_file:
            self.stop_qdrant_service(self.compose_file, self.temp_dir)
        if self.temp_dir:
            import shutil

            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir = None

    def test_network_connectivity_edge_cases_and_recovery(self):
        """Test network connectivity edge cases and failure recovery."""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        assert result.returncode == 0
        assert self.wait_for_qdrant_ready()

        connection_results = []
        for _i in range(10):
            try:
                response = requests.get("http://localhost:6333/healthz", timeout=2)
                connection_results.append(response.status_code == 200)
            except requests.exceptions.RequestException:
                connection_results.append(False)

        success_rate = sum(connection_results) / len(connection_results)
        assert success_rate > 0.8, "Should handle rapid successive connections"

        concurrent_results = []

        def make_request() -> None:
            try:
                response = requests.get("http://localhost:6333/healthz", timeout=5)
                concurrent_results.append(response.status_code == 200)
            except requests.exceptions.RequestException:
                concurrent_results.append(False)

        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        concurrent_success = sum(concurrent_results) / len(concurrent_results)
        assert concurrent_success > 0.8, "Should handle concurrent connections"

    def test_network_performance_under_load(self):
        """Test network performance under various load conditions."""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        assert result.returncode == 0
        assert self.wait_for_qdrant_ready()

        operation_times = []
        errors = []

        def perform_operations() -> None:
            """Perform multiple operations and measure timing."""
            try:
                start = time.monotonic()
                response = requests.get("http://localhost:6333/healthz", timeout=5)
                if response.status_code == 200:
                    operation_times.append(time.monotonic() - start)

                start = time.monotonic()
                response = requests.get(
                    "http://localhost:6333/collections/network_perf_test", timeout=5
                )
                # Accept both 200 (exists) and 404 (not found) as valid responses
                if response.status_code in [200, 404]:
                    operation_times.append(time.monotonic() - start)
            except requests.exceptions.RequestException as e:
                errors.append(f"{type(e).__name__}: {e!s}")

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=perform_operations)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        if operation_times:
            avg_time = sum(operation_times) / len(operation_times)
            max_time = max(operation_times)

            assert avg_time < 1.0, "Average operation time should be fast"
            assert max_time < 3.0, "Maximum operation time should be reasonable"

        error_rate = (
            len(errors) / (len(operation_times) + len(errors))
            if (len(operation_times) + len(errors)) > 0
            else 0
        )
        assert error_rate < 0.1, "Error rate should be low"

    def test_network_failover_and_recovery_scenarios(self):
        """Test network failover and recovery scenarios."""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        assert result.returncode == 0
        assert self.wait_for_qdrant_ready()

        response = requests.get("http://localhost:6333/healthz", timeout=10)
        assert response.status_code == 200

        # Verify container exists before attempting restart
        inspect_result = subprocess.run(
            ["docker", "inspect", self.QDRANT_CONTAINER_NAME],
            check=False,
            capture_output=True,
            text=True,
        )
        assert inspect_result.returncode == 0, f"Container '{self.QDRANT_CONTAINER_NAME}' not found"

        restart_result = subprocess.run(
            ["docker", "restart", self.QDRANT_CONTAINER_NAME],
            check=False,
            capture_output=True,
        )
        assert restart_result.returncode == 0

        recovery_success = self.wait_for_qdrant_ready(timeout=60)
        assert recovery_success, "Service should recover after restart"

        recovery_response = requests.get("http://localhost:6333/healthz", timeout=10)
        assert recovery_response.status_code == 200

        collection_config = {"vectors": {"size": 4, "distance": "Cosine"}}
        create_response = requests.put(
            "http://localhost:6333/collections/recovery_test",
            json=collection_config,
            timeout=10,
        )
        assert create_response.status_code in [200, 201]
