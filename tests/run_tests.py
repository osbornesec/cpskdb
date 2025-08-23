#!/usr/bin/env python3
"""
Test runner for Qdrant Docker Compose tests.

This script provides an easy way to run all tests or specific test categories.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_tests(test_pattern=None, verbose=False, coverage=False):
    """Run the test suite with optional filtering and coverage."""
    
    # Change to the project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=tests", "--cov-report=html", "--cov-report=term"])
    
    # Add test directory
    cmd.append("tests/")
    
    # Add test pattern if specified
    if test_pattern:
        cmd.append(f"-k {test_pattern}")
    
    # Add additional pytest options
    cmd.extend([
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker checking
        "--disable-warnings",  # Disable warnings for cleaner output
    ])
    
    print(f"Running tests with command: {' '.join(cmd)}")
    print(f"Project root: {project_root}")
    print("-" * 80)
    
    # Run the tests
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def run_specific_test_category(category):
    """Run tests for a specific category."""
    categories = {
        "basic": "test_docker_compose_basic.py",
        "api": "test_docker_compose_api_endpoints.py",
        "network": "test_docker_compose_network",
        "performance": "test_docker_compose_performance",
        "errors": "test_docker_compose_errors.py",
        "edge_cases": "test_docker_compose_edge_cases.py",
        "integration": "test_docker_compose_integration.py",
        "ci": "test_docker_compose_ci_restart_policy.py",
        "missing": "test_docker_compose_missing_scenarios.py",
        "all": None
    }
    
    if category not in categories:
        print(f"Unknown category: {category}")
        print(f"Available categories: {', '.join(categories.keys())}")
        return 1
    
    if category == "all":
        return run_tests()
    
    test_file = categories[category]
    if test_file:
        return run_tests(test_file)
    else:
        # For categories that span multiple files, use pattern matching
        return run_tests(category)


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description="Run Qdrant Docker Compose tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_tests.py                    # Run all tests
  python tests/run_tests.py --category basic  # Run basic functionality tests
  python tests/run_tests.py --pattern "health" # Run tests with "health" in name
  python tests/run_tests.py --verbose          # Run with verbose output
  python tests/run_tests.py --coverage         # Run with coverage report
        """
    )
    
    parser.add_argument(
        "--category", "-c",
        choices=["basic", "api", "network", "performance", "errors", "edge_cases", "integration", "ci", "missing", "all"],
        help="Run tests for a specific category"
    )
    
    parser.add_argument(
        "--pattern", "-k",
        help="Run tests matching the given pattern"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Run tests with verbose output"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List available test categories"
    )
    
    args = parser.parse_args()
    
    if args.list_categories:
        print("Available test categories:")
        print("  basic      - Basic functionality tests")
        print("  api        - API endpoint tests")
        print("  network    - Network configuration tests")
        print("  performance - Performance and resource tests")
        print("  errors     - Error handling tests")
        print("  edge_cases - Edge case tests")
        print("  integration - Integration tests")
        print("  ci         - CI-specific restart policy tests")
        print("  missing    - Previously missing test scenarios")
        print("  all        - All tests (default)")
        return 0
    
    # Check if Docker is available
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Docker is not available or not running")
        print("Please ensure Docker is installed and running before running tests")
        return 1
    
    # Check if Docker Compose is available
    try:
        subprocess.run(["docker", "compose", "version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Docker Compose is not available")
        print("Please ensure Docker Compose is installed and available")
        return 1
    
    # Run tests based on arguments
    if args.category:
        return run_specific_test_category(args.category)
    elif args.pattern:
        return run_tests(test_pattern=args.pattern, verbose=args.verbose, coverage=args.coverage)
    else:
        return run_tests(verbose=args.verbose, coverage=args.coverage)


if __name__ == "__main__":
    import os
    sys.exit(main())
