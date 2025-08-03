"""Test plugin-template integration."""

import tempfile
from pathlib import Path
import yaml
import json

import pytest
from claude_code_setup.plugins.registry import PluginRegistry
from claude_code_setup.plugins.loader import PluginLoader
from claude_code_setup.plugins.types import PluginManifest, PluginCapabilities, PluginVersion
from claude_code_setup.utils.plugin_template_loader import (
    get_all_templates_with_plugins,
    load_plugin_templates,
)


def create_test_plugin(plugin_dir: Path, plugin_name: str):
    """Create a test plugin with templates."""
    plugin_dir.mkdir(parents=True, exist_ok=True)
    
    # Create manifest
    manifest = {
        "metadata": {
            "name": plugin_name,
            "display_name": f"Test {plugin_name}",
            "description": f"Test plugin {plugin_name}",
            "version": "1.0.0",
            "author": "Test Author",
            "category": "testing"
        },
        "provides": {
            "templates": ["test-template-1", "test-template-2"],
            "hooks": [],
            "agents": [],
            "workflows": []
        },
        "dependencies": []
    }
    
    manifest_file = plugin_dir / "plugin.yaml"
    with open(manifest_file, "w") as f:
        yaml.dump(manifest, f)
    
    # Create templates directory
    templates_dir = plugin_dir / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    # Create test templates
    template1 = templates_dir / "test-template-1.md"
    template1.write_text("""# Test Template 1

This is a test template from the plugin.

## Usage

Example usage here.
""")
    
    template2 = templates_dir / "test-template-2.md"
    template2.write_text("""# Test Template 2

Another test template.

## Details

More details here.
""")


def test_load_plugin_templates():
    """Test loading templates from a plugin directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        plugin_dir = Path(temp_dir) / "test-plugin"
        create_test_plugin(plugin_dir, "test-plugin")
        
        # Load templates from plugin
        templates = load_plugin_templates(plugin_dir)
        
        assert len(templates) == 2
        assert "test-plugin/test-template-1" in templates
        assert "test-plugin/test-template-2" in templates
        
        # Check template properties
        template1 = templates["test-plugin/test-template-1"]
        assert template1.name == "test-plugin/test-template-1"
        assert "[Plugin: test-plugin]" in template1.description
        assert "Test Template 1" in template1.description
        assert "This is a test template" in template1.content


def test_get_all_templates_with_plugins():
    """Test getting all templates including plugin templates."""
    with tempfile.TemporaryDirectory() as temp_dir:
        plugins_dir = Path(temp_dir) / "plugins"
        plugins_dir.mkdir()
        
        # Create registry
        registry_file = plugins_dir / "registry.json"
        registry = PluginRegistry(registry_file)
        
        # Create and install test plugins
        installed_dir = plugins_dir / "installed"
        installed_dir.mkdir()
        
        plugin1_dir = installed_dir / "test-plugin-1"
        create_test_plugin(plugin1_dir, "test-plugin-1")
        
        plugin2_dir = installed_dir / "test-plugin-2" 
        create_test_plugin(plugin2_dir, "test-plugin-2")
        
        # Use loader to discover plugins
        loader = PluginLoader(plugins_dir, registry)
        # Since we created the plugins directly, we need to sync with registry
        loader.discover_installed_plugins()
        loader.sync_with_registry()
        
        # Activate plugins
        loader.activate_plugin("test-plugin-1")
        loader.activate_plugin("test-plugin-2")
        
        # Get all templates
        template_registry = get_all_templates_with_plugins(registry)
        
        # Check that we have both core and plugin templates
        template_names = list(template_registry.templates.keys())
        
        # Should have plugin templates
        assert any("test-plugin-1/" in name for name in template_names)
        assert any("test-plugin-2/" in name for name in template_names)
        
        # Should still have core templates (without '/' in name)
        assert any("/" not in name for name in template_names)


def test_plugin_template_naming():
    """Test that plugin templates have proper naming convention."""
    with tempfile.TemporaryDirectory() as temp_dir:
        plugin_dir = Path(temp_dir) / "my-plugin"
        create_test_plugin(plugin_dir, "my-plugin")
        
        templates = load_plugin_templates(plugin_dir)
        
        # All templates should be prefixed with plugin name
        for template_name in templates.keys():
            assert template_name.startswith("my-plugin/")
            
        # Descriptions should indicate they're from a plugin
        for template in templates.values():
            assert "[Plugin: my-plugin]" in template.description


def test_empty_plugin_templates_dir():
    """Test plugin with no templates directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        plugin_dir = Path(temp_dir) / "empty-plugin"
        plugin_dir.mkdir()
        
        # Create manifest without templates dir
        manifest = {
            "metadata": {
                "name": "empty-plugin",
                "display_name": "Empty Plugin",
                "description": "Plugin with no templates",
                "version": "1.0.0",
                "author": "Test",
                "category": "testing"
            },
            "provides": {"templates": [], "hooks": [], "agents": [], "workflows": []},
            "dependencies": []
        }
        
        with open(plugin_dir / "plugin.yaml", "w") as f:
            yaml.dump(manifest, f)
        
        # Should return empty dict
        templates = load_plugin_templates(plugin_dir)
        assert templates == {}


def test_plugin_template_conflict_handling():
    """Test handling of template name conflicts."""
    with tempfile.TemporaryDirectory() as temp_dir:
        plugins_dir = Path(temp_dir) / "plugins"
        plugins_dir.mkdir()
        
        registry_file = plugins_dir / "registry.json"
        registry = PluginRegistry(registry_file)
        
        # Create two plugins with same template names
        installed_dir = plugins_dir / "installed"
        installed_dir.mkdir()
        
        for i in [1, 2]:
            plugin_dir = installed_dir / f"plugin-{i}"
            plugin_dir.mkdir()
            
            manifest = {
                "metadata": {
                    "name": f"plugin-{i}",
                    "display_name": f"Plugin {i}",
                    "description": f"Test plugin {i}",
                    "version": "1.0.0",
                    "author": "Test",
                    "category": "testing"
                },
                "provides": {"templates": ["same-template"], "hooks": [], "agents": [], "workflows": []},
                "dependencies": []
            }
            
            with open(plugin_dir / "plugin.yaml", "w") as f:
                yaml.dump(manifest, f)
            
            templates_dir = plugin_dir / "templates"
            templates_dir.mkdir()
            
            template_file = templates_dir / "same-template.md"
            template_file.write_text(f"# Template from Plugin {i}")
        
        # Load plugins
        loader = PluginLoader(plugins_dir, registry)
        # Since we created the plugins directly, we need to sync with registry
        loader.discover_installed_plugins()
        loader.sync_with_registry()
        
        # Activate both plugins
        loader.activate_plugin("plugin-1")
        loader.activate_plugin("plugin-2")
        
        # Get all templates - should have unique names due to plugin prefix
        template_registry = get_all_templates_with_plugins(registry)
        
        assert "plugin-1/same-template" in template_registry.templates
        assert "plugin-2/same-template" in template_registry.templates
        
        # Both should be different templates
        t1 = template_registry.templates["plugin-1/same-template"]
        t2 = template_registry.templates["plugin-2/same-template"]
        assert t1.content != t2.content