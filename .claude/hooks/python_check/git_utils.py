"""
Git auto-commit functionality for safety backups.
"""

import subprocess
import sys
from pathlib import Path
from typing import List
from .config import GIT_TIMEOUT
from .utils import find_project_root, resolve_file_path


def auto_commit_changes(modified_files: List[str], tool_name: str) -> None:
    """Automatically commit file changes to git for safety."""
    try:
        project_root = find_project_root()
        if not project_root:
            return  # Could not find project root

        # Check if we're in a git repository
        git_check = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            cwd=str(project_root),
            timeout=GIT_TIMEOUT,
        )
        if git_check.returncode != 0:
            return  # Not a git repository, skip commit

        # Stage the modified files
        staged_files = []
        for file_path in modified_files:
            resolved_path = resolve_file_path(file_path, project_root)
            if not resolved_path:
                continue

            try:
                relative_path = resolved_path.relative_to(project_root)
            except ValueError:
                continue

            stage_result = subprocess.run(
                ["git", "add", str(relative_path)],
                capture_output=True,
                cwd=str(project_root),
                timeout=GIT_TIMEOUT,
            )
            if stage_result.returncode == 0:
                staged_files.append(str(relative_path))

        if not staged_files:
            return  # No files successfully staged

        # Check if there are any staged changes
        status_check = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            capture_output=True,
            cwd=str(project_root),
            timeout=GIT_TIMEOUT,
        )
        if status_check.returncode == 0:
            return  # No changes to commit

        # Create commit message
        file_list = ', '.join(staged_files)
        # Truncate file list if too long
        if len(file_list) > 100:
            file_list = file_list[:97] + "..."
        
        commit_lines = [
            f"chore: auto-save changes from {tool_name}",
            "",
            "Automatic safety commit after file modification via post-tool hook.",
            f"Tool: {tool_name}",
            f"Files: {file_list}",
        ]
        commit_message = "\n".join(commit_lines)

        subprocess.run(
            ["git", "commit", "-m", commit_message],
            capture_output=True,
            cwd=str(project_root),
            timeout=GIT_TIMEOUT,
        )

    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"Git commit skipped due to error: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Unexpected error during git commit: {e}", file=sys.stderr)
