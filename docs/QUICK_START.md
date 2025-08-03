# Quick Start Guide

## Installation

```bash
# Using pip
pip install claude-code-setup

# Using uv (recommended - faster)
uv pip install claude-code-setup

# For development
git clone https://github.com/jawhnycooke/claude-code-setup.git
cd claude-code-setup
uv venv && source .venv/bin/activate
uv pip install -e .
```

## First Steps

### 1. Initialize Claude Code Setup

```bash
# Interactive setup (recommended for first time)
claude-setup init

# Quick setup with defaults
claude-setup init --quick
```

### 2. Add Essential Templates

```bash
# Add Python optimization template
claude-setup add template python-optimization

# Add all Python templates
claude-setup add template --category python

# Browse and select templates interactively
claude-setup add
```

### 3. Set Up Security Hooks

```bash
# Add file change limiter (prevents accidental mass changes)
claude-setup hooks add file-change-limiter

# Add sensitive file protector
claude-setup hooks add sensitive-file-protector

# View all available hooks
claude-setup hooks list
```

### 4. Install Useful Plugins

```bash
# Add code quality plugin
claude-setup plugins add code-quality

# Add Python development bundle
claude-setup plugins add bundle:python-essentials

# List all available plugins
claude-setup plugins list
```

## Common Commands

```bash
# List all templates, hooks, and settings
claude-setup list

# Update templates or settings
claude-setup update

# Remove a template
claude-setup remove template <name>

# Check Claude Code Setup version
claude-setup --version

# Get help
claude-setup --help
claude-setup <command> --help
```

## Next Steps

- Read the [full usage guide](./guides/USAGE.md) for detailed instructions
- Explore [available templates](./guides/TEMPLATES.md)
- Learn about [hooks and guardrails](./guides/HOOKS.md)
- Discover [plugins](./api/PLUGINS.md) for extended functionality

## Need Help?

- Check [Troubleshooting](./guides/TROUBLESHOOTING.md)
- Review [Settings Guide](./guides/SETTINGS_GUIDE.md)
- See [CLI Reference](./guides/CLI_REFERENCE.md) for all commands