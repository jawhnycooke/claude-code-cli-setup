# Plugin Development Guide

This guide provides detailed information for developers creating plugins for Claude Code Setup.

## Quick Start

### 1. Generate Plugin Scaffold

```bash
# Create a new plugin directory
mkdir my-awesome-plugin
cd my-awesome-plugin

# Create the basic structure
mkdir -p templates hooks agents workflows
touch plugin.yaml README.md
```

### 2. Define Plugin Manifest

Create `plugin.yaml`:

```yaml
metadata:
  name: my-awesome-plugin
  display_name: My Awesome Plugin
  version: "1.0.0"
  description: A plugin that adds awesome functionality
  author: Your Name
  license: MIT
  homepage: https://github.com/yourusername/my-awesome-plugin
  category: productivity
  keywords:
    - awesome
    - productivity
    - automation

dependencies: []

provides:
  templates:
    - awesome-starter
    - awesome-advanced
  hooks:
    - pre-commit-awesome
  agents: []
  workflows: []

requires_python: ">=3.8"
```

### 3. Create Templates

Add templates in `templates/` directory:

```markdown
# templates/awesome-starter.md

# Awesome Starter Template

This template helps you get started with awesome development.

## Purpose

Explain what this template is for and when to use it.

## Usage

```bash
# How to use this template
claude-setup add template my-awesome-plugin/awesome-starter
```

## Configuration

Describe any configuration options or customization points.

## Examples

Provide concrete examples of using this template.
```

### 4. Create Hooks

Add hooks in `hooks/` directory:

```python
#!/usr/bin/env python3
# hooks/pre-commit-awesome.py

import sys
import json
from pathlib import Path

def validate_awesome(file_path):
    """Validate that the file is awesome enough."""
    content = Path(file_path).read_text()
    
    if "awesome" not in content.lower():
        return False, "File needs more awesome!"
    
    return True, "File is awesome!"

def main():
    # Read hook input
    if len(sys.argv) < 2:
        print("Usage: pre-commit-awesome.py <file>")
        return 1
    
    file_path = sys.argv[1]
    
    # Validate
    is_valid, message = validate_awesome(file_path)
    
    # Output result
    result = {
        "valid": is_valid,
        "message": message
    }
    
    print(json.dumps(result))
    return 0 if is_valid else 1

if __name__ == "__main__":
    sys.exit(main())
```

Make the hook executable:
```bash
chmod +x hooks/pre-commit-awesome.py
```

## Plugin Structure

### Complete Plugin Layout

```
my-plugin/
├── plugin.yaml           # Plugin manifest (required)
├── README.md            # Plugin documentation (recommended)
├── LICENSE              # License file (recommended)
├── templates/           # Command templates
│   ├── template1.md
│   ├── template2.md
│   └── README.md       # Templates documentation
├── hooks/               # Automation hooks
│   ├── hook1.py
│   ├── hook2.sh
│   └── README.md       # Hooks documentation
├── agents/              # AI agents (future)
│   └── README.md       # Agents documentation
├── workflows/           # Workflow definitions (future)
│   └── README.md       # Workflows documentation
├── config/              # Default configurations
│   └── defaults.json   # Default plugin settings
└── tests/               # Plugin tests
    ├── test_templates.py
    └── test_hooks.py
```

## Plugin Manifest Reference

### Complete Manifest Example

```yaml
# Required: Plugin metadata
metadata:
  name: my-plugin                    # Unique identifier (lowercase, hyphens)
  display_name: My Plugin            # Human-readable name
  version: "1.0.0"                   # Semantic version (required)
  description: Plugin description    # Clear, concise description
  author: Your Name                  # Author name (required)
  license: MIT                       # License identifier
  homepage: https://example.com      # Plugin homepage
  repository: https://github.com/... # Source repository
  category: development              # Plugin category
  keywords:                          # Search keywords
    - keyword1
    - keyword2
  
# Optional: Plugin dependencies
dependencies:
  - name: other-plugin               # Dependency plugin name
    version: "^1.0.0"               # Version requirement
    optional: false                  # Whether optional
    
# Required: What the plugin provides
provides:
  templates:                         # Template names (without .md)
    - template-name-1
    - template-name-2
  hooks:                            # Hook names (without extension)
    - hook-name-1
    - hook-name-2
  agents: []                        # Future: Agent names
  workflows: []                     # Future: Workflow names

# Optional: Requirements
requires_python: ">=3.8"            # Python version requirement
requires_claude_version: ">=0.12.0" # Claude Code Setup version

# Optional: Configuration schema
config_schema:
  api_key:
    type: string
    description: API key for service
    required: false
    default: ""
  max_retries:
    type: integer
    description: Maximum retry attempts
    required: false
    default: 3
    minimum: 1
    maximum: 10
```

### Metadata Fields

| Field | Required | Description |
|-------|----------|-------------|
| name | Yes | Unique plugin identifier (lowercase, hyphens only) |
| display_name | Yes | Human-readable plugin name |
| version | Yes | Semantic version string (e.g., "1.0.0") |
| description | Yes | Brief description of plugin functionality |
| author | Yes | Plugin author name |
| license | No | License identifier (e.g., MIT, Apache-2.0) |
| homepage | No | Plugin website or documentation URL |
| repository | No | Source code repository URL |
| category | Yes | Plugin category (see categories below) |
| keywords | No | List of search keywords |

### Categories

- **development** - General development tools
- **language** - Language-specific tools (Python, Node.js, etc.)
- **security** - Security and compliance tools
- **testing** - Testing and quality assurance
- **productivity** - Productivity enhancements
- **ai** - AI and machine learning tools
- **infrastructure** - Infrastructure and DevOps
- **general** - General purpose tools

## Templates

### Template Guidelines

1. **Naming Convention**:
   - Use descriptive, lowercase names with hyphens
   - Avoid generic names like "template" or "default"
   - Examples: `django-rest-api`, `react-component`, `security-audit`

2. **Template Structure**:
   ```markdown
   # Template Title
   
   Brief description of what this template does.
   
   ## When to Use
   
   Explain scenarios where this template is helpful.
   
   ## Prerequisites
   
   - List any requirements
   - Tools needed
   - Knowledge required
   
   ## Usage
   
   Step-by-step instructions for using the template.
   
   ## Configuration
   
   Explain any variables or options.
   
   ## Examples
   
   Provide concrete examples.
   
   ## Troubleshooting
   
   Common issues and solutions.
   ```

3. **Template Variables**:
   - Use `{{variable_name}}` for replaceable content
   - Document all variables in the template
   - Provide sensible defaults

### Template Best Practices

- **Be Specific**: Templates should solve specific problems
- **Include Examples**: Show real-world usage
- **Document Prerequisites**: Clear about requirements
- **Test Thoroughly**: Verify on different systems
- **Version Appropriately**: Update version for changes

## Hooks

### Hook Types

1. **File Hooks**:
   - `pre_file_edit` - Before file modification
   - `post_file_edit` - After file modification
   - `pre_file_create` - Before file creation
   - `post_file_create` - After file creation

2. **Command Hooks**:
   - `pre_command` - Before command execution
   - `post_command` - After command execution

3. **Tool Hooks**:
   - `pre_tool_*` - Before specific tool use
   - `post_tool_*` - After specific tool use

### Hook Interface

Hooks receive input via:
- **Command line arguments**: File paths, command details
- **Environment variables**: Context information
- **Standard input**: JSON data for complex inputs

Hooks output via:
- **Exit code**: 0 for success, non-zero for failure
- **Standard output**: JSON response or text
- **Standard error**: Error messages

### Hook Examples

#### Python Hook

```python
#!/usr/bin/env python3
import sys
import json
import os

def main():
    # Get input from environment
    file_path = os.environ.get('CLAUDE_FILE_PATH')
    action = os.environ.get('CLAUDE_ACTION')
    
    # Get input from stdin
    try:
        input_data = json.loads(sys.stdin.read())
    except:
        input_data = {}
    
    # Perform validation/action
    result = {
        "status": "success",
        "message": "Hook executed successfully",
        "data": {
            "file": file_path,
            "action": action
        }
    }
    
    # Output result
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

#### Shell Hook

```bash
#!/bin/bash

# Get inputs
FILE_PATH="$1"
ACTION="$2"

# Validate file
if [[ ! -f "$FILE_PATH" ]]; then
    echo "Error: File not found: $FILE_PATH" >&2
    exit 1
fi

# Perform checks
if grep -q "TODO" "$FILE_PATH"; then
    echo "Warning: File contains TODO items"
fi

# Success
echo "File validated successfully"
exit 0
```

### Hook Registration

When a plugin is activated, hooks are registered in `settings.json`:

```json
{
  "hooks": [
    {
      "trigger": "pre_file_edit",
      "script": ".claude/plugins/installed/my-plugin/hooks/validator.py",
      "description": "Validate file before editing",
      "plugin": "my-plugin",
      "enabled": true
    }
  ]
}
```

## Testing Plugins

### Unit Tests

Create tests in `tests/` directory:

```python
# tests/test_templates.py
import pytest
from pathlib import Path

def test_template_files_exist():
    """Test that all declared templates exist."""
    plugin_dir = Path(__file__).parent.parent
    templates_dir = plugin_dir / "templates"
    
    # List of declared templates from plugin.yaml
    declared_templates = ["awesome-starter", "awesome-advanced"]
    
    for template in declared_templates:
        template_file = templates_dir / f"{template}.md"
        assert template_file.exists(), f"Template {template} not found"

def test_template_content():
    """Test template content is valid."""
    plugin_dir = Path(__file__).parent.parent
    template_file = plugin_dir / "templates" / "awesome-starter.md"
    
    content = template_file.read_text()
    assert "# Awesome Starter Template" in content
    assert "## Usage" in content
```

### Integration Tests

Test plugin installation and activation:

```python
# tests/test_integration.py
import tempfile
import shutil
from pathlib import Path

def test_plugin_installation():
    """Test plugin can be installed."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy plugin to temp location
        plugin_source = Path(__file__).parent.parent
        plugin_dest = Path(temp_dir) / "my-plugin"
        shutil.copytree(plugin_source, plugin_dest)
        
        # Simulate installation
        # ... installation logic ...
        
        assert plugin_dest.exists()
```

### Manual Testing

1. **Install locally**:
   ```bash
   claude-setup plugins add /path/to/your/plugin
   ```

2. **Verify installation**:
   ```bash
   claude-setup plugins info your-plugin
   ```

3. **Test templates**:
   ```bash
   claude-setup list templates
   claude-setup add template your-plugin/template-name
   ```

4. **Test hooks**:
   ```bash
   # Trigger hook by performing action
   # Check logs for hook execution
   ```

## Publishing Plugins

### 1. Prepare for Release

- **Version appropriately**: Update version in `plugin.yaml`
- **Update documentation**: Ensure README is current
- **Test thoroughly**: Run all tests
- **Add changelog**: Document changes

### 2. Package Plugin

```bash
# Create distribution archive
cd my-plugin
zip -r ../my-plugin-1.0.0.zip . -x "*.git*" -x "*__pycache__*" -x "*.pyc"

# Or create tarball
tar -czf ../my-plugin-1.0.0.tar.gz --exclude='.git' --exclude='__pycache__' .
```

### 3. Distribute

#### GitHub Release

1. Create GitHub repository
2. Push code
3. Create release with archive

```bash
# Tag version
git tag v1.0.0
git push origin v1.0.0

# Create release on GitHub
# Upload my-plugin-1.0.0.zip
```

#### Direct Distribution

Share the archive file directly:
```bash
# Users can install with
claude-setup plugins add ./my-plugin-1.0.0.zip
```

## Advanced Topics

### Dynamic Configuration

Plugins can provide dynamic configuration:

```python
# config/generate_config.py
import json
import os

def generate_config():
    """Generate configuration based on environment."""
    config = {
        "api_endpoint": os.getenv("API_ENDPOINT", "https://api.example.com"),
        "timeout": int(os.getenv("TIMEOUT", "30"))
    }
    
    return config

if __name__ == "__main__":
    config = generate_config()
    print(json.dumps(config, indent=2))
```

### Cross-Plugin Communication

Plugins can depend on and use features from other plugins:

```yaml
dependencies:
  - name: base-plugin
    version: "^1.0.0"

# In templates, reference base plugin templates
# In hooks, can call base plugin hooks
```

### Conditional Features

Enable features based on environment:

```python
# hooks/conditional_hook.py
import sys
import shutil

def main():
    # Check if required tool is available
    if not shutil.which("docker"):
        print("Docker not found, skipping Docker validation")
        return 0
    
    # Proceed with Docker-specific validation
    # ...
```

## Troubleshooting

### Common Issues

1. **Plugin not loading**:
   - Check YAML syntax: `yamllint plugin.yaml`
   - Verify required fields
   - Check file permissions

2. **Templates not found**:
   - Ensure templates are listed in `provides.templates`
   - Check file names match exactly
   - Verify .md extension

3. **Hooks not executing**:
   - Make hooks executable: `chmod +x hooks/*.py`
   - Check shebang line is correct
   - Verify hook is listed in manifest

4. **Dependency issues**:
   - Check version syntax
   - Verify dependencies exist
   - Look for circular dependencies

### Debug Techniques

1. **Enable verbose logging**:
   ```bash
   claude-setup --debug plugins add my-plugin
   ```

2. **Check plugin state**:
   ```bash
   cat ~/.claude/plugins/registry.json | jq '.plugins["my-plugin"]'
   ```

3. **Test hooks manually**:
   ```bash
   cd ~/.claude/plugins/installed/my-plugin
   ./hooks/my-hook.py test-input
   ```

## Best Practices Summary

1. **Start Small**: Begin with one template or hook
2. **Document Everything**: Clear README and inline docs
3. **Test Thoroughly**: Unit and integration tests
4. **Version Carefully**: Follow semantic versioning
5. **Consider Users**: Make installation and usage simple
6. **Handle Errors**: Graceful degradation
7. **Stay Compatible**: Test on multiple platforms
8. **Provide Examples**: Show real-world usage
9. **Maintain Actively**: Respond to issues
10. **Share Knowledge**: Contribute back to community