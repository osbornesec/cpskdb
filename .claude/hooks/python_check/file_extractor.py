"""File path extraction from tool inputs and responses."""

from typing import Any

from .config import FILE_MODIFICATION_TOOLS, MARKDOWN_EXTENSIONS, PYTHON_EXTENSIONS


def _extract_paths_from_payload(payload: Any) -> list[str]:
    """Recursively extract file paths from tool payload."""
    paths: list[str] = []
    if payload is None:
        return paths

    # Strings
    if isinstance(payload, str):
        paths.append(payload)
        return paths

    # Lists
    if isinstance(payload, list):
        for item in payload:
            paths.extend(_extract_paths_from_payload(item))
        return paths

    # Dicts
    if isinstance(payload, dict):
        candidate_keys = [
            "file_path",
            "path",
            "file",
            "newPath",
            "oldPath",
            "to",
            "from",
            "target",
            "source",
        ]
        list_like_keys = ["files", "file_paths", "paths", "edits", "changes", "patches"]

        for k in candidate_keys:
            if k in payload:
                paths.extend(_extract_paths_from_payload(payload[k]))

        for k in list_like_keys:
            if k in payload:
                paths.extend(_extract_paths_from_payload(payload[k]))

        return paths

    return paths


def get_modified_files(
    tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]
) -> tuple[list[str], list[str]]:
    """Extract file paths that were modified from tool input/response."""
    files: list[str] = []

    if tool_name in FILE_MODIFICATION_TOOLS:
        # Standard file modification tools – collect from known shapes
        files.extend(_extract_paths_from_payload(tool_input))
        files.extend(_extract_paths_from_payload(tool_response))

    # Dedup and keep order roughly
    seen: set[str] = set()
    deduped: list[str] = []
    for f in files:
        if not isinstance(f, str):
            continue
        f = f.strip()
        if not f:
            continue
        if f not in seen:
            seen.add(f)
            deduped.append(f)

    # Separate Python and Markdown-like files
    python_files = [f for f in deduped if f.endswith(PYTHON_EXTENSIONS)]
    markdown_files = [f for f in deduped if f.endswith(MARKDOWN_EXTENSIONS)]

    return python_files, markdown_files
