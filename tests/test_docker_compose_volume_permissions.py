"""
Volume permission tests for Qdrant Docker Compose
"""

import subprocess
import tempfile
import time
from pathlib import Path

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeVolumePermissions(QdrantDockerComposeTestBase):
    """Volume permission edge case tests"""

    def test_qdrant_volume_permission_errors(self) -> None:
        """Test: Qdrant Volume Mount Permission Errors"""
        with tempfile.TemporaryDirectory() as temp_dir:
            restricted_dir = Path(temp_dir) / "restricted_storage"
            restricted_dir.mkdir()
            restricted_dir.chmod(0o444)

            compose_content = f"""
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_permissions
    ports:
      - "6333:6333"
    volumes:
      - {restricted_dir}:/qdrant/storage
"""

            compose_file = self.setup_compose_file(compose_content, temp_dir)

            try:
                result = self.start_qdrant_service(compose_file, temp_dir)

                if result.returncode == 0:
                    time.sleep(5)
                    logs_result = subprocess.run(
                        ["docker", "logs", "test_qdrant_permissions"],
                        capture_output=True,
                        text=True,
                    )

                    logs_text = logs_result.stdout.lower() + logs_result.stderr.lower()
                    permission_indicators = [
                        "permission",
                        "denied",
                        "access",
                        "cannot write",
                        "read-only",
                    ]
                    self.assertTrue(
                        any(
                            indicator in logs_text
                            for indicator in permission_indicators
                        ),
                        f"Expected permission errors in logs: {logs_text[:500]}",
                    )

            finally:
                try:
                    restricted_dir.chmod(0o755)
                except Exception:
                    pass
                self.stop_qdrant_service(compose_file, temp_dir)
