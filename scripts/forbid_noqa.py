#!/usr/bin/env python3
"""Pre-commit hook: forbid any usage of `# noqa` in Python files.

Exits with non-zero if any Python source line contains a `# noqa` directive.
This enforces fixing the underlying issue instead of silencing linters.
"""

from __future__ import annotations

import sys
from pathlib import Path


def check_file(path: Path) -> list[str]:
    """Return a list of violation messages for a given Python file path."""
    messages: list[str] = []
    try:
        with path.open("r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, start=1):
                # Case-insensitive match to catch any inline linter-ignore directive
                if "# noqa" in line.lower():
                    messages.append(
                        f"{path}:{lineno}: 'noqa' is not allowed; fix the code or adjust linter config."
                    )
    except FileNotFoundError:
        # File might have been deleted between staging and hook run; ignore.
        return messages
    return messages


def main(argv: list[str]) -> int:
    """Entry point: check provided files and report any 'noqa' occurrences.

    Pre-commit passes a list of file paths as arguments.
    This function filters to Python files and scans for forbidden directives.
    """
    violations: list[str] = []
    for arg in argv[1:]:
        p = Path(arg)
        if p.suffix != ".py":
            continue
        violations.extend(check_file(p))

    if violations:
        sys.stderr.write("\n".join(violations) + "\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
