"""
Tests for Qdrant Docker Compose network and configuration edge cases.

This module implements network, port, volume, and configuration-specific edge cases.
"""

from tests.test_docker_compose_extended_base import QdrantDockerComposeExtendedTestBase


class TestQdrantDockerComposeNetworkEdgeCases(QdrantDockerComposeExtendedTestBase):
    """Network and configuration edge cases for Qdrant Docker Compose."""

    def test_volume_mount_with_complex_paths(self):
        """Test Docker Compose with complex volume mount paths."""
        # Create nested directory structure
        complex_path = (
            self.temp_dir / "very" / "nested" / "path with spaces" / "qdrant_data"
        )
        complex_path.mkdir(parents=True, exist_ok=True)

        compose_content = f"""
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant-test
    ports:
      - "6333:6333"
    volumes:
      - "{complex_path}:/qdrant/storage"
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__LOG_LEVEL=INFO
"""

        self.setup_compose_file(compose_content)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

    def test_docker_compose_version_compatibility(self):
        """Test Docker Compose file with different version specifications."""
        # Test with explicit version (legacy format)
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant-test
    ports:
      - "6333:6333"
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__LOG_LEVEL=INFO
"""

        self.setup_compose_file(compose_content)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

    def test_network_configuration_edge_cases(self):
        """Test Docker Compose network configurations edge cases."""
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant-test
    ports:
      - "6333:6333"
    networks:
      custom-network:
        ipv4_address: "172.20.0.100"
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__LOG_LEVEL=INFO

networks:
  custom-network:
    driver: bridge
    ipam:
      config:
        - subnet: "172.20.0.0/16"
"""

        self.setup_compose_file(compose_content)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

    def test_port_binding_edge_cases(self):
        """Test Docker Compose port binding edge cases."""
        # Test binding to specific interface
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant-test
    ports:
      - "127.0.0.1:6333:6333"  # Bind only to localhost
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__LOG_LEVEL=INFO
"""

        self.setup_compose_file(compose_content)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

    def test_log_configuration_edge_cases(self):
        """Test Docker Compose logging configurations edge cases."""
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant-test
    ports:
      - "6333:6333"
    logging:
      driver: json-file
      options:
        max-size: "1k"  # Extremely small log size
        max-file: "1"   # Only one log file
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__LOG_LEVEL=DEBUG  # Generate lots of logs
"""

        self.setup_compose_file(compose_content)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

    def test_docker_compose_tmpfs_edge_cases(self):
        """Test Docker Compose tmpfs mount configurations edge cases."""
        compose_content = """
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant-test
    ports:
      - "6333:6333"
    tmpfs:
      - /tmp:size=10M,noexec  # Small tmpfs with restrictions
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__LOG_LEVEL=INFO
"""

        self.setup_compose_file(compose_content)
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())
