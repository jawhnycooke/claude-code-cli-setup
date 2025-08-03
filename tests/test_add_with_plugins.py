"""Test add command with plugin templates."""

import tempfile
from pathlib import Path
import yaml

import pytest
from click.testing import CliRunner

from claude_code_setup.cli import cli
from claude_code_setup.plugins.registry import PluginRegistry
from claude_code_setup.plugins.loader import PluginLoader


def create_test_plugin_with_templates(plugin_dir: Path):
    """Create a test plugin with templates."""
    plugin_dir.mkdir(parents=True, exist_ok=True)
    
    # Create plugin manifest
    manifest = {
        "metadata": {
            "name": "test-plugin",
            "display_name": "Test Plugin",
            "description": "Plugin with test templates",
            "version": "1.0.0",
            "author": "Test",
            "category": "testing"
        },
        "provides": {
            "templates": ["test-template"],
            "hooks": [],
            "agents": [],
            "workflows": []
        },
        "dependencies": []
    }
    
    with open(plugin_dir / "plugin.yaml", "w") as f:
        yaml.dump(manifest, f)
    
    # Create templates directory
    templates_dir = plugin_dir / "templates"
    templates_dir.mkdir()
    
    # Create a test template
    template_file = templates_dir / "test-template.md"
    template_file.write_text("""# Test Template

This is a test template from a plugin.

## Description

Demonstrates plugin template functionality.

## Usage

```bash
claude-setup add template test-plugin/test-template
```
""")


def test_add_command_discovers_plugin_templates():
    """Test that add command discovers templates from active plugins."""
    runner = CliRunner()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize claude setup
        result = runner.invoke(cli, ["init", "--test-dir", temp_dir, "--quick"])
        assert result.exit_code == 0
        
        # Create plugin structure
        claude_dir = Path(temp_dir) / ".claude"
        plugins_dir = claude_dir / "plugins"
        installed_dir = plugins_dir / "installed"
        installed_dir.mkdir(parents=True, exist_ok=True)
        
        # Create and install test plugin
        plugin_dir = installed_dir / "test-plugin"
        create_test_plugin_with_templates(plugin_dir)
        
        # Create registry and loader
        registry_file = plugins_dir / "registry.json"
        registry = PluginRegistry(registry_file)
        loader = PluginLoader(plugins_dir, registry)
        
        # Discover and activate plugin
        loader.discover_installed_plugins()
        loader.sync_with_registry()
        loader.activate_plugin("test-plugin")
        
        # Now run list command to see if plugin templates are discovered
        result = runner.invoke(cli, ["list", "templates", "--test-dir", temp_dir])
        assert result.exit_code == 0
        
        # Check that plugin template is listed
        assert "test-plugin" in result.output
        assert "Test Template" in result.output


def test_add_plugin_template_installation():
    """Test installing a template from a plugin."""
    runner = CliRunner()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize claude setup
        result = runner.invoke(cli, ["init", "--test-dir", temp_dir, "--quick"])
        assert result.exit_code == 0
        
        # Create plugin structure
        claude_dir = Path(temp_dir) / ".claude"
        plugins_dir = claude_dir / "plugins"
        installed_dir = plugins_dir / "installed"
        installed_dir.mkdir(parents=True, exist_ok=True)
        
        # Create and install test plugin
        plugin_dir = installed_dir / "test-plugin"
        create_test_plugin_with_templates(plugin_dir)
        
        # Create registry and loader
        registry_file = plugins_dir / "registry.json"
        registry = PluginRegistry(registry_file)
        loader = PluginLoader(plugins_dir, registry)
        
        # Discover and activate plugin
        loader.discover_installed_plugins()
        loader.sync_with_registry()
        loader.activate_plugin("test-plugin")
        
        # Install the plugin template
        result = runner.invoke(cli, [
            "add", "template", "test-plugin/test-template",
            "--test-dir", temp_dir,
            "--force"
        ])
        assert result.exit_code == 0
        
        # Verify template was installed
        commands_dir = claude_dir / "commands"
        installed_template = commands_dir / "test-plugin" / "test-template.md"
        assert installed_template.exists()
        
        # Verify content
        content = installed_template.read_text()
        assert "Test Template" in content
        assert "plugin template functionality" in content