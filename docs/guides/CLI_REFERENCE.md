# Claude Code Setup - CLI Reference

Complete command reference for the `claude-setup` CLI tool.

## Table of Contents

- [Overview](#overview)
- [Global Options](#global-options)
- [Commands](#commands)
  - [init](#init)
  - [list](#list)
  - [add](#add)
  - [update](#update)
  - [remove](#remove)
  - [hooks](#hooks)
  - [settings](#settings)
  - [interactive](#interactive)
- [Configuration](#configuration)
- [Examples](#examples)

## Overview

Claude Code Setup provides both interactive and command-line interfaces for managing Claude Code templates, hooks, and settings. The tool supports both beginner-friendly interactive workflows and power-user direct commands.

### Interactive vs Non-Interactive Modes

- **Interactive Mode** (default): Guided workflows with prompts, progress bars, and help text
- **Non-Interactive Mode** (`--no-interactive`): Direct command execution suitable for scripting

## Global Options

Available for all commands:

| Option | Description |
|--------|-------------|
| `--version` | Show version and exit |
| `--no-interactive` | Disable all interactive prompts |
| `--debug` | Enable debug output |
| `--help` | Show help message |

## Commands

### init

Initialize Claude Code setup in your project or globally.

#### Syntax
```bash
claude-setup init [OPTIONS]
```

#### Options

| Option | Type | Description |
|--------|------|-------------|
| `--quick` | Flag | Quick setup with defaults |
| `-f, --force` | Flag | Force overwrite existing configuration |
| `-d, --dry-run` | Flag | Simulate without making changes |
| `--test-dir PATH` | Path | Use test directory instead of current directory |
| `-g, --global` | Flag | Save configuration to global ~/.claude directory |
| `-p, --permissions TEXT` | Text | Comma-separated list of permission sets |
| `--theme TEXT` | Text | Theme to use (default, dark) |
| `--no-check` | Flag | Skip checks for existing configuration |

#### Examples

```bash
# Interactive setup
claude-setup init

# Quick setup with defaults
claude-setup init --quick

# Global configuration
claude-setup init --global --theme dark

# Setup with specific permissions
claude-setup init --permissions "python,git,shell" --quick

# Test directory setup
claude-setup init --test-dir ./my-test --force
```

#### Behavior

- **Interactive Mode**: Walks through setup wizard with customization options
- **Quick Mode**: Uses defaults for fast setup
- **Global Mode**: Creates configuration in `~/.claude` instead of local `.claude`
- **Force Mode**: Overwrites existing configuration without confirmation

---

### list

List available templates, hooks, and settings with interactive options.

#### Syntax
```bash
claude-setup list [CATEGORY] [OPTIONS]
```

#### Categories

| Category | Description |
|----------|-------------|
| `templates` | List available command templates |
| `hooks` | List available hooks |
| `settings` | Show current settings |
| `permissions` | List available permission sets |

#### Options

| Option | Type | Description |
|--------|------|-------------|
| `--test-dir PATH` | Path | Use specific test directory |
| `--no-interactive` | Flag | Show list only, no actions |

#### Examples

```bash
# Interactive list with actions
claude-setup list

# List only templates
claude-setup list templates

# List hooks in non-interactive mode
claude-setup list hooks --no-interactive

# List settings from test directory
claude-setup list settings --test-dir ./test-config
```

#### Output Format

- **Interactive**: Rich tables with action options
- **Non-Interactive**: Simple text list
- **Templates**: Grouped by category (python, node, project, general)
- **Hooks**: Grouped by type (security, testing, aws)

---

### add

Add templates, hooks, permissions, or environment variables.

#### Syntax
```bash
claude-setup add [TYPE] [NAME] [OPTIONS]
```

#### Types

| Type | Description | Examples |
|------|-------------|----------|
| `template` | Add command template | `python-optimization`, `code-review` |
| `hook` | Add automation hook | `file-change-limiter`, `command-validator` |
| `permission` | Add permission rule | `"Python(*)"`, `"Bash(pip:*)"` |
| `env` | Add environment variable | `PYTHON_ENV=development` |

#### Options

| Option | Type | Description |
|--------|------|-------------|
| `-f, --force` | Flag | Overwrite existing items |
| `--test-dir PATH` | Path | Use specific test directory |
| `--category TEXT` | Text | Filter templates by category |

#### Examples

```bash
# Interactive mode - choose what to add
claude-setup add

# Add specific template
claude-setup add template python-optimization

# Add security hook
claude-setup add hook file-change-limiter

# Add permission with force
claude-setup add permission "Python(*)" --force

# Add environment variable
claude-setup add env PYTHON_ENV development

# Add from specific category
claude-setup add template --category python
```

#### Template Categories

- **general**: `code-review`, `fix-issue`
- **python**: `python-optimization` 
- **node**: `node-optimization`
- **project**: `create-tasks`, `generate-docs`, `update-tasks`

#### Available Hooks

- **security/file-change-limiter**: Limits file modifications per operation
- **security/command-validator**: Validates dangerous commands
- **security/sensitive-file-protector**: Protects sensitive files
- **aws/deployment-guard**: AWS deployment safety checks
- **testing/test-enforcement**: Enforces testing requirements

---

### update

Update templates or settings to their latest versions.

#### Syntax
```bash
claude-setup update [TYPE] [OPTIONS]
```

#### Types

| Type | Description |
|------|-------------|
| `templates` | Update all templates |
| `settings` | Update settings format |
| `hooks` | Update installed hooks |

#### Options

| Option | Type | Description |
|--------|------|-------------|
| `--dry-run` | Flag | Show what would be updated |
| `--test-dir PATH` | Path | Use specific test directory |
| `-f, --force` | Flag | Force update without confirmation |

#### Examples

```bash
# Interactive update with options
claude-setup update

# Update all templates
claude-setup update templates

# Dry run to see changes
claude-setup update --dry-run

# Force update settings
claude-setup update settings --force
```

---

### remove

Remove templates or permissions from configuration.

#### Syntax
```bash
claude-setup remove [TYPE] [NAME] [OPTIONS]
```

#### Types

| Type | Description |
|------|-------------|
| `template` | Remove command template |
| `permission` | Remove permission rule |
| `hook` | Remove automation hook |

#### Options

| Option | Type | Description |
|--------|------|-------------|
| `--test-dir PATH` | Path | Use specific test directory |
| `--no-confirm` | Flag | Skip confirmation prompts |

#### Examples

```bash
# Interactive removal with confirmation
claude-setup remove

# Remove specific template
claude-setup remove template python-optimization

# Remove permission without confirmation
claude-setup remove permission "Python(*)" --no-confirm

# Remove hook
claude-setup remove hook file-change-limiter
```

---

### hooks

Manage security and automation hooks.

#### Syntax
```bash
claude-setup hooks [SUBCOMMAND] [OPTIONS]
```

#### Subcommands

| Subcommand | Description |
|------------|-------------|
| `list` | List available and installed hooks |
| `add [NAME]` | Install specific hook |
| `remove [NAME]` | Uninstall specific hook |
| `status` | Show hook status and health |

#### Options

| Option | Type | Description |
|--------|------|-------------|
| `--test-dir PATH` | Path | Use specific test directory |
| `--category TEXT` | Text | Filter by category (security, testing, aws) |
| `-f, --force` | Flag | Force installation/removal |

#### Examples

```bash
# List all hooks
claude-setup hooks list

# Install security hook
claude-setup hooks add file-change-limiter

# Remove hook with force
claude-setup hooks remove command-validator --force

# Show hook status
claude-setup hooks status

# List security hooks only
claude-setup hooks list --category security
```

#### Hook Event Types

Hooks can respond to these Claude Code events:

- **UserPromptSubmit**: When user submits a prompt
- **PreToolUse**: Before tool execution
- **PostToolUse**: After tool execution
- **FileChange**: When files are modified
- **CommandExecution**: When commands are run

---

### settings

Manage Claude Code settings and configuration.

#### Syntax
```bash
claude-setup settings [ACTION] [OPTIONS]
```

#### Actions

| Action | Description |
|--------|-------------|
| `show` | Display current settings |
| `theme` | Manage UI theme settings |
| `env` | Manage environment variables |
| `permissions` | Manage permission settings |

#### Options

| Option | Type | Description |
|--------|------|-------------|
| `--test-dir PATH` | Path | Use specific test directory |
| `--global` | Flag | Use global configuration |
| `--no-interactive` | Flag | Non-interactive mode |

#### Examples

```bash
# Interactive settings management
claude-setup settings

# Show current settings
claude-setup settings show

# Manage theme settings
claude-setup settings theme

# Manage permissions interactively
claude-setup settings permissions

# Show global settings
claude-setup settings show --global
```

#### Available Themes

- **default**: Light theme with standard colors
- **dark**: Dark theme optimized for dark terminals

#### Permission Sets

- **python**: Python development permissions
- **node**: Node.js development permissions  
- **git**: Git operations permissions
- **shell**: Shell command permissions
- **package-managers**: Package manager permissions

---

### interactive

Launch interactive mode with guided workflows.

#### Syntax
```bash
claude-setup interactive [OPTIONS]
```

#### Options

| Option | Type | Description |
|--------|------|-------------|
| `--test-dir PATH` | Path | Use specific test directory |

#### Examples

```bash
# Launch interactive menu
claude-setup interactive

# Interactive with test directory
claude-setup interactive --test-dir ./test-config
```

#### Interactive Features

- **Menu-driven navigation**
- **Contextual help and tips**
- **Progress tracking**
- **Undo/redo capabilities**
- **Real-time validation**

---

## Configuration

### Directory Structure

```
.claude/                    # Configuration directory
├── settings.json          # Main settings file
├── commands/              # Installed templates
│   ├── python/           # Python-specific templates
│   ├── node/             # Node.js templates
│   ├── project/          # Project management templates
│   └── general/          # General-purpose templates
└── hooks/                # Installed hooks
    ├── security/         # Security hooks
    ├── testing/          # Testing hooks
    └── aws/              # AWS-related hooks
```

### Settings File Format

```json
{
  "theme": "default",
  "autoUpdaterStatus": "enabled",
  "permissions": {
    "allow": [
      "Python(*)",
      "Bash(pip:*)",
      "Git(*)"
    ]
  },
  "environmentVariables": {
    "PYTHON_ENV": "development"
  },
  "hooks": {
    "file-change-limiter": {
      "enabled": true,
      "events": ["FileChange"],
      "config": {}
    }
  }
}
```

## Examples

### Quick Start Workflow

```bash
# 1. Initialize with Python development setup
claude-setup init --quick --permissions "python,git,shell"

# 2. Add Python optimization template  
claude-setup add template python-optimization

# 3. Add security hooks
claude-setup add hook file-change-limiter
claude-setup add hook sensitive-file-protector

# 4. Configure environment
claude-setup add env PYTHON_ENV development
claude-setup add env VIRTUAL_ENV .venv

# 5. Verify setup
claude-setup list settings
```

### Enterprise Setup

```bash
# Global configuration for team
claude-setup init --global --theme dark --no-check

# Add comprehensive security hooks
claude-setup hooks add file-change-limiter --force
claude-setup hooks add command-validator --force
claude-setup hooks add sensitive-file-protector --force

# Configure strict permissions
claude-setup add permission "Python(pytest:*, black:*, ruff:*)"
claude-setup add permission "Git(add:*, commit:*, push:*, pull:*)"
claude-setup add permission "Bash(pip:*, uv:*)"

# Add project templates
claude-setup add template code-review
claude-setup add template create-tasks
claude-setup add template update-tasks
```

### Development Workflow

```bash
# Initialize project-specific config
claude-setup init --test-dir ./dev-config

# Add development templates
claude-setup add template python-optimization --test-dir ./dev-config
claude-setup add template code-review --test-dir ./dev-config

# Configure development environment
claude-setup add env DEBUG true --test-dir ./dev-config
claude-setup add env LOG_LEVEL debug --test-dir ./dev-config

# Test configuration
claude-setup settings show --test-dir ./dev-config
```

### CI/CD Integration

```bash
# Non-interactive setup for CI
claude-setup init --quick --no-interactive --permissions "python,shell"

# Add only essential hooks
claude-setup add hook command-validator --force --no-interactive

# Verify setup
claude-setup list settings --no-interactive
```

For more examples and advanced usage patterns, see the [USAGE.md](USAGE.md) documentation.