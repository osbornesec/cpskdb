"""
Tests for Qdrant Docker Compose state transitions and initialization.

This module tests state-related scenarios including container initialization,
data directory states, and volume remounting scenarios.
"""

import tempfile
import unittest

import requests  # type: ignore

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeStateTransitions(QdrantDockerComposeTestBase):
    """Test Qdrant state transitions via Docker Compose"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.compose_file = None

    def tearDown(self):
        """Clean up test environment"""
        if self.compose_file:
            self.stop_qdrant_service(self.compose_file, self.temp_dir)

    def test_container_initialization_state_scenarios(self):
        """Test various container initialization states"""
        compose_content_init_states = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_init_states
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
            compose_content_init_states, self.temp_dir
        )

        # Start service and verify clean initialization
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Verify initial state
        response = requests.get("http://localhost:6333/", timeout=30)
        self.assertEqual(response.status_code, 200)

        # Stop service
        self.stop_qdrant_service(self.compose_file, self.temp_dir)

    def test_data_directory_initialization_states(self):
        """Test data directory initialization states"""
        compose_content_data_states = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_data_states
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    volumes:
      - qdrant_persistent_data:/qdrant/storage

volumes:
  qdrant_persistent_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_data_states, self.temp_dir
        )

        # First initialization (new volume)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Stop service but keep volumes
        self.stop_qdrant_service(self.compose_file, self.temp_dir, remove_volumes=False)

        # Second initialization (existing volume with data)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Stop service
        self.stop_qdrant_service(self.compose_file, self.temp_dir)

    def test_volume_remounting_scenarios(self):
        """Test volume remounting scenarios and data persistence"""
        compose_content_remount = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_remount
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    volumes:
      - qdrant_remount_data:/qdrant/storage

volumes:
  qdrant_remount_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_remount, self.temp_dir
        )

        # Phase 1: Initial start with fresh volume
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Create some data to persist
        collection_data = {
            "name": "test_collection",
            "vectors": {"size": 4, "distance": "Dot"},
        }

        create_response = requests.put(
            "http://localhost:6333/collections/test_collection",
            json=collection_data,
            timeout=30,
        )
        self.assertEqual(create_response.status_code, 200)

        # Verify collection exists
        collections_response = requests.get(
            "http://localhost:6333/collections", timeout=30
        )
        self.assertEqual(collections_response.status_code, 200)
        collections_data = collections_response.json()
        collection_names = [
            col["name"] for col in collections_data["result"]["collections"]
        ]
        self.assertIn("test_collection", collection_names)

        # Stop service but preserve volume
        self.stop_qdrant_service(self.compose_file, self.temp_dir, remove_volumes=False)

        # Phase 2: Restart and verify data persistence
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Verify collection still exists after remount
        collections_response = requests.get(
            "http://localhost:6333/collections", timeout=30
        )
        self.assertEqual(collections_response.status_code, 200)
        collections_data = collections_response.json()
        collection_names = [
            col["name"] for col in collections_data["result"]["collections"]
        ]
        self.assertIn("test_collection", collection_names)

        # Phase 3: Test volume remount with configuration changes
        self.stop_qdrant_service(self.compose_file, self.temp_dir, remove_volumes=False)

        # Update compose with different log level but same volume
        compose_content_updated = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_remount
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=DEBUG  # Changed log level
    volumes:
      - qdrant_remount_data:/qdrant/storage  # Same volume

volumes:
  qdrant_remount_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_updated, self.temp_dir
        )

        # Start with updated config but same volume
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        # Verify data persists through config changes
        collections_response = requests.get(
            "http://localhost:6333/collections", timeout=30
        )
        self.assertEqual(collections_response.status_code, 200)
        collections_data = collections_response.json()
        collection_names = [
            col["name"] for col in collections_data["result"]["collections"]
        ]
        self.assertIn("test_collection", collection_names)

        # Final cleanup
        self.stop_qdrant_service(self.compose_file, self.temp_dir)


if __name__ == "__main__":
    unittest.main()
