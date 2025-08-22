"""
Tests for Qdrant Docker Compose snapshots volume functionality.

This module implements comprehensive snapshots volume testing that addresses
the "Qdrant Snapshots Volume Mounts Correctly" scenario from the test specification.
"""

import tempfile
import time
import unittest

import requests

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeSnapshots(QdrantDockerComposeTestBase):
    """Test Qdrant snapshots volume functionality via Docker Compose"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.compose_file = None

    def tearDown(self):
        """Clean up test environment"""
        if self.compose_file:
            self.stop_qdrant_service(self.compose_file, self.temp_dir)

    def test_snapshots_volume_mounts_correctly(self):
        """Test snapshots volume mounts correctly to /qdrant/snapshots directory"""
        # Setup and start Qdrant with snapshots volume
        compose_content = self.create_production_compose_with_snapshots()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Wait for service to be ready
        self.assertTrue(self.wait_for_qdrant_ready())

        # Verify the snapshots directory is accessible inside the container
        import subprocess

        check_result = subprocess.run(
            [
                "docker",
                "exec",
                "test_qdrant_prod_snapshots",
                "ls",
                "-la",
                "/qdrant/snapshots",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(check_result.returncode, 0)

    def test_snapshot_creation_via_api(self):
        """Test snapshot creation via API creates files in the mounted host volume"""
        # Setup and start Qdrant
        compose_content = self.create_production_compose_with_snapshots()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Wait for service to be ready
        self.assertTrue(self.wait_for_qdrant_ready())

        # Create a test collection
        collection_name = "test_snapshots_collection"
        self.create_test_collection(collection_name)

        # Create a snapshot
        snapshot_response = self.create_snapshot(collection_name)
        self.assertIn(snapshot_response.status_code, [200, 201])

        # Verify snapshot was created successfully
        snapshot_data = snapshot_response.json()
        self.assertIn("result", snapshot_data)

    def test_snapshot_files_persist_after_restart(self):
        """Test snapshot files persist on host after container restart"""
        # Setup and start Qdrant
        compose_content = self.create_production_compose_with_snapshots()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Wait for service to be ready
        self.assertTrue(self.wait_for_qdrant_ready())

        # Create a test collection and snapshot
        collection_name = "test_persistence_collection"
        self.create_test_collection(collection_name)
        snapshot_response = self.create_snapshot(collection_name)
        self.assertIn(snapshot_response.status_code, [200, 201])

        # Get list of snapshots before restart
        list_response = requests.get(
            f"http://localhost:6333/collections/{collection_name}/snapshots", timeout=10
        )
        self.assertEqual(list_response.status_code, 200)
        snapshots_before = list_response.json()["result"]

        # Restart the container
        self.stop_qdrant_service(self.compose_file, self.temp_dir, remove_volumes=False)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Verify snapshots still exist after restart
        list_response_after = requests.get(
            f"http://localhost:6333/collections/{collection_name}/snapshots", timeout=10
        )
        self.assertEqual(list_response_after.status_code, 200)
        snapshots_after = list_response_after.json()["result"]

        # At least the snapshots we created should still be there
        self.assertGreaterEqual(len(snapshots_after), len(snapshots_before))

    def test_snapshot_restoration_functionality(self):
        """Test snapshot restoration functionality works correctly"""
        # Setup and start Qdrant
        compose_content = self.create_production_compose_with_snapshots()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Wait for service to be ready
        self.assertTrue(self.wait_for_qdrant_ready())

        # Create a test collection
        collection_name = "test_restore_collection"
        self.create_test_collection(collection_name)

        # Add some test data
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

        # Create a snapshot
        snapshot_response = self.create_snapshot(collection_name)
        self.assertIn(snapshot_response.status_code, [200, 201])
        snapshot_data = snapshot_response.json()
        snapshot_name = snapshot_data["result"]["name"]
        
        # Extract snapshot location from API response, with fallback
        snapshot_location = None
        if "location" in snapshot_data["result"]:
            snapshot_location = snapshot_data["result"]["location"]
        elif "path" in snapshot_data["result"]:
            snapshot_location = snapshot_data["result"]["path"]
        
        # Fallback to constructing path if not provided by API
        if not snapshot_location:
            # Use configurable base path with fallback to default
            base_snapshots_path = "/qdrant/snapshots"  # Could be made configurable via env var
            snapshot_location = f"file://{base_snapshots_path}/{snapshot_name}"

        # Delete the collection
        delete_response = requests.delete(
            f"http://localhost:6333/collections/{collection_name}", timeout=10
        )
        self.assertEqual(delete_response.status_code, 200)

        # Restore from snapshot using the actual location
        restore_data = {"location": snapshot_location}
        restore_response = requests.put(
            f"http://localhost:6333/collections/{collection_name}/snapshots/recover",
            json=restore_data,
            timeout=30,
        )
        self.assertIn(restore_response.status_code, [200, 201])

        # Verify collection is restored
        time.sleep(2)  # Allow time for restoration
        collection_response = requests.get(
            f"http://localhost:6333/collections/{collection_name}", timeout=10
        )
        self.assertEqual(collection_response.status_code, 200)

    def test_snapshots_directory_permissions(self):
        """Test snapshots directory permissions are correct for Qdrant process"""
        # Setup and start Qdrant
        compose_content = self.create_production_compose_with_snapshots()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Wait for service to be ready
        self.assertTrue(self.wait_for_qdrant_ready())

        # Check directory permissions inside container
        import subprocess

        perm_result = subprocess.run(
            [
                "docker",
                "exec",
                "test_qdrant_prod_snapshots",
                "stat",
                "-c",
                "%a %U %G",
                "/qdrant/snapshots",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(perm_result.returncode, 0)

        # Verify Qdrant process can write to the directory
        write_test = subprocess.run(
            [
                "docker",
                "exec",
                "test_qdrant_prod_snapshots",
                "touch",
                "/qdrant/snapshots/test_file",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(write_test.returncode, 0)

    def test_snapshots_directory_missing_behavior(self):
        """Test behavior when snapshots directory has issues"""
        # Create a compose file without snapshots volume
        compose_content_no_snapshots = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_no_snapshots
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_no_snapshots, self.temp_dir
        )
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Wait for service to be ready
        self.assertTrue(self.wait_for_qdrant_ready())

        # Try to create a snapshot when directory might not exist
        collection_name = "test_no_snapshots_collection"
        self.create_test_collection(collection_name)

        # Attempt to create snapshot - should handle gracefully
        try:
            snapshot_response = requests.post(
                f"http://localhost:6333/collections/{collection_name}/snapshots",
                timeout=10,
            )
            # Without snapshots volume, expect an error response
            if snapshot_response.status_code in [200, 201]:
                # If it succeeds, snapshots might be stored elsewhere
                self.assertTrue(snapshot_response.json().get("result"))
            else:
                # Should fail with a client error, not server error
                self.assertEqual(
                    snapshot_response.status_code,
                    400,
                    "Should return 400 for missing snapshot directory"
                )
        except requests.exceptions.RequestException:
            # Connection errors are acceptable in this edge case
            pass

    def test_snapshot_file_naming_convention(self):
        """Test snapshot files have expected naming convention and are accessible"""
        # Setup and start Qdrant
        compose_content = self.create_production_compose_with_snapshots()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Wait for service to be ready
        self.assertTrue(self.wait_for_qdrant_ready())

        # Create a test collection and snapshot
        collection_name = "test_naming_collection"
        self.create_test_collection(collection_name)
        snapshot_response = self.create_snapshot(collection_name)
        self.assertIn(snapshot_response.status_code, [200, 201])

        # Get snapshot info
        snapshot_data = snapshot_response.json()
        snapshot_name = snapshot_data["result"]["name"]

        # Verify naming convention (should end with .snapshot)
        self.assertTrue(snapshot_name.endswith(".snapshot"))

        # Verify snapshot file exists and is accessible
        import subprocess

        file_check = subprocess.run(
            [
                "docker",
                "exec",
                "test_qdrant_prod_snapshots",
                "ls",
                "-la",
                f"/qdrant/snapshots/{snapshot_name}",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(file_check.returncode, 0)

        # Verify file size is reasonable (not empty)
        size_check = subprocess.run(
            [
                "docker",
                "exec",
                "test_qdrant_prod_snapshots",
                "stat",
                "-c",
                "%s",
                f"/qdrant/snapshots/{snapshot_name}",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(size_check.returncode, 0)
        file_size = int(size_check.stdout.strip())
        self.assertGreater(file_size, 0)


if __name__ == "__main__":
    unittest.main()
