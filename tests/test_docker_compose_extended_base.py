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

        # Force cleanup any remaining containers
        self.force_cleanup_containers()

        # Wait for port to be available
        self.wait_for_port_available()

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_compose_file_from_dict(self, config: Dict[str, Any]) -> None:
        """Create docker-compose.yml file with given config dictionary."""
        # This method is deprecated - use setup_compose_file with string content instead
        raise NotImplementedError(
            "Use setup_compose_file with string templates instead of config dictionaries"
        )

    def setup_compose_file(self, compose_content: str) -> Path:
        """Setup docker-compose file in temporary directory."""
        self.compose_file.write_text(compose_content)
        return self.compose_file

    def start_qdrant_service(
        self, compose_file: Path, cwd: Path
    ) -> subprocess.CompletedProcess:
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
                response = requests.get("http://localhost:6333/healthz", timeout=5)
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

    def wait_for_port_available(self, port: int = 6333, timeout: int = 10) -> bool:
        """Wait for a port to become available."""
        import socket

        start_time = time.time()
        while time.time() - start_time < timeout:
            # Try to connect to see if port is in use
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(("localhost", port))
                if result != 0:  # Connection failed, port is available
                    return True
            time.sleep(0.5)
        return False

    def force_cleanup_containers(self) -> None:
        """Force cleanup any remaining containers on port 6333."""
        # Stop any containers using port 6333
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "publish=6333", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                container_names = result.stdout.strip().split("\n")
                for name in container_names:
                    subprocess.run(["docker", "stop", name], capture_output=True)
                    subprocess.run(["docker", "rm", name], capture_output=True)
        except Exception:
            pass

    def get_container_restart_count(self, container_name: str) -> int:
        """Get the restart count for a specific container."""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "inspect",
                    container_name,
                    "--format={{.RestartCount}}"
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                restart_count = result.stdout.strip()
                return int(restart_count) if restart_count.isdigit() else 0
            return 0
        except Exception:
            return 0
