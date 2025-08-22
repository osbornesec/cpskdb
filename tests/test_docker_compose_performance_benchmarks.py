"""
Tests for Qdrant Docker Compose performance benchmarks.

This module implements performance benchmark testing for scenarios
"Qdrant Startup Time Benchmarks", "Qdrant API Response Time Validation", and
"Qdrant Long-Running Memory Stability" from the test specification.
"""

import psutil
import subprocess
import tempfile
import time
import unittest

import requests

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposePerformanceBenchmarks(QdrantDockerComposeTestBase):
    """Test Qdrant performance benchmarks via Docker Compose"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.compose_file = None

    def tearDown(self):
        """Clean up test environment"""
        if self.compose_file:
            self.stop_qdrant_service(self.compose_file, self.temp_dir)

    def test_container_startup_time_within_limits(self):
        """Test container startup time within limits"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)

        start_time = time.monotonic()
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        startup_time = time.monotonic() - start_time

        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())
        self.assertLess(startup_time, 30, "Startup should be fast")

    def test_production_startup_time_benchmark(self):
        """Test production startup time benchmark"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)

        start_time = time.monotonic()
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        ready_success = self.wait_for_qdrant_ready(timeout=60)
        total_time = time.monotonic() - start_time

        self.assertTrue(ready_success)
        self.assertLess(total_time, 45, "Production startup should be reasonable")

    def test_api_response_times_meet_requirements(self):
        """Test API response times meet requirements"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        health_times = []
        for _ in range(10):
            start = time.monotonic()
            response = requests.get("http://localhost:6333/healthz", timeout=5)
            duration = time.monotonic() - start
            if response.status_code == 200:
                health_times.append(duration)

        self.assertGreater(len(health_times), 5, "Most health checks should succeed")
        if health_times:
            avg_time = sum(health_times) / len(health_times)
            self.assertLess(avg_time, 0.1, "Health checks should be fast")

        collections_times = []
        for _ in range(5):
            start = time.monotonic()
            response = requests.get("http://localhost:6333/collections", timeout=5)
            duration = time.monotonic() - start
            if response.status_code == 200:
                collections_times.append(duration)

        if collections_times:
            avg_collections_time = sum(collections_times) / len(collections_times)
            self.assertLess(avg_collections_time, 0.2, "Collections endpoint should be fast")

    def test_collection_operations_performance(self):
        """Test collection operations performance"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        collection_config = {"vectors": {"size": 128, "distance": "Cosine"}}

        start_time = time.monotonic()
        create_response = requests.put(
            "http://localhost:6333/collections/perf_test",
            json=collection_config,
            timeout=10,
        )
        create_time = time.monotonic() - start_time

        self.assertIn(create_response.status_code, [200, 201])
        self.assertLess(create_time, 5.0, "Collection creation should be fast")

        vectors = []
        for i in range(100):
            vectors.append(
                {
                    "id": i,
                    "vector": [0.1 * (i % 10)] * 128,
                    "payload": {"index": i},
                }
            )

        batch_data = {"points": vectors}

        start_time = time.monotonic()
        upsert_response = requests.put(
            "http://localhost:6333/collections/perf_test/points",
            json=batch_data,
            timeout=30,
        )
        upsert_time = time.monotonic() - start_time

        self.assertIn(upsert_response.status_code, [200, 201])
        self.assertLess(upsert_time, 10.0, "Batch upsert should be efficient")

        search_query = {"vector": [0.1] * 128, "limit": 10}

        search_times = []
        for _ in range(10):
            start = time.monotonic()
            search_response = requests.post(
                "http://localhost:6333/collections/perf_test/points/search",
                json=search_query,
                timeout=5,
            )
            duration = time.monotonic() - start

            if search_response.status_code == 200:
                search_times.append(duration)

        self.assertGreater(len(search_times), 5, "Most searches should succeed")
        if search_times:
            avg_search_time = sum(search_times) / len(search_times)
            self.assertLess(avg_search_time, 0.5, "Search should be fast")

import statistics
import subprocess
import tempfile
import threading
import time
import unittest
        request_times = []
        request_errors = []
        num_threads = 5
        requests_per_thread = 10

        def make_concurrent_requests():
            """Make multiple requests and record timing"""
            session = requests.Session()
            for _ in range(requests_per_thread):
                start_time = time.monotonic()
                try:
                    response = session.get("http://localhost:6333/healthz", timeout=5)
                    request_time = time.monotonic() - start_time
                    if response.status_code == 200:
                        request_times.append(request_time)
                    else:
                        request_errors.append(response.status_code)
                except requests.exceptions.RequestException as e:
                    request_errors.append(str(e))
            session.close()

        # Run concurrent requests
        threads = []
        start_time = time.monotonic()

        for _ in range(num_threads):
            thread = threading.Thread(target=make_concurrent_requests)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        total_time = time.monotonic() - start_time

        # Analyze results
        total_requests = num_threads * requests_per_thread
        successful_requests = len(request_times)

        self.assertGreater(
            successful_requests, total_requests * 0.9, "Too many failed requests"
        )

        if request_times:
            avg_response_time = statistics.mean(request_times)
            max_response_time = max(request_times)

            self.assertLess(
                avg_response_time,
                0.5,
                f"Average response time {avg_response_time:.3f}s too slow",
            )
            self.assertLess(
                max_response_time,
                2.0,
                f"Max response time {max_response_time:.3f}s too slow",
            )

            print(f"Concurrent performance test:")
            print(f"  Total requests: {total_requests}")
            print(f"  Successful: {successful_requests}")
            print(f"  Errors: {len(request_errors)}")
            print(f"  Average response time: {avg_response_time:.3f}s")
            print(f"  Max response time: {max_response_time:.3f}s")
            print(f"  Total test time: {total_time:.2f}s")


if __name__ == "__main__":
    unittest.main()
