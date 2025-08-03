#!/bin/bash

# Test enforcement hook - runs tests after code changes
# Exit codes:
# 0 - Tests passed, continue
# 1 - Hook error (allow operation)
# 2 - Tests failed (block operation)

# Read input from stdin
INPUT=$(cat)

# Extract tool name
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')

# Only run for code changes
if [[ ! "$TOOL_NAME" =~ ^(Edit|MultiEdit|Write)$ ]]; then
    exit 0
fi

# Extract file paths
if [ "$TOOL_NAME" = "MultiEdit" ]; then
    FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path')
else
    FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path')
fi

# Check if this is a test file itself (avoid infinite loop)
if [[ "$FILE_PATH" =~ test|spec ]]; then
    exit 0
fi

# Determine which test command to run based on file extension
if [[ "$FILE_PATH" =~ \.py$ ]]; then
    # Python file - run pytest
    if command -v pytest &> /dev/null; then
        echo "Running Python tests..." >&2
        if pytest --tb=short -v; then
            echo "✅ Python tests passed" >&2
            exit 0
        else
            echo "❌ Python tests failed - please fix before continuing" >&2
            exit 2
        fi
    fi
elif [[ "$FILE_PATH" =~ \.(js|jsx|ts|tsx)$ ]]; then
    # JavaScript/TypeScript file - run npm test
    if [ -f "package.json" ] && grep -q "\"test\"" package.json; then
        echo "Running JavaScript tests..." >&2
        if npm test; then
            echo "✅ JavaScript tests passed" >&2
            exit 0
        else
            echo "❌ JavaScript tests failed - please fix before continuing" >&2
            exit 2
        fi
    fi
elif [[ "$FILE_PATH" =~ \.rb$ ]]; then
    # Ruby file - run rspec
    if command -v rspec &> /dev/null; then
        echo "Running Ruby tests..." >&2
        if rspec; then
            echo "✅ Ruby tests passed" >&2
            exit 0
        else
            echo "❌ Ruby tests failed - please fix before continuing" >&2
            exit 2
        fi
    fi
fi

# No applicable test runner found or tests passed
exit 0