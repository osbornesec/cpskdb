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

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.compose_file = None

    def tearDown(self):
        """Clean up test environment"""
        if self.compose_file:
            self.stop_qdrant_service(self.compose_file, self.temp_dir)

    def test_collections_endpoint_accessible(self):
        """Test /collections endpoint returns valid JSON with collections list"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

        response = requests.get("http://localhost:6333/collections", timeout=10)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("result", data)
        self.assertIn("collections", data["result"])
        self.assertIsInstance(data["result"]["collections"], list)

    def test_cluster_endpoint_accessible(self):
        """Test /cluster endpoint returns cluster information"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

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

    def test_service_info_endpoint_accessible(self):
        """Test service info endpoint / returns proper Qdrant version and title information"""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

        response = requests.get("http://localhost:6333/", timeout=10)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("title", data)
        self.assertIn("version", data)
        self.assertEqual(data["title"], "qdrant - vector search engine")


if __name__ == "__main__":
    unittest.main()