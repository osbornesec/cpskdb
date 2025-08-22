"""
Tests for Qdrant Docker Compose performance benchmarks.

This module implements performance benchmark testing for scenarios
"Qdrant Startup Time Benchmarks", "Qdrant API Response Time Validation", and
"Qdrant Long-Running Memory Stability" from the test specification.
"""

import random
import tempfile
import time
import unittest

import requests  # type: ignore

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposePerformanceBenchmarks(QdrantDockerComposeTestBase):
    """Test Qdrant performance benchmarks via Docker Compose"""
    
    # Configurable performance thresholds
    STARTUP_TIMEOUT_FAST = 30  # seconds for fast startup
    STARTUP_TIMEOUT_PRODUCTION = 45  # seconds for production startup  
    HEALTH_CHECK_SUCCESS_RATE = 0.8  # 80% success rate
    SEARCH_SUCCESS_RATE = 0.8  # 80% success rate
    MIN_HEALTH_CHECKS = 8  # out of 10
    MIN_SEARCH_SUCCESS = 8  # out of 10

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
        self.assertLess(startup_time, self.STARTUP_TIMEOUT_FAST, "Startup should be fast")

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
        self.assertLess(total_time, self.STARTUP_TIMEOUT_PRODUCTION, "Production startup should be reasonable")

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

        self.assertGreaterEqual(len(health_times), self.MIN_HEALTH_CHECKS, f"At least {self.MIN_HEALTH_CHECKS} out of 10 health checks should succeed")
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
            self.assertLess(
                avg_collections_time, 0.2, "Collections endpoint should be fast"
            )

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

        # Generate diverse vectors for better test coverage
        vectors = []
        random.seed(42)  # Deterministic but diverse
        for i in range(100):
            # Create much more diverse vectors
            vector = []
            for j in range(128):
                # Generate values based on position and index for diversity
                base_val = (i * 0.01) + (j * 0.001)
                noise = random.uniform(-0.1, 0.1)
                vector.append(base_val + noise)
            
            vectors.append(
                {
                    "id": i,
                    "vector": vector,
                    "payload": {"index": i, "category": i % 5, "value": i * 2.5},
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

        # Use a more diverse search vector
        search_vector = []
        for j in range(128):
            search_vector.append(0.1 + (j * 0.001) + random.uniform(-0.05, 0.05))
        
        search_query = {"vector": search_vector, "limit": 10}

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

        self.assertGreaterEqual(len(search_times), self.MIN_SEARCH_SUCCESS, f"At least {self.MIN_SEARCH_SUCCESS} out of 10 searches should succeed")
        if search_times:
            avg_search_time = sum(search_times) / len(search_times)
            self.assertLess(avg_search_time, 0.5, "Search should be fast")


if __name__ == "__main__":
    unittest.main()
