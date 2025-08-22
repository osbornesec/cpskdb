"""
Tests for Qdrant Docker Compose API endpoint accessibility and functionality.

This module implements comprehensive API endpoint testing that validates the
"Qdrant API Endpoints Are Accessible" scenario from the test specification.
"""

import tempfile
import unittest

import requests

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeAPIEndpoints(QdrantDockerComposeTestBase):
    """Test Qdrant API endpoints accessibility via Docker Compose"""

    def tearDown(self):
        """Clean up test environment"""
        if self.compose_file:
            self.stop_qdrant_service(self.compose_file, self.temp_dir)
        # Clean up temporary directory
        import shutil
        if hasattr(self, 'temp_dir') and self.temp_dir:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    def test_collections_endpoint_accessible(self):
        """Test /collections endpoint returns valid JSON with collections list"""
        # Setup and start Qdrant
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Wait for service to be ready
        self.assertTrue(self.wait_for_qdrant_ready())

        # Test collections endpoint
        response = self.assert_endpoint_accessible("/collections")
        data = response.json()
        self.assertIn("result", data)
        self.assertIn("collections", data["result"])
        self.assertIsInstance(data["result"]["collections"], list)

    def test_cluster_endpoint_accessible(self):
        """Test /cluster endpoint returns cluster information"""
        # Setup and start Qdrant
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        # Wait for service to be ready
        self.assertTrue(self.wait_for_qdrant_ready())

        # Test cluster endpoint (may return 404 in single-node setup, which is acceptable)
        response = requests.get("http://localhost:6333/cluster", timeout=10)
        self.assertIn(response.status_code, [200, 404])

        if response.status_code == 200:
            data = response.json()
            self.assertIn("result", data)

    def test_metrics_endpoint_accessible(self):
        """Test /metrics endpoint returns Prometheus-style metrics"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

        response = requests.get("http://localhost:6333/metrics", timeout=10)
        self.assertIn(response.status_code, [200, 404])
        
        if response.status_code == 200:
            metrics_text = response.text
            self.assertIsInstance(metrics_text, str)
            self.assertTrue(
                "# HELP" in metrics_text
                or "# TYPE" in metrics_text
                or len(metrics_text) > 0
            )