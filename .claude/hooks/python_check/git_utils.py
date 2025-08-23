"""
Git auto-commit functionality for safety backups.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple, Union
from .config import GIT_TIMEOUT
from .utils import find_project_root, resolve_file_path

# Constants
MAX_FILE_LIST_LENGTH = 100
FILE_LIST_TRUNCATE_LENGTH = 97
GIT_COMMAND_TIMEOUT = GIT_TIMEOUT


def run_git_command(
    args: List[str], 
    project_root: Path, 
    capture_output: bool = True
) -> subprocess.CompletedProcess:
    """Run a git command with consistent parameters.
    
    Args:
        args: Git command arguments
        project_root: Project root directory path
        capture_output: Whether to capture command output
        
    Returns:
        CompletedProcess result from subprocess.run
    """
    return subprocess.run(
        args,
        capture_output=capture_output,
        cwd=str(project_root),
        timeout=GIT_COMMAND_TIMEOUT,
    )


def validate_git_repo() -> Optional[Path]:
    """Validate git repository and return project root.
    
    Returns:
        Path to project root if valid git repo, None otherwise
    """
    project_root = find_project_root()
    if not project_root:
        return None  # Could not find project root

    # Check if we're in a git repository
    git_check = run_git_command(["git", "rev-parse", "--git-dir"], project_root)
    if git_check.returncode != 0:
        return None  # Not a git repository, skip commit
        
    return project_root


def stage_modified_files(modified_files: List[str], project_root: Path) -> Tuple[List[str], bool]:
    """Stage modified files and verify there are changes to commit.
    
    Args:
        modified_files: List of file paths to stage
        project_root: Project root directory path
        
    Returns:
        Tuple of (staged_files, has_changes) where staged_files is list of 
        successfully staged relative paths and has_changes indicates if there
        are staged changes to commit
    """
    if not modified_files:
        return [], False
    
    staged_files = []
    for file_path in modified_files:
        resolved_path = resolve_file_path(file_path, project_root)
        if not resolved_path:
            continue

        try:
            relative_path = resolved_path.relative_to(project_root)
        except ValueError:
            continue

        stage_result = run_git_command(["git", "add", str(relative_path)], project_root)
        if stage_result.returncode == 0:
            staged_files.append(str(relative_path))
        else:
            # Log git add failure with context and command output
            stderr_output = stage_result.stderr.decode('utf-8', errors='replace') if stage_result.stderr else "No stderr output"
            stdout_output = stage_result.stdout.decode('utf-8', errors='replace') if stage_result.stdout else "No stdout output"
            print(
                f"Git add failed for {relative_path} (exit code: {stage_result.returncode}):\n"
                f"stderr: {stderr_output}\n"
                f"stdout: {stdout_output}",
                file=sys.stderr
            )

    if not staged_files:
        return [], False  # No files successfully staged

    # Check if there are any staged changes
    status_check = run_git_command(["git", "diff", "--cached", "--quiet"], project_root)
    has_changes = status_check.returncode != 0
    
    return staged_files, has_changes


def build_commit_message(tool_name: str, staged_files: List[str]) -> str:
    """Build commit message for auto-save commit.
    
    Args:
        tool_name: Name of the tool that triggered the commit
        staged_files: List of successfully staged file paths
        
    Returns:
        Formatted commit message string
    """
    if not staged_files:
        return ""
        
    file_list = ", ".join(staged_files)
    # Truncate file list if too long
    if len(file_list) > MAX_FILE_LIST_LENGTH:
        file_list = file_list[:FILE_LIST_TRUNCATE_LENGTH] + "..."

    commit_lines = [
        f"chore: auto-save changes from {tool_name}",
        "",
        "Automatic safety commit after file modification via post-tool hook.",
        f"Tool: {tool_name}",
        f"Files: {file_list}",
    ]
    return "\n".join(commit_lines)


def execute_commit(commit_message: str, project_root: Path) -> bool:
    """Execute the git commit command.
    
    Args:
        commit_message: Commit message to use
        project_root: Project root directory path
        
    Returns:
        True if commit was successful, False otherwise
    """
    if not commit_message:
        return False
        
    commit_result = run_git_command(
        ["git", "commit", "-m", commit_message], 
        project_root
    )
    return commit_result.returncode == 0


def auto_commit_changes(modified_files: List[str], tool_name: str) -> None:
    """Automatically commit file changes to git for safety."""
    try:
        # Validate git repository
        project_root = validate_git_repo()
        if not project_root:
            return  # Could not find project root or not a git repo

        # Stage modified files and check for changes
        staged_files, has_changes = stage_modified_files(modified_files, project_root)
        if not has_changes:
            return  # No changes to commit

        # Build and execute commit
        commit_message = build_commit_message(tool_name, staged_files)
        if not execute_commit(commit_message, project_root):
            print("Git commit failed", file=sys.stderr)

    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"Git commit skipped due to error: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Unexpected error during git commit: {e}", file=sys.stderr)
