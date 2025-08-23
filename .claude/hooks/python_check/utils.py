"""
Utility functions for path resolution and project root detection.
"""

import subprocess
from pathlib import Path
from typing import Optional


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
    Resolve a file path to an absolute path, handling relative paths and symlinks.
    Returns None if the file doesn't exist or is outside the project root.
    """
    p = Path(file_path)
    if not p.is_absolute():
        p = project_root / p

    try:
        relative_path = p.relative_to(project_root)
    except ValueError:
        # File is outside project root, check if it's a symlink pointing inside
        if p.is_symlink():
            try:
                resolved_path = p.resolve()
                try:
                    relative_path = resolved_path.relative_to(project_root)
                    p = resolved_path
                except ValueError:
                    return None
            except Exception:
                return None
        else:
            return None

    return p if p.exists() else None
