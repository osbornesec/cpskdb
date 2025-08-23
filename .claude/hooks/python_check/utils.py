"""
Utility functions for path resolution and project root detection.
"""

import subprocess
from pathlib import Path
from typing import Optional
import os

def find_project_root() -> Optional[Path]:
    """
    Find the project root by searching upwards for a .claude directory.
    The project root is defined as the directory containing the .claude folder.
    """
    current_path = Path(__file__).parent.resolve()
    while current_path != current_path.parent:
        if (current_path / ".claude").exists():
            return current_path
        current_path = current_path.parent
    
    # Final check at the root directory
    if (current_path / ".claude").exists():
        return current_path
    
    # Try git root as a fallback
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(Path(__file__).parent.resolve()),
        )
        if result.returncode == 0:
            git_root = result.stdout.strip()
            if git_root:
                return Path(git_root)
    except Exception:
        pass
    
    return None


def resolve_file_path(file_path: str, project_root: Path) -> Optional[Path]:
    """
    Resolve a file path to an absolute, canonical path, ensuring it's within the project root.
    This function securely handles symlinks and prevents directory traversal.
    Returns the resolved Path object if valid and existing, otherwise None.
    """
    # Create an absolute path from the file_path and project_root
    if os.path.isabs(file_path):
        p = Path(file_path)
    else:
        p = project_root / file_path

    # Get the canonical path, which resolves any symlinks
    try:
        canonical_path = Path(os.path.realpath(p))
    except OSError:  # This can happen if the path is invalid
        return None

    # Ensure the canonical path is within the project root
    if project_root.resolve() not in canonical_path.parents and canonical_path != project_root.resolve():
        return None

    # Final check for existence
    return canonical_path if canonical_path.exists() else None