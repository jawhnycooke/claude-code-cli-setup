"""Plugin-aware template loader.

This module extends the template loading functionality to include templates
provided by activated plugins.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional

from ..plugins.registry import PluginRegistry
from ..plugins.types import PluginStatus
from ..types import Template, TemplateCategory, TemplateRegistry
from .logger import debug, warning
from .template import load_templates_from_files_sync, _category_string_to_enum


def load_plugin_templates(plugin_dir: Path) -> Dict[str, Template]:
    """Load templates from a plugin directory.
    
    Args:
        plugin_dir: Path to the plugin directory
        
    Returns:
        Dictionary of templates by name
    """
    templates = {}
    templates_dir = plugin_dir / "templates"
    
    if not templates_dir.exists():
        return templates
    
    # Load all .md files in templates directory
    for template_file in templates_dir.glob("*.md"):
        try:
            content = template_file.read_text(encoding='utf-8')
            
            if not content.strip():
                warning(f"Empty template file: {template_file}")
                continue
            
            name = template_file.stem
            plugin_name = plugin_dir.name
            
            # Create unique template key with plugin prefix
            template_key = f"{plugin_name}/{name}"
            
            # Extract description from content
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            description = title_match.group(1) if title_match else f"{plugin_name} {name}"
            
            # Use general category for plugin templates
            # Could be enhanced to read category from plugin metadata
            category = TemplateCategory.GENERAL
            
            templates[template_key] = Template(
                name=template_key,
                description=f"[Plugin: {plugin_name}] {description}",
                category=category,
                content=content
            )
            
        except Exception as e:
            warning(f"Failed to load plugin template {template_file}: {e}")
    
    return templates


def get_all_templates_with_plugins(
    registry: PluginRegistry,
    force_reload: bool = False
) -> TemplateRegistry:
    """Get all templates including those from active plugins.
    
    Args:
        registry: Plugin registry instance
        force_reload: Force reload templates
        
    Returns:
        TemplateRegistry with core and plugin templates
    """
    # Load core templates
    core_registry = load_templates_from_files_sync()
    all_templates = dict(core_registry.templates)
    
    # Load templates from active plugins
    active_plugins = registry.get_active_plugins()
    
    for plugin_name, plugin in active_plugins.items():
        if not plugin.install_path:
            continue
            
        plugin_dir = Path(plugin.install_path)
        if not plugin_dir.exists():
            warning(f"Plugin directory not found: {plugin_dir}")
            continue
        
        # Check if plugin provides templates
        if not plugin.manifest.provides.templates:
            continue
        
        debug(f"Loading templates from plugin: {plugin_name}")
        plugin_templates = load_plugin_templates(plugin_dir)
        
        # Merge plugin templates
        for template_key, template in plugin_templates.items():
            if template_key in all_templates:
                warning(f"Plugin template {template_key} conflicts with existing template")
            else:
                all_templates[template_key] = template
        
        debug(f"Loaded {len(plugin_templates)} templates from {plugin_name}")
    
    return TemplateRegistry(templates=all_templates)


def filter_templates_by_plugin(
    templates: Dict[str, Template],
    plugin_name: Optional[str] = None
) -> Dict[str, Template]:
    """Filter templates by plugin name.
    
    Args:
        templates: All templates
        plugin_name: Plugin name to filter by (None for core templates)
        
    Returns:
        Filtered templates
    """
    if plugin_name is None:
        # Return core templates (no plugin prefix)
        return {
            name: template
            for name, template in templates.items()
            if '/' not in name
        }
    else:
        # Return templates from specific plugin
        prefix = f"{plugin_name}/"
        return {
            name: template
            for name, template in templates.items()
            if name.startswith(prefix)
        }