"""
Base class for extended Docker Compose edge case tests.

This module provides common functionality for all extended edge case test modules.
"""

import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from typing import Any, Dict

import requests  # type: ignore
import yaml


class QdrantDockerComposeExtendedTestBase(unittest.TestCase):
    """Base class for extended Qdrant Docker Compose edge case tests."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.compose_file = self.temp_dir / "docker-compose.yml"

    def tearDown(self):
        """Clean up test environment."""
        try:
            subprocess.run(
                ["docker", "compose", "-f", str(self.compose_file), "down", "-v"],
                capture_output=True,
                cwd=self.temp_dir,
            )
        except Exception:
            pass
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_compose_file(self, config: Dict[str, Any]) -> None:
        """Create docker-compose.yml file with given config."""
        with open(self.compose_file, "w") as f:
            yaml.dump(config, f)

    def start_qdrant_service(self, compose_file: Path, cwd: Path) -> subprocess.CompletedProcess:
        """Start Qdrant service using Docker Compose."""
        return subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "up", "-d"],
            capture_output=True,
            cwd=cwd,
        )

    def wait_for_qdrant_ready(self, timeout: int = 30) -> bool:
        """Wait for Qdrant to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get("http://localhost:6333/health", timeout=5)
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                pass
            time.sleep(1)
        return False

    def verify_collection_exists(self, collection_name: str) -> bool:
        """Verify that a collection exists in Qdrant."""
        try:
            response = requests.get(
                f"http://localhost:6333/collections/{collection_name}",
                timeout=5,
            )
            return response.status_code == 200
        except requests.RequestException:
            return False