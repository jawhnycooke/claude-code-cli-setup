# Claude Code Setup

Claude Code Setup is a CLI tool for managing command templates and configurations for Claude Code. It provides a streamlined way to set up, configure, and organize Claude Code commands in your projects, similar to shadcn/ui's approach to component installation.

## Purpose and Key Functionality

Claude Code Setup simplifies the configuration and use of Claude Code by providing:

- Command template management with add, list, update, and remove functionality
- Settings management for permissions, themes, and environment variables
- **Hooks system for guardrails and automation** (security, testing, AWS safety)
- **Plugin system for modular extensions** (templates, hooks, agents, workflows)
- Interactive setup wizards for beginners and direct CLI commands for power users
- Support for both local project configuration and global user configuration
- Category-based organization of templates (python, node, project, general)

The tool creates a `.claude` directory in either your project or home directory, which contains command templates and settings that enhance your Claude Code experience.

## Technologies Used

Claude Code Setup is built with:

- Python 3.9+ for robust, type-safe development
- Click for CLI command structure and argument parsing
- Rich for enhanced terminal UI and styling
- Questionary for interactive prompts
- Pydantic for settings validation and data modeling
- PyFiglet for ASCII art banners
- Halo for progress spinners

## Basic Usage

Getting started with Claude Code Setup:

```bash
# Install the package
pip install claude-code-setup
# Or with uv (recommended for faster installations)
uv pip install claude-code-setup

# Initialize Claude Code in your project (interactive)
claude-setup init

# Or initialize with defaults
claude-setup init --quick

# List available templates and settings
claude-setup list

# Add templates interactively
claude-setup add

# Add specific templates directly
claude-setup add template python-optimization

# Update templates or settings
claude-setup update

# List available hooks
claude-setup hooks list

# Add security hooks
claude-setup hooks add file-change-limiter

# Add all hooks interactively
claude-setup hooks add

# List available plugins
claude-setup plugins list

# Add a plugin
claude-setup plugins add code-quality

# Add a plugin bundle
claude-setup plugins add bundle:python-full-stack
```

## Documentation

For more details on installation, configuration, and advanced usage, please see our [comprehensive documentation](./docs/README.md):

### Quick Links
- [**Setup Guide**](./docs/guides/SETUP.md) - Installation and initial setup
- [**Usage Guide**](./docs/guides/USAGE.md) - Detailed usage instructions  
- [**CLI Reference**](./docs/guides/CLI_REFERENCE.md) - Complete command reference
- [**Plugin System**](./docs/api/PLUGINS.md) - Using and developing plugins
- [**Hooks Guide**](./docs/guides/HOOKS.md) - Security and automation hooks

### For Developers
- [**Architecture**](./docs/development/ARCHITECTURE.md) - System design and architecture
- [**Development Setup**](./docs/development/DEVELOPMENT_SETUP.md) - Contributing to the project
- [**Plugin Development**](./docs/api/PLUGIN_DEVELOPMENT.md) - Creating custom plugins