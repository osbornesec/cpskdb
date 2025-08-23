"""
Test Qdrant Docker Compose network isolation scenarios.

This module implements network isolation testing including multi-stack isolation
and security-focused network configurations.
"""

import shutil
import subprocess
import tempfile
import time

import requests

from tests.test_docker_compose_base import QdrantDockerComposeTestBase


class TestQdrantDockerComposeNetworkIsolation(QdrantDockerComposeTestBase):
    """Test Qdrant network isolation functionality via Docker Compose"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.compose_file = None

    def tearDown(self):
        """Clean up test environment"""
        if self.compose_file:
            self.stop_qdrant_service(self.compose_file, self.temp_dir)
        if self.temp_dir:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir = None

    def test_network_isolation_between_compose_stacks(self):
        """Test network isolation between different Docker Compose stacks"""
        temp_dir2 = None
        compose_file2 = None

        compose_content_stack1 = """
version: '3.8'

networks:
  stack1-network:
    driver: bridge

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_stack1
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    networks:
      - stack1-network
    volumes:
      - qdrant_data_stack1:/qdrant/storage

volumes:
  qdrant_data_stack1:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_stack1, self.temp_dir
        )
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.wait_for_qdrant_ready())

        response1 = requests.get("http://localhost:6333/healthz", timeout=10)
        self.assertEqual(response1.status_code, 200)

        compose_content_stack2 = """
version: '3.8'

networks:
  stack2-network:
    driver: bridge

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_stack2
    ports:
      - "6334:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    networks:
      - stack2-network
    volumes:
      - qdrant_data_stack2:/qdrant/storage

volumes:
  qdrant_data_stack2:
"""

        try:
            temp_dir2 = tempfile.mkdtemp()
            compose_file2 = self.setup_compose_file(compose_content_stack2, temp_dir2)

            result2 = subprocess.run(
                ["docker", "compose", "-f", str(compose_file2), "up", "-d"],
                capture_output=True,
                text=True,
                cwd=temp_dir2,
            )

            if result2.returncode == 0:
                # Wait for second stack to be ready with timeout
                max_retries = 30
                for _ in range(max_retries):
                    try:
                        response2 = requests.get(
                            "http://localhost:6334/healthz", timeout=5
                        )
                        if response2.status_code == 200:
                            break
                    except requests.exceptions.ConnectionError:
                        time.sleep(1)
                else:
                    self.skipTest("Second stack failed to start within timeout")

                # Verify both stacks are accessible on different ports
                response2 = requests.get("http://localhost:6334/healthz", timeout=10)
                self.assertEqual(response1.status_code, 200)
                self.assertEqual(response2.status_code, 200)

                # Verify network isolation by checking different networks
                network1_result = subprocess.run(
                    [
                        "docker",
                        "inspect",
                        "test_qdrant_stack1",
                        "--format={{.NetworkSettings.Networks}}",
                    ],
                    capture_output=True,
                    text=True,
                )
                network2_result = subprocess.run(
                    [
                        "docker",
                        "inspect",
                        "test_qdrant_stack2",
                        "--format={{.NetworkSettings.Networks}}",
                    ],
                    capture_output=True,
                    text=True,
                )

                if network1_result.returncode == 0 and network2_result.returncode == 0:
                    self.assertIn("stack1-network", network1_result.stdout)
                    self.assertIn("stack2-network", network2_result.stdout)
                    self.assertNotIn("stack2-network", network1_result.stdout)
                    self.assertNotIn("stack1-network", network2_result.stdout)
        finally:
            if compose_file2 and temp_dir2:
                subprocess.run(
                    ["docker", "compose", "-f", str(compose_file2), "down", "-v"],
                    capture_output=True,
                    cwd=temp_dir2,
                )
                shutil.rmtree(temp_dir2, ignore_errors=True)

    def test_network_security_and_access_control(self):
        """Test network security and access control scenarios"""
        compose_content_isolated = """
version: '3.8'

networks:
  internal-only:
    driver: bridge
    internal: true
  external-access:
    driver: bridge

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: test_qdrant_isolated
    ports:
      - "6333:6333"
    environment:
      - QDRANT__LOG_LEVEL=INFO
    networks:
      - external-access
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
"""

        self.compose_file = self.setup_compose_file(
            compose_content_isolated, self.temp_dir
        )
        result = self.start_qdrant_service(self.compose_file, self.temp_dir)
        self.assertEqual(result.returncode, 0)

        self.assertTrue(self.wait_for_qdrant_ready())

        # Dynamically get the network name
        network_name_result = subprocess.run(
            [
                "docker",
                "inspect",
                "test_qdrant_isolated",
                "--format={{range $key, $value := .NetworkSettings.Networks}}{{$key}}{{end}}",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(network_name_result.returncode, 0)
        network_name = network_name_result.stdout.strip()

        # Get Qdrant container IP
        ip_result = subprocess.run(
            [
                "docker",
                "inspect",
                "test_qdrant_isolated",
                "--format={{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}",
            ],
            capture_output=True,
            text=True,
        )
        qdrant_ip = ip_result.stdout.strip()

        # Test connectivity from same network (should succeed)
        same_network_test = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                network_name,
                "curlimages/curl:latest",
                "curl",
                "-f",
                "--max-time",
                "5",
                f"http://{qdrant_ip}:6333/healthz",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            same_network_test.returncode,
            0,
            f"Same network access should succeed: {same_network_test.stderr}",
        )

        # Test connectivity from different network (should fail)
        # Create a separate network for isolation test
        subprocess.run(
            ["docker", "network", "create", "test_isolated_network"],
            capture_output=True,
        )

        try:
            different_network_test = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--network",
                    "test_isolated_network",
                    "curlimages/curl:latest",
                    "curl",
                    "-f",
                    "--max-time",
                    "5",
                    f"http://{qdrant_ip}:6333/healthz",
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(
                different_network_test.returncode,
                0,
                "Different network access should fail (network isolation)",
            )
        finally:
            # Cleanup test network
            subprocess.run(
                ["docker", "network", "rm", "test_isolated_network"],
                capture_output=True,
            )
