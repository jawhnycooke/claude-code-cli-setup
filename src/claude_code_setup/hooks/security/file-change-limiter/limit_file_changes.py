#!/usr/bin/env python3
import json
import os
import sys

# Configuration from environment or defaults
MAX_FILES_PER_OPERATION = int(os.environ.get("MAX_FILES_PER_OPERATION", "3"))
MAX_LINES_PER_FILE = int(os.environ.get("MAX_LINES_PER_FILE", "100"))


def main() -> None:
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)
        tool_input = input_data.get("tool_input", {})
        tool_name = input_data.get("tool_name", "")

        # Handle different tool types
        if tool_name in ["Edit", "Write"]:
            # Single file operations
            file_paths = [tool_input.get("file_path", "")]

            # Check content size for Write operations
            if tool_name == "Write" and "content" in tool_input:
                line_count = len(tool_input["content"].split("\n"))
                if line_count > MAX_LINES_PER_FILE:
                    print(
                        f"BLOCKED: File too large ({line_count} lines). Maximum {MAX_LINES_PER_FILE} lines.",
                        file=sys.stderr,
                    )
                    sys.exit(2)

        elif tool_name == "MultiEdit":
            # Multiple file operations
            file_paths = [tool_input.get("file_path", "")]

            # Check edits
            edits = tool_input.get("edits", [])
            for edit in edits:
                if "new_string" in edit:
                    line_count = len(edit["new_string"].split("\n"))
                    if line_count > MAX_LINES_PER_FILE:
                        print(
                            f"BLOCKED: Edit too large ({line_count} lines). Maximum {MAX_LINES_PER_FILE} lines per edit.",
                            file=sys.stderr,
                        )
                        sys.exit(2)
        else:
            # Tool doesn't modify files, allow it
            sys.exit(0)

        # Count unique files being modified
        unique_files = list(set(filter(None, file_paths)))

        if len(unique_files) > MAX_FILES_PER_OPERATION:
            print(
                f"BLOCKED: Too many files ({len(unique_files)}). Maximum {MAX_FILES_PER_OPERATION} files per operation.",
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
