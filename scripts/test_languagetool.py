#!/usr/bin/env python3
"""
Test script for LanguageTool installation and functionality.
"""

try:
    import language_tool_python  # type: ignore
except ImportError:
    print("LanguageTool not installed. Run: pip install language_tool_python")
    exit(1)


def test_languagetool() -> None:
    """Test LanguageTool with a sample text containing errors."""
    print("Testing LanguageTool...")

    # Test text with intentional errors
    test_text = "A sentence with a error in it. This are another mistake."

    try:
        # Use public API (no Java required)
        tool = language_tool_python.LanguageToolPublicAPI("en-US")
        print(f"Checking text: '{test_text}'")

        matches = tool.check(test_text)

        if matches:
            print(f"Found {len(matches)} issues:")
            for i, match in enumerate(matches, 1):
                print(f"  {i}. {match}")
        else:
            print("No issues found")

    except Exception as e:
        print(f"Error: {e}")
        print("Trying local server mode...")

        try:
            # Fallback to local server (requires Java)
            with language_tool_python.LanguageTool("en-US") as tool:
                matches = tool.check(test_text)

                if matches:
                    print(f"Found {len(matches)} issues:")
                    for i, match in enumerate(matches, 1):
                        print(f"  {i}. {match}")
                else:
                    print("No issues found")

        except Exception as e2:
            print(f"Local server also failed: {e2}")
            print("You may need to install Java for local server mode")


if __name__ == "__main__":
    test_languagetool()
