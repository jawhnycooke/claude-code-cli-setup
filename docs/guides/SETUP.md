# Claude Code Setup - Installation & Configuration

This document provides detailed instructions for installing, configuring, and setting up the Claude Code Setup tool.

## Prerequisites

Before installing Claude Code Setup, ensure your system meets these requirements:

- Python 3.9 or higher
- pip or uv package manager (uv recommended for faster installations)
- A terminal that supports ANSI colors for the best experience

The tool is designed to work on macOS, Linux, and Windows environments.

## Installation

You can install Claude Code Setup using pip or uv:

### Using pip

```bash
pip install claude-code-setup
```

### Using uv (Recommended)

```bash
uv pip install claude-code-setup
```

### Using pipx (Isolated Installation)

```bash
pipx install claude-code-setup
```

### Using pnpm

```bash
pnpm install -g @jawhnycooke/claude-code-setup
```

After installation, verify that the tool is correctly installed by running:

```bash
claude-setup --version
```

This should display the current version of Claude Code Setup.

## Initial Setup

After installation, you need to initialize Claude Code in your project or globally. There are two approaches:

### Interactive Setup (Recommended for Beginners)

The interactive setup walks you through the configuration process with guided prompts:

```bash
claude-setup init
```

This will:
1. Ask where to set up Claude Code (local project or global)
2. Check for existing configuration
3. Configure settings interactively
4. Offer to install popular templates

### Quick Setup (For Power Users)

If you prefer to use default settings without prompts:

```bash
claude-setup init --quick
```

This will create a `.claude` directory with default settings and folder structure without any interactive prompts.

### Setup Options

The init command supports several options:

- `--quick`: Quick setup with defaults (skip interactive prompts)
- `--force` or `-f`: Force overwrite of existing configuration
- `--dry-run` or `-d`: Simulate without making changes
- `--test-dir <dir>`: Use a test directory instead of current directory
- `--global` or `-g`: Save configuration to global `~/.claude` directory

## Configuration Structure

Claude Code Setup creates a `.claude` directory with the following structure:

```
.claude/
├── commands/        # Command templates
│   ├── general/     # General purpose templates
│   ├── node/        # Node.js specific templates
│   ├── project/     # Project management templates
│   └── python/      # Python specific templates
└── settings.json    # Configuration settings
```

The settings file contains:

- Permissions for various tools
- Theme configuration
- Environment variables
- Any other custom settings

## Settings Configuration

You can manage settings using the following commands:

### Adding Settings

```bash
# Add a permission
claude-setup add permission "Bash(npm:*)"

# Set a theme
claude-setup add theme dark

# Add an environment variable
claude-setup add env NODE_ENV production
```

### Updating Settings

```bash
# Update all settings to latest defaults while preserving customizations
claude-setup update settings
```

### Viewing Current Settings

```bash
# List all settings
claude-setup list settings
```

## Environment Variables

Claude Code Setup respects the following environment variables:

- `CLAUDE_HOME`: Override the location of the global Claude directory
- `CLAUDE_NO_COLOR`: Disable colored output
- `CLAUDE_DEBUG`: Enable debug logging

## Development Setup

If you want to develop or contribute to Claude Code Setup:

```bash
# Clone the repository
git clone https://github.com/jawhnycooke/claude-code-setup.git
cd claude-code-setup

# Install dependencies
pnpm install

# Build the project
pnpm run build

# Run in watch mode during development
pnpm run dev
```

The development environment supports:
- TypeScript with strict type checking
- ESLint for code quality
- Vitest for testing
- Release-it for versioning and publishing

## Troubleshooting

If you encounter issues during setup:

1. Ensure Node.js version 20+ is installed
2. Check file permissions in your project directory
3. Try running with `--force` to overwrite any corrupted configuration
4. For global installation issues, you may need to use `sudo` on Unix-based systems

For persistent issues, check the GitHub repository for known issues or to file a new bug report.