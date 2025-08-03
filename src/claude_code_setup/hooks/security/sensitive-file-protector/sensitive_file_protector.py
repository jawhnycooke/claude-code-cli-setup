#!/usr/bin/env python3
import json
import os
import re
import sys

# Default sensitive patterns
DEFAULT_SENSITIVE_PATTERNS = [
    r"\.env$",
    r"\.env\.",
    r"\.pem$",
    r"\.key$",
    r"\.cert$",
    r"\.crt$",
    r"\.p12$",
    r"\.pfx$",
    r"id_rsa",
    r"id_dsa",
    r"id_ecdsa",
    r"id_ed25519",
    r"\.ssh/",
    r"\.aws/credentials",
    r"\.aws/config",
    r"\.npmrc",
    r"\.pypirc",
    r"\.gitconfig",
    r"\.netrc",
    r"secrets\.json",
    r"secrets\.yaml",
    r"secrets\.yml",
    r"credentials",
    r"password",
    r"passwd",
    r"shadow",
    r"package-lock\.json$",
    r"yarn\.lock$",
    r"Gemfile\.lock$",
    r"poetry\.lock$",
    r"composer\.lock$",
]


def is_sensitive_file(file_path: str) -> bool:
    """Check if a file path matches sensitive patterns."""
    # Get additional patterns from environment
    extra_patterns = os.environ.get("SENSITIVE_FILE_PATTERNS", "").split(",")
    extra_patterns = [p.strip() for p in extra_patterns if p.strip()]

    all_patterns = DEFAULT_SENSITIVE_PATTERNS + extra_patterns

    for pattern in all_patterns:
        if re.search(pattern, file_path, re.IGNORECASE):
            return True
    return False


def main() -> None:
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)
        tool_input = input_data.get("tool_input", {})
        tool_name = input_data.get("tool_name", "")

        # Get file paths based on tool type
        file_paths = []

        if tool_name in ["Edit", "Write", "Read"]:
            file_path = tool_input.get("file_path", "")
            if file_path:
                file_paths.append(file_path)

        elif tool_name == "MultiEdit":
            file_path = tool_input.get("file_path", "")
            if file_path:
                file_paths.append(file_path)

        elif tool_name == "Bash":
            # Check for sensitive operations in bash commands
            command = tool_input.get("command", "")
            # Look for file operations that might affect sensitive files
            if any(op in command for op in ["cat", "echo", "cp", "mv", "rm"]):
                # Extract potential file paths from command
                # This is a simple heuristic, not perfect
                tokens = command.split()
                for token in tokens:
                    if "/" in token or "." in token:
                        file_paths.append(token)

        # Check each file path
        for file_path in file_paths:
            if is_sensitive_file(file_path):
                print(
                    f"BLOCKED: Attempting to modify sensitive file: {file_path}",
                    file=sys.stderr,
                )
                print(
                    "This file contains sensitive information and should not be modified by AI.",
                    file=sys.stderr,
                )
                sys.exit(2)

        # All checks passed
        sys.exit(0)

    except Exception as e:
        print(f"Hook error: {str(e)}", file=sys.stderr)
        # Allow operation on hook error
        sys.exit(0)


if __name__ == "__main__":
    main()
