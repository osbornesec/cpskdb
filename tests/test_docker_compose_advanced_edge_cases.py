"""
Storage recovery tests for Qdrant Docker Compose
"""

import subprocess
import tempfile
import time
from pathlib import Path

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeStorageRecovery(QdrantDockerComposeTestBase):
    """Storage recovery edge case tests"""

    def test_qdrant_recovery_from_temporary_storage_issues(self) -> None:
        """Test: Qdrant Recovers from Temporary Storage Issues"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_dir = Path(temp_dir) / "qdrant_storage"
            storage_dir.mkdir()

            compose_content = f"""
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_storage_recovery
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    volumes:
      - {storage_dir}:/qdrant/storage
    restart: unless-stopped
"""

            compose_file = self.setup_compose_file(compose_content, temp_dir)

            try:
                result = self.start_qdrant_service(compose_file, temp_dir)
                self.assertEqual(
                    result.returncode, 0, f"Docker compose failed: {result.stderr}"
                )

                self.assertTrue(
                    self.wait_for_qdrant_ready(), "Qdrant service not ready"
                )
                self.create_test_collection("recovery_test")

                original_perms = storage_dir.stat().st_mode
                storage_dir.chmod(0o444)

                # Wait for container to detect permission change
                start_time = time.monotonic()
                timeout = 10
                while time.monotonic() - start_time < timeout:
                    # Check if container can detect the permission issue
                    logs_result = subprocess.run(
                        [
                            "docker",
                            "logs",
                            "--tail",
                            "20",
                            "test_qdrant_storage_recovery",
                        ],
                        capture_output=True,
                        text=True,
                        cwd=temp_dir,
                    )
                    if (
                        "permission" in logs_result.stdout.lower()
                        or "access" in logs_result.stdout.lower()
                    ):
                        break
                    time.sleep(0.5)

                storage_dir.chmod(original_perms)

                # Wait for container to recover
                start_time = time.monotonic()
                while time.monotonic() - start_time < timeout:
                    try:
                        if self.wait_for_qdrant_ready():
                            break
                    except Exception:
                        pass
                    time.sleep(0.5)

                self.assert_qdrant_healthy()
                self.verify_collection_exists("recovery_test")

            finally:
                try:
                    storage_dir.chmod(0o755)
                except Exception:
                    pass
                self.stop_qdrant_service(compose_file, temp_dir)
