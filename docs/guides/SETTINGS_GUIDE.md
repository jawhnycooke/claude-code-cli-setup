# Claude Code Setup - Settings Configuration Guide

This guide provides comprehensive documentation for configuring and managing settings in Claude Code Setup.

## Overview

Claude Code Setup uses a flexible settings system that allows you to customize permissions, themes, environment variables, and hook configurations. Settings can be managed at both global (`~/.claude`) and project-local (`./.claude`) levels.

## Settings File Structure

Settings are stored in JSON format at `.claude/settings.json` with the following structure:

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
    "PYTHON_ENV": "development",
    "DEBUG": "true"
  },
  "hooks": {
    "file-change-limiter": {
      "enabled": true,
      "events": ["FileChange"],
      "config": {
        "maxFiles": 3,
        "maxLines": 100
      }
    }
  }
}
```

## Managing Settings

### Using the Settings Command

The `claude-setup settings` command provides multiple ways to manage your configuration:

#### Interactive Mode (Default)
```bash
claude-setup settings
```
This launches an interactive menu where you can:
- View current settings
- Modify theme settings
- Manage permissions
- Configure environment variables
- Enable/disable hooks

#### Direct Actions
```bash
# Show current settings
claude-setup settings show

# Manage theme
claude-setup settings theme

# Manage environment variables
claude-setup settings env

# Manage permissions
claude-setup settings permissions
```

### Global vs Local Settings

#### Local Settings (Project-specific)
By default, settings are stored in the current project directory:
```bash
./.claude/settings.json
```

#### Global Settings (User-wide)
Use the `--global` flag to manage settings that apply to all projects:
```bash
claude-setup settings show --global
claude-setup settings theme --global
```

Global settings are stored at:
- macOS/Linux: `~/.claude/settings.json`
- Windows: `%USERPROFILE%\.claude\settings.json`

### Settings Precedence

When both global and local settings exist:
1. Local settings take precedence over global settings
2. Missing values in local settings fall back to global settings
3. Missing values in both fall back to default settings

## Configuration Options

### Themes

Claude Code Setup supports two built-in themes:

#### default (Light Theme)
- Optimized for light terminal backgrounds
- Uses bright colors for visibility
- Standard color scheme for all UI elements

#### dark (Dark Theme)
- Optimized for dark terminal backgrounds
- Uses muted colors to reduce eye strain
- High contrast for readability

To change theme:
```bash
# Interactive theme selection
claude-setup settings theme

# Or during initialization
claude-setup init --theme dark
```

### Permissions

Permissions control which tools and commands Claude Code can execute. The permission system uses pattern matching:

#### Permission Syntax
```
Tool(command:action)
```

Examples:
- `Python(*)` - Allow all Python operations
- `Bash(pip:*)` - Allow all pip commands
- `Git(add:*, commit:*)` - Allow git add and commit only
- `Bash(rm:*)` - Allow file removal (use with caution!)

#### Common Permission Sets

**Python Development**
```json
"allow": [
  "Python(*)",
  "Bash(pip:*)",
  "Bash(uv:*)",
  "Bash(pytest:*)",
  "Bash(black:*)",
  "Bash(mypy:*)",
  "Bash(ruff:*)"
]
```

**Node.js Development**
```json
"allow": [
  "Bash(node:*)",
  "Bash(npm:*)",
  "Bash(npx:*)",
  "Bash(yarn:*)",
  "Bash(pnpm:*)"
]
```

**Full Stack Development**
```json
"allow": [
  "Python(*)",
  "Bash(node:*)",
  "Bash(npm:*)",
  "Git(*)",
  "Bash(docker:*)",
  "Read(*)",
  "Write(*)"
]
```

**Restricted Mode**
```json
"allow": [
  "Read(*)",
  "Python(analysis:*)",
  "Git(status:*, diff:*)"
]
```

#### Adding Permissions

```bash
# Add single permission
claude-setup add permission "Python(*)"

# Add during initialization
claude-setup init --permissions "python,git,shell"

# Interactive permission management
claude-setup settings permissions
```

### Environment Variables

Environment variables are passed to Claude Code and can be used in templates and commands:

#### Common Variables
```json
"environmentVariables": {
  "PYTHON_ENV": "development",
  "NODE_ENV": "development",
  "DEBUG": "true",
  "LOG_LEVEL": "info",
  "DATABASE_URL": "postgresql://localhost/mydb",
  "API_KEY": "your-api-key-here"
}
```

#### Managing Environment Variables

```bash
# Add environment variable
claude-setup add env PYTHON_ENV development

# Interactive management
claude-setup settings env

# Multiple variables
claude-setup add env DEBUG true
claude-setup add env LOG_LEVEL debug
```

### Hook Configuration

Hooks can have specific configuration passed through the settings:

```json
"hooks": {
  "file-change-limiter": {
    "enabled": true,
    "events": ["FileChange"],
    "config": {
      "maxFiles": 3,
      "maxLines": 100,
      "excludePatterns": ["*.test.js", "*.spec.py"]
    }
  },
  "command-validator": {
    "enabled": true,
    "events": ["PreToolUse"],
    "config": {
      "blockedCommands": ["rm -rf", "sudo"],
      "requireConfirmation": ["deploy", "publish"]
    }
  }
}
```

## Advanced Configuration

### Custom Settings Validation

Settings are validated using Pydantic models to ensure:
- Valid JSON structure
- Correct data types
- Valid permission patterns
- Proper hook configurations

### Settings Inheritance

You can create a hierarchy of settings:

1. **System Defaults** → Base configuration
2. **Global User Settings** → User preferences
3. **Project Settings** → Project-specific overrides
4. **Environment Settings** → Runtime overrides

### Programmatic Access

Settings can be accessed programmatically:

```python
from claude_code_setup.core.settings import Settings

# Load settings
settings = Settings.load()

# Access values
theme = settings.get_theme()
permissions = settings.get_permissions()
env_vars = settings.get_environment_variables()

# Modify settings
settings.set_theme("dark")
settings.add_permission("Docker(*)")
settings.save()
```

### Settings Backup and Restore

#### Backup Settings
```bash
# Backup local settings
cp .claude/settings.json .claude/settings.backup.json

# Backup global settings
cp ~/.claude/settings.json ~/.claude/settings.backup.json
```

#### Restore Settings
```bash
# Restore from backup
cp .claude/settings.backup.json .claude/settings.json

# Or reinitialize with defaults
claude-setup init --force
```

## Troubleshooting

### Common Issues

#### Settings Not Loading
```bash
# Verify settings file exists
ls -la .claude/settings.json

# Check JSON validity
python -m json.tool .claude/settings.json

# Debug settings loading
claude-setup settings show --debug
```

#### Permission Denied
```bash
# Fix file permissions
chmod 644 .claude/settings.json
chmod 755 .claude/

# Check ownership
ls -la .claude/
```

#### Settings Corruption
```bash
# Reset to defaults
rm .claude/settings.json
claude-setup init --quick

# Or restore from backup
cp .claude/settings.backup.json .claude/settings.json
```

### Settings Migration

When upgrading Claude Code Setup:

1. **Automatic Migration**: The tool attempts to migrate settings automatically
2. **Manual Migration**: Use `claude-setup update settings` to update format
3. **Fresh Start**: Use `claude-setup init --force` for clean installation

## Best Practices

### Security
- Never commit sensitive environment variables to version control
- Use project-specific permissions to limit tool access
- Regularly review and audit permissions
- Enable security hooks for additional protection

### Team Collaboration
- Share base settings through version control
- Use global settings for personal preferences
- Document custom permission requirements
- Create team-specific permission sets

### Performance
- Minimize environment variables to reduce overhead
- Disable unused hooks to improve performance
- Use specific permissions rather than wildcards when possible

## Examples

### Development Environment Setup
```bash
# Initialize with development settings
claude-setup init --quick --permissions "python,git,shell"

# Add development environment variables
claude-setup add env PYTHON_ENV development
claude-setup add env DEBUG true
claude-setup add env LOG_LEVEL debug

# Enable security hooks
claude-setup hooks add file-change-limiter
claude-setup hooks add command-validator

# Set dark theme for late-night coding
claude-setup settings theme
# Select: dark
```

### Production Environment Setup
```bash
# Initialize with restricted permissions
claude-setup init --permissions "python,git"

# Add production environment variables
claude-setup add env PYTHON_ENV production
claude-setup add env DEBUG false
claude-setup add env LOG_LEVEL warning

# Enable all security hooks
claude-setup hooks add file-change-limiter
claude-setup hooks add command-validator
claude-setup hooks add sensitive-file-protector

# Configure strict hook settings
# Edit .claude/settings.json to add:
{
  "hooks": {
    "file-change-limiter": {
      "config": {
        "maxFiles": 1,
        "maxLines": 50
      }
    }
  }
}
```

### CI/CD Configuration
```bash
# Non-interactive setup for CI
claude-setup init --quick --no-interactive

# Add minimal permissions
echo '{
  "permissions": {
    "allow": [
      "Python(test:*)",
      "Git(status:*, diff:*)",
      "Read(*)"
    ]
  },
  "environmentVariables": {
    "CI": "true",
    "PYTHON_ENV": "test"
  }
}' > .claude/settings.json
```

## See Also

- [CLI_REFERENCE.md](CLI_REFERENCE.md) - Complete command reference
- [HOOKS.md](HOOKS.md) - Detailed hook documentation
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
- [TEMPLATES.md](TEMPLATES.md) - Available command templates