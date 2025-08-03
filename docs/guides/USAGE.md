# Claude Code Setup - Usage Guide

This document provides detailed information on using the Claude Code Setup tool effectively, including common use cases and examples.

## Command Overview

Claude Code Setup offers the following main commands:

- `init`: Initialize Claude Code setup in your project or globally
- `list`: Display available templates, hooks, and current settings
- `add`: Add templates, hooks, permissions, or environment variables
- `update`: Update templates or settings to their latest versions
- `remove`: Remove templates, hooks, or permissions from your configuration
- `hooks`: Manage security and automation hooks
- `settings`: Configure themes, environment variables, and permissions
- `interactive`: Launch guided interactive workflows

Each command supports both interactive and direct usage modes to accommodate different user preferences.

## Working with Templates

Templates are pre-defined command configurations stored as Markdown files that enhance your Claude Code experience.

### Listing Available Templates

To see what templates are available:

```bash
# Interactive list with options to add/update
claude-setup list

# Non-interactive list of just templates
claude-setup list templates
```

The output shows templates organized by category, with indicators for which ones you already have installed.

### Adding Templates

Templates can be added in two ways:

#### Interactive Template Selection

```bash
# Launch interactive template selection
claude-setup add
# Then choose "Templates" from the menu and select the ones you want
```

This approach presents a categorized list of templates with checkboxes to select multiple templates at once.

#### Direct Template Installation

```bash
# Install a specific template directly
claude-setup add template code-review

# Install with force overwrite of existing template
claude-setup add template fix-issue --force

# Install to global configuration
claude-setup add template create-tasks --global
```

### Updating Templates

To ensure your templates are up to date:

```bash
# Update all installed templates
claude-setup update templates

# Update a specific template
claude-setup update code-review

# Interactive update menu
claude-setup update
```

### Using Templates

After installation, templates are available in your Claude Code environment. You can use them by:

1. Running Claude Code with the template name
2. Accessing them through the Claude Code interface
3. Referencing them in Claude Code command flags

## Managing Settings

Settings control how Claude Code behaves and what permissions it has.

### Viewing Current Settings

```bash
# List current settings
claude-setup list settings
```

This shows your current theme, permissions, and environment variables.

### Adding Settings

#### Using the Settings Command

The dedicated settings command provides comprehensive configuration management:

```bash
# Interactive settings management
claude-setup settings

# Manage themes directly
claude-setup settings theme

# Manage environment variables
claude-setup settings env

# Manage permissions
claude-setup settings permissions
```

#### Adding Permissions

Permissions control what tools Claude Code can use:

```bash
# Add a specific Bash permission
claude-setup add permission "Bash(npm:*)"

# Add Python permissions
claude-setup add permission "Python(*)"

# Use permission sets
claude-setup init --permissions "python,git,shell"

# Interactive permission management
claude-setup settings permissions
```

Common permission patterns:
- `Python(*)` - All Python operations
- `Bash(pip:*)` - All pip commands
- `Git(*)` - All git operations
- `Read(*)` - All file reading
- `Write(*)` - All file writing

#### Setting Themes

Choose between available UI themes:

```bash
# Interactive theme selection
claude-setup settings theme

# Direct theme setting
claude-setup add theme dark

# Set theme during initialization
claude-setup init --theme dark
```

#### Adding Environment Variables

Configure environment variables for Claude Code:

```bash
# Set an environment variable
claude-setup add env NODE_ENV production

# Set multiple variables
claude-setup add env DEBUG true
claude-setup add env LOG_LEVEL info

# Interactive environment variable management
claude-setup settings env
```

### Updating Settings

To update your settings to the latest defaults while preserving your customizations:

```bash
# Update all settings
claude-setup update settings
```

## Working with Hooks

Hooks provide security and automation features for Claude Code operations.

### Listing Available Hooks

```bash
# Interactive list with installation options
claude-setup hooks list

# Non-interactive list
claude-setup hooks list --no-interactive

# List by category
claude-setup hooks list --category security
```

### Installing Hooks

```bash
# Install a specific hook
claude-setup hooks add file-change-limiter

# Install multiple hooks interactively
claude-setup hooks add

# Force reinstall
claude-setup hooks add command-validator --force
```

### Available Hooks

#### Security Hooks
- **file-change-limiter**: Limits the number of files modified per operation
- **command-validator**: Validates potentially dangerous commands
- **sensitive-file-protector**: Protects sensitive files from modification

#### Testing Hooks
- **test-enforcement**: Enforces test requirements before code changes

#### AWS Hooks
- **deployment-guard**: AWS deployment safety checks

### Managing Hook Configuration

Hook settings are stored in your settings.json:

```bash
# View hook status
claude-setup hooks status

# Remove a hook
claude-setup hooks remove file-change-limiter
```

## Advanced Usage

### Local vs Global Configuration

Claude Code Setup supports both project-level and global configurations:

```bash
# Initialize in current project
claude-setup init

# Initialize globally
claude-setup init --global

# Add template to global config
claude-setup add template code-review --global
```

The global configuration is stored in `~/.claude` and is available for all your projects.

### Testing Mode

When developing templates or configurations, you can use test mode:

```bash
# Initialize in a test directory
claude-setup init --test-dir ./my-test-dir

# Test adding a template
claude-setup add template code-review --test-dir ./my-test-dir
```

This creates a contained environment for testing without affecting your actual configuration.

### Dry Run Mode

To see what changes would be made without actually making them:

```bash
# Dry run initialization
claude-setup init --dry-run

# Dry run template addition
claude-setup add template code-review --dry-run
```

### Command Templates by Category

Claude Code Setup organizes templates into these categories:

1. **General** - Broadly applicable templates like code reviews and issue fixing
   - Example: `code-review`, `fix-issue`

2. **Node** - Templates specific to Node.js development
   - Example: `node-optimization`

3. **Python** - Templates specific to Python development
   - Example: `python-optimization`

4. **Project** - Templates for project management tasks
   - Example: `create-tasks`, `generate-docs`, `update-tasks`

## Example Workflows

### Setting Up a New Python Project

```bash
# Initialize with Python-focused setup
claude-setup init --quick --permissions "python,git,shell"

# Add Python-specific templates
claude-setup add template python-optimization
claude-setup add template code-review

# Add security hooks
claude-setup hooks add file-change-limiter
claude-setup hooks add sensitive-file-protector

# Configure environment
claude-setup settings theme  # Choose dark theme
claude-setup add env PYTHON_ENV development
claude-setup add env DEBUG true
```

### Setting Up a Node.js Project

```bash
# Initialize with Node.js permissions
claude-setup init --permissions "node,git,shell"

# Add Node.js templates
claude-setup add template node-optimization
claude-setup add template code-review

# Configure for Node.js development
claude-setup add env NODE_ENV development
claude-setup add permission "Bash(npm:*)"
claude-setup add permission "Bash(yarn:*)"
```

### Enterprise Security Setup

```bash
# Initialize with strict security
claude-setup init --global

# Add all security hooks
claude-setup hooks add file-change-limiter
claude-setup hooks add command-validator
claude-setup hooks add sensitive-file-protector

# Configure strict permissions
claude-setup add permission "Python(pytest:*, black:*, mypy:*)"
claude-setup add permission "Git(status:*, diff:*, add:*, commit:*)"
claude-setup remove permission "Bash(rm:*)"  # Remove dangerous permissions
```

### CI/CD Environment Setup

```bash
# Non-interactive setup for automation
claude-setup init --quick --no-interactive

# Add minimal permissions for CI
claude-setup add permission "Python(test:*)" --no-interactive
claude-setup add permission "Read(*)" --no-interactive

# Add test enforcement hook
claude-setup hooks add test-enforcement --no-interactive

# Set CI environment
claude-setup add env CI true --no-interactive
claude-setup add env PYTHON_ENV test --no-interactive
```

### Updating an Existing Setup

```bash
# List what's currently installed
claude-setup list

# Check for template updates
claude-setup update templates

# Update all hooks to latest versions
claude-setup update hooks

# Update settings to latest defaults
claude-setup update settings
```

### Quick Development Setup

```bash
# Use interactive mode for guided setup
claude-setup interactive

# Or use the quick setup with common defaults
claude-setup init --quick
claude-setup add template code-review
claude-setup add template create-tasks
claude-setup hooks add file-change-limiter
```

## Troubleshooting Common Issues

### Command Not Found

If `claude-setup` command is not found after installation:

```bash
# Check if installed correctly
pip show claude-code-setup

# Try using Python module directly
python -m claude_code_setup.cli --version

# Reinstall with user flag
pip install --user claude-code-setup
```

### Missing Templates or Hooks

If templates or hooks are not appearing in the list:

```bash
# Check current setup location
claude-setup list

# Ensure you're viewing the correct location
claude-setup list --global  # for global configuration

# Verify installation directory exists
ls -la ~/.claude/  # or ./.claude for local
```

### Permission Issues

If Claude Code can't perform certain actions:

```bash
# Check current permissions
claude-setup settings show

# Add necessary permissions
claude-setup add permission "Bash(your-command:*)"

# Use interactive permission management
claude-setup settings permissions
```

### Hook Not Working

If hooks aren't triggering as expected:

```bash
# Check hook status
claude-setup hooks status

# Verify hook is enabled in settings
claude-setup settings show

# Reinstall the hook
claude-setup hooks remove problematic-hook
claude-setup hooks add problematic-hook --force
```

### Configuration Conflicts

If you encounter configuration conflicts:

```bash
# Force overwrite existing settings
claude-setup init --force

# Update to latest defaults while preserving customizations
claude-setup update settings

# Check for JSON errors in settings
python -m json.tool .claude/settings.json
```

### Performance Issues

If commands are running slowly:

```bash
# Use non-interactive mode for scripts
claude-setup list --no-interactive

# Check for large configuration files
du -sh ~/.claude/*

# Reinstall with uv for better performance
uv pip install claude-code-setup
```

## Integrating with Existing Workflows

Claude Code Setup can be incorporated into your development workflow:

### Project Setup Scripts

Include claude-setup in your project initialization:

```bash
#!/bin/bash
# setup.sh - Project setup script

# Install dependencies
pip install -r requirements.txt
pip install claude-code-setup

# Initialize Claude Code
claude-setup init --quick --no-interactive

# Add project-specific templates
claude-setup add template python-optimization --no-interactive
claude-setup add template code-review --no-interactive

# Add security hooks
claude-setup hooks add file-change-limiter --no-interactive

# Configure environment
claude-setup add env PYTHON_ENV development --no-interactive
```

### Team Configuration Sharing

Share configurations across your team:

```bash
# Export your configuration
cp -r .claude .claude-team-config

# In version control (.gitignore)
.claude/
!.claude-team-config/

# Team members can copy the configuration
cp -r .claude-team-config .claude
```

### Makefile Integration

```makefile
# Makefile
setup-claude:
	pip install claude-code-setup
	claude-setup init --quick --no-interactive
	claude-setup add template code-review --no-interactive
	claude-setup hooks add file-change-limiter --no-interactive

dev-setup: install-deps setup-claude
	@echo "Development environment ready!"
```

### Docker Integration

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install claude-setup
RUN pip install claude-code-setup

# Configure claude-setup
RUN claude-setup init --global --quick --no-interactive && \
    claude-setup add permission "Python(*)" --no-interactive && \
    claude-setup add permission "Read(*)" --no-interactive
```

### Pre-commit Hook

Ensure templates are up to date:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: claude-setup-check
        name: Check Claude Setup
        entry: claude-setup list --no-interactive
        language: system
        pass_filenames: false
```

By understanding these commands and examples, you can make the most of Claude Code Setup to enhance your development experience and maintain consistency across your team and projects.