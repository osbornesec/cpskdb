"""
Tests for Qdrant Docker Compose state persistence functionality.

This module implements comprehensive state persistence testing for scenarios
"Qdrant Maintains Collection State", "Qdrant Index State Persistence", and
"Qdrant Data Persistence Across Stack Restarts" from the test specification.
"""

import subprocess
import tempfile
import time
import unittest

import requests

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeStatePersistence(QdrantDockerComposeTestBase):
    """Test Qdrant state persistence functionality via Docker Compose"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.compose_file = None

    def tearDown(self):
        """Clean up test environment"""
        if self.compose_file:
            self.stop_qdrant_service(self.compose_file, self.temp_dir)

    def test_collection_metadata_persists_across_restarts(self):
        """Test collection metadata persists across restarts"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        collection_config = {"vectors": {"size": 128, "distance": "Cosine"}}
        create_response = requests.put(
            "http://localhost:6333/collections/persist_test",
            json=collection_config,
            timeout=10,
        )
        self.assertIn(create_response.status_code, [200, 201])

        restart_result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "restart"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )
        self.assertEqual(restart_result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        info_response = requests.get(
            "http://localhost:6333/collections/persist_test", timeout=10
        )
        self.assertEqual(info_response.status_code, 200)

        collection_info = info_response.json()
        self.assertIn("result", collection_info)
        self.assertEqual(collection_info["result"]["config"]["params"]["vectors"]["size"], 128)

    def test_index_state_preserved_after_restart(self):
        """Test index state preserved after restart"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        collection_config = {"vectors": {"size": 4, "distance": "Cosine"}}
        create_response = requests.put(
            "http://localhost:6333/collections/index_test",
            json=collection_config,
            timeout=10,
        )
        self.assertIn(create_response.status_code, [200, 201])

        points_data = {
            "points": [
                {"id": 1, "vector": [1.0, 2.0, 3.0, 4.0], "payload": {"test": "data1"}},
                {"id": 2, "vector": [2.0, 3.0, 4.0, 5.0], "payload": {"test": "data2"}},
            ]
        }

        upsert_response = requests.put(
            "http://localhost:6333/collections/index_test/points",
            json=points_data,
            timeout=10,
        )
        self.assertIn(upsert_response.status_code, [200, 201])

        restart_result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "restart"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )
        self.assertEqual(restart_result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        search_query = {"vector": [1.5, 2.5, 3.5, 4.5], "limit": 2}
        search_response = requests.post(
            "http://localhost:6333/collections/index_test/points/search",
            json=search_query,
            timeout=10,
        )
        self.assertEqual(search_response.status_code, 200)

        search_results = search_response.json()
        self.assertIn("result", search_results)
        self.assertEqual(len(search_results["result"]), 2)

    def test_vector_data_persists_across_full_stack_restart(self):
        """Test vector data persists across full stack restart"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        collection_config = {"vectors": {"size": 8, "distance": "Cosine"}}
        create_response = requests.put(
            "http://localhost:6333/collections/full_restart_test",
            json=collection_config,
            timeout=10,
        )
        self.assertIn(create_response.status_code, [200, 201])

        test_vectors = []
        for i in range(10):
            test_vectors.append({
                "id": i + 1,
                "vector": [float(i % 4)] * 8,
                "payload": {"category": f"test_{i}", "value": i * 10}
            })

        batch_data = {"points": test_vectors}
        upsert_response = requests.put(
            "http://localhost:6333/collections/full_restart_test/points",
            json=batch_data,
            timeout=10,
        )
        self.assertIn(upsert_response.status_code, [200, 201])

        down_result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "down"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )
        self.assertEqual(down_result.returncode, 0)

        up_result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "up", "-d"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )
        self.assertEqual(up_result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        info_response = requests.get(
            "http://localhost:6333/collections/full_restart_test", timeout=10
        )
        self.assertEqual(info_response.status_code, 200)

        collection_info = info_response.json()
        self.assertIn("result", collection_info)
        self.assertEqual(collection_info["result"]["points_count"], 10)

        search_query = {"vector": [1.0] * 8, "limit": 5, "with_payload": True}
        search_response = requests.post(
            "http://localhost:6333/collections/full_restart_test/points/search",
            json=search_query,
            timeout=10,
        )
        self.assertEqual(search_response.status_code, 200)

        search_results = search_response.json()
        self.assertIn("result", search_results)
        self.assertGreater(len(search_results["result"]), 0)

        for result in search_results["result"]:
            self.assertIn("payload", result)
            self.assertIn("category", result["payload"])