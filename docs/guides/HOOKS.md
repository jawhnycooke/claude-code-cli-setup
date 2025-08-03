# Claude Code Hooks

Claude Code hooks provide powerful guardrails and automation for AI-assisted development. This guide explains how to use hooks to enhance safety and productivity when working with Claude Code.

## Overview

Hooks are scripts that run at specific points during Claude Code's workflow, allowing you to:
- Prevent dangerous operations
- Enforce coding standards
- Automate testing
- Protect sensitive files
- Validate deployments

## Available Hooks

### Security Hooks

#### file-change-limiter
Prevents Claude from making too many changes at once.
- **Event**: PreToolUse
- **Default limits**: 3 files per operation, 100 lines per file
- **Configure**: `MAX_FILES_PER_OPERATION`, `MAX_LINES_PER_FILE`

#### sensitive-file-protector
Blocks modifications to sensitive files like .env, credentials, and private keys.
- **Event**: PreToolUse
- **Configure**: `SENSITIVE_FILE_PATTERNS` (comma-separated regex patterns)

#### command-validator
Validates bash commands and blocks dangerous operations.
- **Event**: PreToolUse
- **Configure**: `ALLOW_WARNINGS=true` to allow warning-level commands

### Testing Hooks

#### test-enforcement
Automatically runs tests after code changes and blocks if tests fail.
- **Event**: PostToolUse
- **Supports**: Python (pytest), JavaScript/TypeScript (npm test), Ruby (rspec)

### AWS Hooks

#### deployment-guard
Validates AWS operations and prevents dangerous commands.
- **Event**: PreToolUse
- **Configure**: 
  - `ALLOW_PRODUCTION=true` for production operations
  - `MAX_LAMBDA_MEMORY` (default: 1024MB)
  - `MAX_LAMBDA_TIMEOUT` (default: 300s)

## Installation

### Quick Start
```bash
# List all available hooks
claude-setup hooks list

# Add specific hooks
claude-setup hooks add security/file-change-limiter
claude-setup hooks add testing/test-enforcement

# Add all security hooks
claude-setup hooks add security/file-change-limiter security/sensitive-file-protector security/command-validator

# Add hooks globally
claude-setup hooks add security/file-change-limiter --global
```

### Interactive Installation
```bash
# Interactive selection
claude-setup hooks add
```

## Configuration

Hooks are configured through environment variables and the settings.json file.

### Environment Variables
```bash
# File change limits
export MAX_FILES_PER_OPERATION=5
export MAX_LINES_PER_FILE=200

# AWS limits
export ALLOW_PRODUCTION=true
export MAX_LAMBDA_MEMORY=2048
```

### Settings.json Structure
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 .claude/hooks/security/file-change-limiter/limit_file_changes.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/testing/test-enforcement/run_tests_on_change.sh"
          }
        ]
      }
    ]
  }
}
```

## Hook Events

- **UserPromptSubmit**: Before Claude processes a user prompt
- **PreToolUse**: Before any tool execution
- **PostToolUse**: After successful tool completion
- **Stop**: When conversation ends
- **ToolOutputFiltered**: When tool output is filtered
- **ToolErrorThrown**: When a tool throws an error

## Creating Custom Hooks

### Hook Structure
```
my-hook/
├── metadata.json      # Hook configuration
├── my_script.py       # Hook script
└── README.md          # Documentation
```

### metadata.json Example
```json
{
  "name": "my-hook",
  "description": "My custom hook",
  "category": "custom",
  "event": "PreToolUse",
  "matcher": "Bash",
  "dependencies": ["python3"],
  "config": {
    "type": "command",
    "command": "python3 .claude/hooks/custom/my-hook/my_script.py"
  }
}
```

### Script Requirements
- Read input from stdin (JSON format)
- Exit codes:
  - 0: Allow operation
  - 1: Hook error (allow operation)
  - 2: Block operation
- Write block reasons to stderr

## Best Practices

1. **Start Strict**: Begin with tight limits and relax as needed
2. **Layer Protection**: Use multiple hooks for defense in depth
3. **Monitor Logs**: Review blocked operations to adjust settings
4. **Test Hooks**: Verify hooks work before relying on them
5. **Document Configuration**: Keep track of custom environment variables

## Examples

### Junior Developer Setup
```bash
# Install protective hooks
claude-setup hooks add \
  security/file-change-limiter \
  security/sensitive-file-protector \
  security/command-validator \
  testing/test-enforcement

# Configure strict limits
export MAX_FILES_PER_OPERATION=2
export MAX_LINES_PER_FILE=50
```

### AWS Development Setup
```bash
# Install AWS hooks
claude-setup hooks add \
  aws/deployment-guard \
  security/command-validator

# Configure for development only
export ALLOW_PRODUCTION=false
export MAX_LAMBDA_MEMORY=512
```

## Troubleshooting

### Hook Not Triggering
- Check hook is properly installed: `ls .claude/hooks/`
- Verify settings.json contains hook configuration
- Ensure script has execute permissions

### Hook Blocking Valid Operations
- Adjust environment variables
- Check hook logs (written to stderr)
- Temporarily disable with `claude-setup hooks remove <hook>`

### Performance Issues
- Hooks run synchronously, keep them fast
- Avoid network calls in hooks
- Use caching where appropriate

## Contributing

To contribute new hooks:
1. Follow the hook structure guidelines
2. Include comprehensive documentation
3. Add tests for the hook
4. Submit a pull request

For more information, see the [main README](README.md).