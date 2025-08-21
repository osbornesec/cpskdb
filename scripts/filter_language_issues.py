#!/usr/bin/env python3
"""
Filter LanguageTool results to focus on actual writing issues.
"""

import sys
from pathlib import Path

try:
    import language_tool_python  # type: ignore
except ImportError:
    print("LanguageTool not installed. Run: pip install language_tool_python")
    sys.exit(1)


def is_technical_term(text: str) -> bool:
    """Check if text is likely a technical term that should be ignored."""
    technical_terms = {
        "fastapi",
        "langraph",
        "qdrant",
        "redis",
        "ollama",
        "reranking",
        "rerankers",
        "postgresql",
        "cohere",
        "voyage",
        "uvicorn",
        "gunicorn",
        "pydantic",
        "pytest",
        "api",
        "apis",
        "cpu",
        "gpu",
        "json",
        "yaml",
        "yml",
        "csv",
        "sql",
        "http",
        "https",
        "url",
        "uri",
        "cli",
        "gui",
        "uuid",
        "jwt",
        "oauth",
        "tdd",
        "ci",
        "cd",
        "mcp",
        "llm",
        "ml",
        "ai",
        "rag",
        "embeddings",
        "vectorstore",
        "chunking",
        "nodejs",
        "javascript",
        "typescript",
        "python",
        "dockerfile",
        "kubernetes",
        "docker",
        "containerization",
        "microservices",
    }
    return text.lower().strip() in technical_terms


def should_ignore_rule(rule_id: str, message: str, text: str) -> bool:
    """Determine if a LanguageTool rule should be ignored."""
    # Ignore spelling mistakes for technical terms
    if rule_id == "MORFOLOGIK_RULE_EN_US" and is_technical_term(text):
        return True

    # Ignore whitespace issues in code blocks
    if rule_id == "WHITESPACE_RULE":
        return True

    # Ignore comma/parenthesis whitespace in code blocks
    if rule_id == "COMMA_PARENTHESIS_WHITESPACE":
        return True

    # Ignore very short text snippets (likely code)
    if len(text.strip()) <= 3:
        return True

    return False


def check_text_filtered(text: str, tool, file_path: str = "") -> list:
    """Check text with LanguageTool and filter results."""
    try:
        matches = tool.check(text)
        filtered_issues = []

        for match in matches:
            error_text = text[match.offset : match.offset + match.errorLength]

            if not should_ignore_rule(match.ruleId, match.message, error_text):
                filtered_issues.append(
                    {
                        "file": file_path,
                        "line": text[: match.offset].count("\n") + 1,
                        "rule_id": match.ruleId,
                        "message": match.message,
                        "text": error_text,
                        "suggestions": match.replacements[:3],  # Top 3 suggestions
                        "context": text[
                            max(0, match.offset - 20) : match.offset
                            + match.errorLength
                            + 20
                        ].strip(),
                    }
                )

        return filtered_issues
    except Exception as e:
        print(f"Error checking text: {e}")
        return []


def main():
    """Run filtered LanguageTool check on main documentation."""
    print("Running filtered LanguageTool check...")

    # Initialize LanguageTool
    try:
        tool = language_tool_python.LanguageTool("en-US")
        print("Using LanguageTool local server")
    except Exception as e:
        print(f"Failed to initialize LanguageTool: {e}")
        return

    # Check main documentation files
    files_to_check = ["README.md", "CLAUDE.md"]
    all_issues = []

    for file_path in files_to_check:
        if not Path(file_path).exists():
            continue

        print(f"Checking {file_path}...")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            issues = check_text_filtered(content, tool, file_path)
            all_issues.extend(issues)

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    # Report filtered results
    if all_issues:
        print(f"\nFound {len(all_issues)} significant language issues:")
        print("=" * 60)

        for issue in sorted(all_issues, key=lambda x: (x["file"], x["line"])):
            print(f"\n📁 {issue['file']} (Line {issue['line']})")
            print(f"Rule: {issue['rule_id']}")
            print(f"Issue: {issue['message']}")
            print(f"Text: '{issue['text']}'")
            if issue["suggestions"]:
                suggestions = ", ".join(issue["suggestions"])
                print(f"Suggestions: {suggestions}")
            print(f"Context: ...{issue['context']}...")
            print("-" * 40)
    else:
        print("\n✅ No significant language issues found!")

    tool.close()


if __name__ == "__main__":
    main()
