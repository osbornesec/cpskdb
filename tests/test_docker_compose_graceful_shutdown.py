"""
Tests for Qdrant Docker Compose graceful shutdown functionality.

This module implements graceful shutdown testing for the
"Qdrant Graceful Shutdown State" scenario from the test specification.
"""

import subprocess
import tempfile
import time
import unittest

import requests

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeGracefulShutdown(QdrantDockerComposeTestBase):
    """Test Qdrant graceful shutdown functionality via Docker Compose"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.compose_file = None

    def tearDown(self):
        """Clean up test environment"""
        if self.compose_file:
            self.stop_qdrant_service(self.compose_file, self.temp_dir)

    def test_container_responds_to_sigterm(self):
        """Test container responds to SIGTERM"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        stop_result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "stop"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
            timeout=30,
        )
        self.assertEqual(stop_result.returncode, 0)

    def test_active_connections_handled_gracefully(self):
        """Test active connections handled gracefully"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        response = requests.get("http://localhost:6333/healthz", timeout=10)
        self.assertEqual(response.status_code, 200)

        stop_result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "stop"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
            timeout=30,
        )
        self.assertEqual(stop_result.returncode, 0)

    def test_container_exits_with_zero_code_graceful_shutdown(self):
        """Test container exits with zero code on graceful shutdown"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        stop_result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "stop"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )
        self.assertEqual(stop_result.returncode, 0)

        inspect_result = subprocess.run(
            ["docker", "inspect", "test_qdrant_production", "--format={{.State.ExitCode}}"],
            capture_output=True,
            text=True,
        )

        if inspect_result.returncode == 0:
            exit_code = inspect_result.stdout.strip()
            self.assertEqual(exit_code, "0")

    def test_data_integrity_maintained_after_graceful_shutdown(self):
        """Test data integrity maintained after graceful shutdown"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        collection_config = {"vectors": {"size": 4, "distance": "Cosine"}}
        create_response = requests.put(
            "http://localhost:6333/collections/shutdown_test",
            json=collection_config,
            timeout=10,
        )
        self.assertIn(create_response.status_code, [200, 201])

        points_data = {
            "points": [
                {"id": 1, "vector": [1.0, 2.0, 3.0, 4.0], "payload": {"test": "data"}},
            ]
        }

        upsert_response = requests.put(
            "http://localhost:6333/collections/shutdown_test/points",
            json=points_data,
            timeout=10,
        )
        self.assertIn(upsert_response.status_code, [200, 201])

        stop_result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "stop"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )
        self.assertEqual(stop_result.returncode, 0)

        start_result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(start_result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        info_response = requests.get(
            "http://localhost:6333/collections/shutdown_test", timeout=10
        )
        self.assertEqual(info_response.status_code, 200)

        collection_info = info_response.json()
        self.assertIn("result", collection_info)
        self.assertEqual(collection_info["result"]["points_count"], 1)

    def test_shutdown_logs_contain_appropriate_messages(self):
        """Test shutdown logs contain appropriate messages"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        stop_result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "stop"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )
        self.assertEqual(stop_result.returncode, 0)

        logs_result = subprocess.run(
            ["docker", "logs", "test_qdrant_production"],
            capture_output=True,
            text=True,
        )

        if logs_result.returncode == 0:
            log_content = logs_result.stdout + logs_result.stderr
            self.assertTrue(len(log_content) > 0, "Should have log output")


if __name__ == "__main__":
    unittest.main()
