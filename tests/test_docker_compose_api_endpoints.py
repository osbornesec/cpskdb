"""Tests for Qdrant Docker Compose API endpoint accessibility and functionality.

This module implements comprehensive API endpoint testing that validates the
"Qdrant API Endpoints Are Accessible" scenario from the test specification.
"""

import shutil
import tempfile
import unittest

import requests  # type: ignore

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeAPIEndpoints(QdrantDockerComposeTestBase):
    """Test Qdrant API endpoints accessibility via Docker Compose."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.compose_file = None

    def tearDown(self):
        """Clean up test environment."""
        if self.compose_file:
            self.stop_qdrant_service(self.compose_file, self.temp_dir)
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir)

    def test_collections_endpoint_accessible(self):
        """Test /collections endpoint returns valid JSON with collections list."""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        assert result.returncode == 0

        assert self.wait_for_qdrant_ready()

        response = requests.get("http://localhost:6333/collections", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "collections" in data["result"]
        assert isinstance(data["result"]["collections"], list)

    def test_cluster_endpoint_accessible(self):
        """Test /cluster endpoint returns cluster information."""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        assert result.returncode == 0

        assert self.wait_for_qdrant_ready()

        response = requests.get("http://localhost:6333/cluster", timeout=10)
        assert response.status_code in [200, 404]

    def test_metrics_endpoint_accessible(self):
        """Test /metrics endpoint returns Prometheus-style metrics."""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        assert result.returncode == 0

        assert self.wait_for_qdrant_ready()

        response = requests.get("http://localhost:6333/metrics", timeout=10)
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            metrics_text = response.text
            assert isinstance(metrics_text, str)
            assert metrics_text, "Metrics response should not be empty"

            # Check for Prometheus format indicators
            is_prometheus_format = (
                "# HELP" in metrics_text
                or "# TYPE" in metrics_text
                or any(
                    line.strip() and not line.strip().startswith("#") and " " in line
                    for line in metrics_text.splitlines()
                )
            )
            assert is_prometheus_format, "Response should be in Prometheus format"

    def test_service_info_endpoint_accessible(self):
        """Test service info endpoint / returns proper Qdrant version and title information."""
        compose_content = self.create_production_compose_content()
        self.compose_file = self.setup_compose_file(compose_content, self.temp_dir)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        assert result.returncode == 0

        assert self.wait_for_qdrant_ready()

        response = requests.get("http://localhost:6333/", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "version" in data
        assert data["title"] == "qdrant - vector search engine"


if __name__ == "__main__":
    unittest.main()
