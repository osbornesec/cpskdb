"""
File size validation and line counting utilities.
"""

from pathlib import Path
from typing import List
from .config import MAX_LINES_OF_CODE, get_bool_env


def count_lines_of_code(file_path: str) -> int:
    """Count lines of code excluding comments and empty lines."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        code_lines = 0
        in_multiline_string = False
        string_delimiter = None

        for line in lines:
            line_to_process = line.strip()
            if not line_to_process:
                continue

            while True:
                if in_multiline_string:
                    delimiter_pos = line_to_process.find(string_delimiter)
                    if delimiter_pos != -1:
                        in_multiline_string = False
                        string_delimiter = None
                        line_to_process = line_to_process[delimiter_pos + 3 :]
                        if not line_to_process.strip():
                            break
                    else:
                        break  # Whole line is inside multiline string

                if line_to_process.startswith("#"):
                    break

                if '"""' in line_to_process or "'''" in line_to_process:
                    delimiter = '"""' if '"""' in line_to_process else "'''"
                    if line_to_process.count(delimiter) % 2 == 1:
                        in_multiline_string = True
                        string_delimiter = delimiter
                        # Process part of the line before the multiline string
                        line_to_process = line_to_process.split(delimiter)[0]

                if line_to_process.strip():
                    code_lines += 1
                break

        return code_lines
    except Exception:
        return 0  # Return 0 if file can't be read


def validate_file_size(file_path: str) -> List[str]:
    """Validate that file doesn't exceed maximum lines of code."""
    errors: List[str] = []

    if not Path(file_path).exists():
        return errors

    if get_bool_env("SKIP_SIZE_CHECK", False):
        return errors

    line_count = count_lines_of_code(file_path)
    if line_count > MAX_LINES_OF_CODE:
        errors.append(
            f"File size violation: {file_path} has {line_count} LOC "
            f"(max: {MAX_LINES_OF_CODE}). Please split this file into smaller, more manageable modules."
        )

    return errors
