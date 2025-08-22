"""
Tests for Qdrant Docker Compose developer workflow functionality.

This module implements developer workflow testing for scenarios
"Complete Qdrant Development Workflow" and "Developer Onboarding Workflow"
from the test specification.
"""

import logging
import os
import shutil
import tempfile
import time
import unittest

import requests

from tests.test_docker_compose_base import QdrantDockerComposeTestBase

logger = logging.getLogger(__name__)

# Test constants
VECTOR_DIM = 128
VECTOR_VAL_A = 0.1
VECTOR_VAL_B = 0.2


class TestQdrantDockerComposeDevWorkflow(QdrantDockerComposeTestBase):
    """Test Qdrant development workflow functionality via Docker Compose"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.compose_file = None

    def tearDown(self):
        """Clean up test environment"""
        if self.compose_file:
            self.stop_qdrant_service(self.compose_file, self.temp_dir)

        # Clean up temporary directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception:
                # Log but don't fail teardown
                pass

    def test_complete_developer_setup_from_fresh_environment(self):
        """Test complete developer setup from fresh environment"""
        compose_content = self.create_development_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)

        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

        response = requests.get("http://localhost:6333/healthz", timeout=10)
        self.assertEqual(response.status_code, 200)

        collections_response = requests.get(
            "http://localhost:6333/collections", timeout=10
        )
        self.assertEqual(collections_response.status_code, 200)

        collection_config = {"vectors": {"size": 4, "distance": "Cosine"}}
        create_response = requests.put(
            "http://localhost:6333/collections/dev_test",
            json=collection_config,
            timeout=10,
        )
        self.assertIn(create_response.status_code, [200, 201])

    def test_immediate_working_qdrant_environment(self):
        """Test immediate working Qdrant environment"""
        compose_content = self.create_development_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)

        start_time = time.monotonic()
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        ready_success = self.wait_for_qdrant_ready(timeout=30)
        setup_time = time.monotonic() - start_time

        self.assertTrue(ready_success)
        self.assertLess(setup_time, 60, "Environment should be ready quickly")

        response = requests.get("http://localhost:6333/healthz", timeout=5)
        self.assertEqual(response.status_code, 200)

    def test_basic_vector_operations_workflow(self):
        """Test basic vector operations workflow"""
        compose_content = self.create_development_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        collection_config = {"vectors": {"size": VECTOR_DIM, "distance": "Cosine"}}
        create_response = requests.put(
            "http://localhost:6333/collections/workflow_test",
            json=collection_config,
            timeout=10,
        )
        self.assertIn(create_response.status_code, [200, 201])

        vector_data = {
            "points": [
                {
                    "id": 1,
                    "vector": [VECTOR_VAL_A] * VECTOR_DIM,
                    "payload": {"text": "First document"},
                },
                {
                    "id": 2,
                    "vector": [VECTOR_VAL_B] * VECTOR_DIM,
                    "payload": {"text": "Second document"},
                },
            ]
        }

        upsert_response = requests.put(
            "http://localhost:6333/collections/workflow_test/points",
            json=vector_data,
            timeout=10,
        )
        self.assertIn(upsert_response.status_code, [200, 201])

        search_query = {
            "vector": [0.15] * 128,
            "limit": 5,
            "with_payload": True,
        }

        search_response = requests.post(
            "http://localhost:6333/collections/workflow_test/points/search",
            json=search_query,
            timeout=10,
        )
        self.assertEqual(search_response.status_code, 200)

        search_results = search_response.json()
        self.assertIn("result", search_results)
        self.assertGreater(len(search_results["result"]), 0)


if __name__ == "__main__":
    unittest.main()
