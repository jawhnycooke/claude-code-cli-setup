# Claude Code Setup Plugin System

The Claude Code Setup plugin system provides a modular way to extend functionality through plugins that can provide templates, hooks, agents, and workflows.

## Table of Contents

- [Overview](#overview)
- [Plugin Architecture](#plugin-architecture)
- [Creating Plugins](#creating-plugins)
- [Plugin Manifest](#plugin-manifest)
- [Plugin Commands](#plugin-commands)
- [Plugin Bundles](#plugin-bundles)
- [Example Plugins](#example-plugins)
- [Developer Guide](#developer-guide)

## Overview

Plugins allow you to:
- **Extend functionality** - Add new templates, hooks, agents, and workflows
- **Share configurations** - Package and distribute your Claude Code setups
- **Organize by domain** - Group related functionality (e.g., security, testing, Python development)
- **Manage dependencies** - Specify dependencies between plugins
- **Version control** - Semantic versioning for compatibility

## Plugin Architecture

### Directory Structure

```
.claude/
├── plugins/
│   ├── registry.json       # Plugin registry tracking installations
│   ├── repository/         # Available plugins (not yet installed)
│   │   ├── code-quality/
│   │   ├── security-essentials/
│   │   └── python-developer/
│   └── installed/          # Installed plugins
│       ├── code-quality/
│       │   ├── plugin.yaml
│       │   ├── templates/
│       │   ├── hooks/
│       │   └── README.md
│       └── security-essentials/
```

### Plugin States

Plugins can be in one of several states:

- **AVAILABLE** - In repository but not installed
- **INSTALLED** - Installed but not active
- **ACTIVE** - Installed and active (features available)
- **DISABLED** - Installed but temporarily disabled
- **ERROR** - Has errors preventing activation

## Creating Plugins

### Basic Plugin Structure

```
my-plugin/
├── plugin.yaml         # Plugin manifest (required)
├── templates/          # Command templates
│   ├── template1.md
│   └── template2.md
├── hooks/              # Automation hooks
│   ├── pre-commit.sh
│   └── file-validator.py
├── agents/             # AI agents (future)
├── workflows/          # Workflow definitions (future)
└── README.md          # Plugin documentation
```

### Plugin Manifest

The `plugin.yaml` file defines plugin metadata and capabilities:

```yaml
metadata:
  name: my-plugin
  display_name: My Plugin
  version: "1.0.0"
  description: Description of what the plugin does
  author: Your Name
  license: MIT
  homepage: https://github.com/username/my-plugin
  category: general
  keywords:
    - productivity
    - automation

dependencies:
  - name: other-plugin
    version: "^1.0.0"
    optional: false

provides:
  templates:
    - my-template-1
    - my-template-2
  hooks:
    - pre-commit
    - file-validator
  agents: []
  workflows: []

requires_python: ">=3.8"

config_schema:
  api_key:
    type: string
    description: API key for external service
    required: false
```

### Version Format

Plugins use semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR** - Incompatible API changes
- **MINOR** - Backwards-compatible functionality additions
- **PATCH** - Backwards-compatible bug fixes

Version requirements support:
- `^1.0.0` - Compatible with 1.x.x (>=1.0.0, <2.0.0)
- `~1.2.0` - Compatible with 1.2.x (>=1.2.0, <1.3.0)
- `>=1.0.0` - Any version >= 1.0.0
- `1.0.0` - Exact version match

## Plugin Commands

### List Plugins

```bash
# List all plugins (installed and available)
claude-setup plugins list

# List only installed plugins
claude-setup plugins list --installed

# List only active plugins
claude-setup plugins list --active
```

### Add Plugins

```bash
# Add a plugin from the repository
claude-setup plugins add code-quality

# Add multiple plugins
claude-setup plugins add code-quality security-essentials

# Add a plugin from a file
claude-setup plugins add ./my-plugin.zip

# Add a plugin from a directory
claude-setup plugins add /path/to/plugin-directory
```

### Remove Plugins

```bash
# Remove a plugin
claude-setup plugins remove code-quality

# Force removal (ignore dependents)
claude-setup plugins remove code-quality --force
```

### Plugin Information

```bash
# Show detailed plugin information
claude-setup plugins info code-quality

# Show plugin dependencies
claude-setup plugins info code-quality --dependencies
```

### Activate/Deactivate Plugins

```bash
# Activate a plugin
claude-setup plugins activate code-quality

# Deactivate a plugin
claude-setup plugins deactivate code-quality
```

## Plugin Bundles

Bundles are collections of related plugins that work well together.

### Available Bundles

#### Essential Bundle
- **Plugins**: code-quality, security-essentials
- **Purpose**: Core tools for professional development

```bash
claude-setup plugins add bundle:essential
```

#### Python Full Stack Bundle
- **Plugins**: python-developer, code-quality, security-essentials
- **Purpose**: Complete Python development environment

```bash
claude-setup plugins add bundle:python-full-stack
```

### Bundle Definition

Bundles are defined in YAML files:

```yaml
name: my-bundle
display_name: My Bundle
description: A collection of related plugins
category: bundle

plugins:
  plugin-1: "^1.0.0"
  plugin-2: "^2.0.0"
  plugin-3: "~1.5.0"
```

## Example Plugins

### Code Quality Plugin

Provides templates and hooks for code quality:

```yaml
metadata:
  name: code-quality
  display_name: Code Quality Tools
  version: "1.0.0"
  description: Enhanced code review and quality assurance tools
  author: Claude Code Setup Team
  category: development

provides:
  templates:
    - code-review-checklist
    - performance-optimization
  hooks:
    - pre-commit-quality-check
```

### Security Essentials Plugin

Security-focused templates and validation:

```yaml
metadata:
  name: security-essentials
  display_name: Security Essentials
  version: "1.0.0"
  description: Essential security tools and validations
  author: Claude Code Setup Team
  category: security

provides:
  templates:
    - security-audit
    - vulnerability-assessment
  hooks:
    - secrets-scanner
    - security-validator
```

### Python Developer Plugin

Python-specific development tools:

```yaml
metadata:
  name: python-developer
  display_name: Python Developer Tools
  version: "1.0.0"
  description: Comprehensive Python development toolkit
  author: Claude Code Setup Team
  category: language

provides:
  templates:
    - python-project-setup
    - django-app-scaffolding
    - fastapi-microservice
  hooks:
    - python-linter
    - type-checker
```

## Developer Guide

### Creating a Plugin

1. **Create plugin directory structure**:
```bash
mkdir my-plugin
cd my-plugin
mkdir templates hooks
```

2. **Create plugin.yaml**:
```yaml
metadata:
  name: my-plugin
  display_name: My Awesome Plugin
  version: "1.0.0"
  description: Does awesome things
  author: Your Name
  category: productivity

provides:
  templates:
    - awesome-template
  hooks:
    - awesome-hook
```

3. **Add templates** in `templates/`:
```markdown
# templates/awesome-template.md

# Awesome Template

This template helps you do awesome things.

## Usage

Describe how to use this template.
```

4. **Add hooks** in `hooks/`:
```python
# hooks/awesome-hook.py
#!/usr/bin/env python3

import sys
import json

def main():
    # Hook logic here
    print("Hook executed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

5. **Test your plugin**:
```bash
# Install locally
claude-setup plugins add /path/to/my-plugin

# Verify installation
claude-setup plugins info my-plugin

# Test templates
claude-setup list templates
claude-setup add template my-plugin/awesome-template
```

### Plugin Templates

Plugin templates are namespaced to avoid conflicts:
- Core template: `code-review`
- Plugin template: `my-plugin/awesome-template`

When users select templates, plugin templates are clearly marked:
```
GENERAL TEMPLATES
  code-review             Review code for best practices
  [my-plugin] awesome     Does awesome things
```

### Plugin Hooks

Hooks from plugins are registered in settings.json when activated:
```json
{
  "hooks": [
    {
      "trigger": "pre_file_edit",
      "script": ".claude/plugins/installed/my-plugin/hooks/awesome-hook.py",
      "description": "Awesome validation",
      "plugin": "my-plugin"
    }
  ]
}
```

### Publishing Plugins

To share your plugin:

1. **Package as ZIP**:
```bash
zip -r my-plugin-1.0.0.zip my-plugin/
```

2. **Share via GitHub**:
```bash
git init
git add .
git commit -m "Initial plugin release"
git remote add origin https://github.com/username/my-plugin
git push -u origin main
```

3. **Submit to repository** (future):
- Fork the claude-code-setup repository
- Add your plugin to `src/plugins/repository/`
- Submit a pull request

### Best Practices

1. **Naming**:
   - Use lowercase with hyphens
   - Be descriptive but concise
   - Avoid generic names

2. **Versioning**:
   - Follow semantic versioning
   - Document breaking changes
   - Maintain backwards compatibility when possible

3. **Dependencies**:
   - Minimize dependencies
   - Use version ranges wisely
   - Mark optional dependencies

4. **Documentation**:
   - Include clear README
   - Document all templates and hooks
   - Provide usage examples

5. **Testing**:
   - Test on multiple platforms
   - Verify all paths are relative
   - Check dependency resolution

## Future Enhancements

The plugin system is designed to be extensible. Planned features include:

### Agent Framework (Coming Soon)
- AI-powered automation agents
- Custom agent definitions
- Agent composition and chaining

### Workflow Engine (Coming Soon)
- Multi-step automation workflows
- Conditional logic and branching
- Integration with templates and hooks

### Plugin Repository
- Central plugin repository
- Plugin discovery and search
- Ratings and reviews
- Automatic updates

### Enhanced Integration
- Hook system integration ✓
- Settings management integration
- Cross-plugin communication
- Plugin configuration UI

## Troubleshooting

### Common Issues

**Plugin not loading**:
- Check `plugin.yaml` syntax
- Verify required fields are present
- Check file permissions

**Dependency conflicts**:
- Review version requirements
- Check for circular dependencies
- Use `--force` to override

**Template not found**:
- Ensure plugin is activated
- Check template file exists
- Verify template name in manifest

### Debug Commands

```bash
# Check plugin status
claude-setup plugins info my-plugin

# View plugin registry
cat ~/.claude/plugins/registry.json

# Check logs
claude-setup plugins list --verbose
```

## Contributing

To contribute to the plugin system:

1. **Report issues**: GitHub issues for bugs or features
2. **Submit plugins**: Pull requests to add to repository
3. **Improve docs**: Documentation improvements welcome
4. **Test plugins**: Help test across platforms

## License

The plugin system is part of Claude Code Setup and follows the same MIT license. Individual plugins may have their own licenses as specified in their manifests.