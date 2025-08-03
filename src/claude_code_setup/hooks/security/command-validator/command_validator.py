#!/usr/bin/env python3
import json
import os
import re
import sys

# Dangerous command patterns
DANGEROUS_PATTERNS = [
    # Destructive file operations
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+\*",
    r"rm\s+-f\s+/",
    r":\s*>\s*/",  # Truncating root files
    # System modifications
    r"chmod\s+777",
    r"chmod\s+-R\s+777",
    r"chown\s+-R\s+root",
    # Package manager dangers
    r"npm\s+install.*--force",
    r"pip\s+install.*--force-reinstall.*--no-deps",
    r"apt-get\s+install.*-y.*--force-yes",
    # Dangerous downloads
    r"curl.*\|\s*sh",
    r"wget.*\|\s*sh",
    r"curl.*\|\s*bash",
    r"wget.*\|\s*bash",
    # Cryptocurrency mining
    r"xmrig",
    r"cgminer",
    r"ethminer",
    # System shutdown/reboot
    r"shutdown",
    r"reboot",
    r"init\s+0",
    r"init\s+6",
    # Dangerous git operations
    r"git\s+push.*--force",
    r"git\s+reset\s+--hard\s+HEAD",
    # AWS dangerous operations (if no specific AWS hook)
    r"aws.*delete",
    r"aws.*terminate",
    r"terraform\s+destroy",
    r"cdk\s+destroy",
]

# Patterns that require confirmation
WARNING_PATTERNS = [
    r"sudo",
    r"npm\s+publish",
    r"pip\s+upload",
    r"docker\s+push",
    r"git\s+push.*main",
    r"git\s+push.*master",
    r"deploy",
    r"production",
]


def check_command(command: str) -> dict[str, str]:
    """Check if command contains dangerous patterns."""
    # Check for absolute dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return {
                "decision": "block",
                "reason": f"Dangerous command pattern detected: {pattern}",
                "level": "danger",
            }

    # Check for warning patterns (unless explicitly allowed)
    if os.environ.get("ALLOW_WARNINGS", "false").lower() != "true":
        for pattern in WARNING_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return {
                    "decision": "block",
                    "reason": f"Command requires manual confirmation: contains '{pattern}'",
                    "level": "warning",
                }

    return {"decision": "allow"}


def main() -> None:
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)
        tool_input = input_data.get("tool_input", {})
        tool_name = input_data.get("tool_name", "")

        # Only check Bash commands
        if tool_name != "Bash":
            sys.exit(0)

        command = tool_input.get("command", "")
        if not command:
            sys.exit(0)

        # Check the command
        result = check_command(command)

        if result["decision"] == "block":
            print(f"BLOCKED: {result['reason']}", file=sys.stderr)
            if result.get("level") == "warning":
                print(
                    "To allow this command, run it manually or set ALLOW_WARNINGS=true",
                    file=sys.stderr,
                )
            sys.exit(2)

        # Command is allowed
        sys.exit(0)

    except Exception as e:
        print(f"Hook error: {str(e)}", file=sys.stderr)
        # Allow operation on hook error
        sys.exit(0)


if __name__ == "__main__":
    main()
