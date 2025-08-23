"""
Tests for Qdrant Docker Compose restart policy functionality.

This module implements restart policy testing that validates the
"Qdrant Restart Policy Functions Correctly" scenario from the test specification.
"""

import subprocess
import tempfile
import time
import unittest

import requests

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeRestartPolicy(QdrantDockerComposeTestBase):
    """Test Qdrant restart policy functionality via Docker Compose"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.compose_file = None

    def tearDown(self):
        """Clean up test environment"""
        if self.compose_file:
            self.stop_qdrant_service(self.compose_file, self.temp_dir)

    def get_container_restart_count(self, container_name):
        """Get the restart count for a container."""
        try:
            result = subprocess.run(
                ["docker", "inspect", container_name, "--format={{.RestartCount}}"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                try:
                    return int(result.stdout.strip())
                except ValueError:
                    return None
            return None
        except Exception:
            return None

    def test_container_restarts_after_unexpected_exit(self):
        """Test container automatically restarts when it exits unexpectedly"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

        initial_restart_count = self.get_container_restart_count(
            "test_qdrant_production"
        )
        self.assertIsNotNone(initial_restart_count)

        kill_result = subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "kill", "-s", "SIGKILL", "qdrant"],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )
        self.assertEqual(kill_result.returncode, 0)

        time.sleep(5)
        new_restart_count = self.get_container_restart_count("test_qdrant_production")
        self.assertIsNotNone(new_restart_count)
        self.assertGreater(new_restart_count, initial_restart_count)
        self.assertTrue(self.wait_for_qdrant_ready(timeout=60))

    def test_unless_stopped_policy_behavior(self):
        """Test unless-stopped policy behavior"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

        kill_result = subprocess.run(
            ["docker", "kill", "--signal=SIGKILL", "test_qdrant_production"],
            capture_output=True,
        )
        self.assertEqual(kill_result.returncode, 0)
        time.sleep(5)
        self.assertTrue(self.wait_for_qdrant_ready(timeout=60))

        subprocess.run(
            ["docker", "stop", "test_qdrant_production"], capture_output=True
        )
        time.sleep(5)

        status_result = subprocess.run(
            [
                "docker",
                "inspect",
                "test_qdrant_production",
                "--format={{.State.Running}}",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(status_result.returncode, 0)
        self.assertEqual(status_result.stdout.strip(), "false")

    def test_service_available_after_restart(self):
        """Test that service becomes available again without manual intervention after restart"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

        collection_name = "test_restart_collection"
        self.create_test_collection(collection_name)
        self.verify_collection_exists(collection_name)

        subprocess.run(
            ["docker", "kill", "--signal=SIGKILL", "test_qdrant_production"],
            capture_output=True,
        )

        self.assertTrue(self.wait_for_qdrant_ready(timeout=60))
        self.assert_qdrant_healthy()

        response = requests.get("http://localhost:6333/collections", timeout=10)
        self.assertEqual(response.status_code, 200)

    def test_data_persists_across_automatic_restarts(self):
        """Test that data persists across automatic restarts"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

        collection_name = "test_persistence_collection"
        self.create_test_collection(collection_name)

        test_points = {
            "points": [
                {"id": 1, "vector": [0.1, 0.2, 0.3, 0.4]},
                {"id": 2, "vector": [0.5, 0.6, 0.7, 0.8]},
            ]
        }
        points_response = requests.put(
            f"http://localhost:6333/collections/{collection_name}/points",
            json=test_points,
            timeout=10,
        )
        self.assertEqual(points_response.status_code, 200)

        subprocess.run(
            ["docker", "kill", "--signal=SIGKILL", "test_qdrant_production"],
            capture_output=True,
        )

        self.assertTrue(self.wait_for_qdrant_ready(timeout=60))
        points_response = requests.post(
            f"http://localhost:6333/collections/{collection_name}/points/scroll",
            json={"limit": 10},
            timeout=10,
        )
        self.assertEqual(points_response.status_code, 200)
        points_data = points_response.json()
        self.assertEqual(len(points_data.get("result", {}).get("points", [])), 2)
        # Verify the point IDs are preserved
        point_ids = [p["id"] for p in points_data.get("result", {}).get("points", [])]
        self.assertIn(1, point_ids)
        self.assertIn(2, point_ids)

    def test_restart_policy_configuration(self):
        """Test that restart policy is properly configured in compose"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

        inspect_result = subprocess.run(
            [
                "docker",
                "inspect",
                "test_qdrant_production",
                "--format={{.HostConfig.RestartPolicy.Name}}",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(inspect_result.returncode, 0)
        restart_policy = inspect_result.stdout.strip()
        self.assertEqual(restart_policy, "unless-stopped")


if __name__ == "__main__":
    unittest.main()
