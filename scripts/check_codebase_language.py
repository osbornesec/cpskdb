#!/usr/bin/env python3
"""
Run LanguageTool against codebase documentation and comments.
"""

import sys
from pathlib import Path

try:
    import language_tool_python  # type: ignore
except ImportError:
    print("LanguageTool not installed. Run: pip install language_tool_python")
    sys.exit(1)


def extract_comments_from_python(file_path: str) -> list[tuple[str, int]]:
    """Extract comments and docstrings from Python files."""
    comments = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        in_docstring = False
        docstring_delimiter = None

        for i, line in enumerate(lines, 1):
            # Single line comments
            if "#" in line:
                comment_part = line[line.index("#") :].strip("#").strip()
                if comment_part and not comment_part.startswith("!"):
                    comments.append((comment_part, i))

            # Docstrings (simplified detection)
            if '"""' in line or "'''" in line:
                delimiter = '"""' if '"""' in line else "'''"
                if not in_docstring:
                    in_docstring = True
                    docstring_delimiter = delimiter
                    # Extract content after opening delimiter
                    after_delimiter = line.split(delimiter, 1)[1]
                    if delimiter in after_delimiter:  # Single line docstring
                        docstring_content = after_delimiter.split(delimiter)[0].strip()
                        if docstring_content:
                            comments.append((docstring_content, i))
                        in_docstring = False
                elif delimiter == docstring_delimiter:
                    in_docstring = False
                    # Extract content before closing delimiter
                    before_delimiter = line.split(delimiter)[0].strip()
                    if before_delimiter:
                        comments.append((before_delimiter, i))
            elif in_docstring:
                content = line.strip()
                if content:
                    comments.append((content, i))

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return comments


def check_file_with_languagetool(file_path: str, tool) -> list:
    """Check a file with LanguageTool."""
    issues = []

    try:
        if file_path.endswith(".md"):
            # For Markdown files, read entire content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            matches = tool.check(content)
            for match in matches:
                issues.append(
                    {
                        "file": file_path,
                        "line": content[: match.offset].count("\n") + 1,
                        "issue": str(match),
                        "text": content[
                            match.offset : match.offset + match.errorLength
                        ],
                    }
                )

        elif file_path.endswith(".py"):
            # For Python files, check comments and docstrings
            comments = extract_comments_from_python(file_path)
            for comment_text, line_num in comments:
                if len(comment_text.strip()) > 5:  # Skip very short comments
                    matches = tool.check(comment_text)
                    for match in matches:
                        issues.append(
                            {
                                "file": file_path,
                                "line": line_num,
                                "issue": str(match),
                                "text": comment_text[
                                    match.offset : match.offset + match.errorLength
                                ],
                            }
                        )

    except Exception as e:
        print(f"Error checking {file_path}: {e}")

    return issues


def main():
    """Run LanguageTool checks on the codebase."""
    print("Checking codebase with LanguageTool...")

    # Initialize LanguageTool (use local server only)
    tool = None
    try:
        tool = language_tool_python.LanguageTool("en-US")
        print("Using LanguageTool local server")
    except Exception as e:
        print(f"Failed to initialize LanguageTool: {e}")
        print("Make sure Java is installed for local LanguageTool server")
        return

    # Find files to check
    root_path = Path(".")
    files_to_check = []

    # Add all Markdown files (excluding hidden directories and cache)
    for md_file in root_path.glob("**/*.md"):
        # Skip hidden directories and cache directories
        if not any(part.startswith(".") for part in md_file.parts):
            files_to_check.append(str(md_file))

    # Add all Python files (excluding hidden directories and cache)
    for py_file in root_path.glob("**/*.py"):
        # Skip hidden directories and cache directories
        if not any(part.startswith(".") for part in py_file.parts):
            files_to_check.append(str(py_file))

    if not files_to_check:
        print("No files found to check")
        return

    print(f"Checking {len(files_to_check)} files...")

    all_issues = []
    for file_path in files_to_check:
        print(f"Checking {file_path}...")
        issues = check_file_with_languagetool(file_path, tool)
        all_issues.extend(issues)

    # Report results
    if all_issues:
        print(f"\nFound {len(all_issues)} language issues:")
        print("=" * 60)

        current_file = ""
        for issue in sorted(all_issues, key=lambda x: (x["file"], x["line"])):
            if issue["file"] != current_file:
                current_file = issue["file"]
                print(f"\n📁 {current_file}")
                print("-" * 40)

            print(f"Line {issue['line']}: {issue['issue']}")
            if issue["text"]:
                print(f"  Text: '{issue['text']}'")
            print()
    else:
        print("\n✅ No language issues found!")

    # Close tool if it's a local instance
    if hasattr(tool, "close"):
        tool.close()


if __name__ == "__main__":
    main()
