"""Plugin-aware hook loader.

This module extends the hook loading functionality to include hooks
provided by activated plugins.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..plugins.registry import PluginRegistry
from ..plugins.types import PluginStatus
from ..types import Hook, HookRegistry, HookEvent, HookConfig
from ..utils.logger import debug, warning, info
from ..utils.hook import get_all_hooks_sync
from ..utils.fs import read_json_file, write_json_file


def load_plugin_hooks(plugin_dir: Path) -> Dict[str, Hook]:
    """Load hooks from a plugin directory.
    
    Args:
        plugin_dir: Path to the plugin directory
        
    Returns:
        Dictionary of hooks by name
    """
    hooks = {}
    hooks_dir = plugin_dir / "hooks"
    
    if not hooks_dir.exists():
        return hooks
    
    # Load all hook files in hooks directory
    for hook_file in hooks_dir.iterdir():
        if hook_file.is_file() and hook_file.suffix in ['.py', '.sh', '.js']:
            try:
                name = hook_file.stem
                plugin_name = plugin_dir.name
                
                # Create unique hook key with plugin prefix
                hook_key = f"{plugin_name}/{name}"
                
                # Determine hook trigger from name or metadata
                trigger = determine_hook_trigger(name, hook_file)
                
                # Map trigger to HookEvent
                event = map_trigger_to_event(trigger)
                
                hooks[hook_key] = Hook(
                    name=hook_key,
                    description=f"[Plugin: {plugin_name}] {name} hook",
                    category="plugin",
                    event=event,
                    config=HookConfig(
                        type="command",
                        command=str(hook_file)
                    ),
                    scripts={hook_file.name: hook_file.read_text(encoding='utf-8')}
                )
                
            except Exception as e:
                warning(f"Failed to load plugin hook {hook_file}: {e}")
    
    return hooks


def map_trigger_to_event(trigger: str) -> HookEvent:
    """Map trigger string to HookEvent enum.
    
    Args:
        trigger: Trigger string
        
    Returns:
        HookEvent enum value
    """
    mapping = {
        'pre_command': HookEvent.USER_PROMPT_SUBMIT,
        'post_command': HookEvent.POST_TOOL_USE,
        'pre_file_edit': HookEvent.PRE_TOOL_USE,
        'post_file_edit': HookEvent.POST_TOOL_USE,
        'pre_tool': HookEvent.PRE_TOOL_USE,
        'post_tool': HookEvent.POST_TOOL_USE,
    }
    return mapping.get(trigger, HookEvent.PRE_TOOL_USE)


def determine_hook_trigger(name: str, hook_file: Path) -> str:
    """Determine the hook trigger from name or file content.
    
    Args:
        name: Hook file name (without extension)
        hook_file: Path to hook file
        
    Returns:
        Hook trigger type
    """
    # Common trigger patterns
    trigger_patterns = {
        'pre-commit': 'pre_command',
        'post-commit': 'post_command',
        'pre-file': 'pre_file_edit',
        'post-file': 'post_file_edit',
        'file-validator': 'pre_file_edit',
        'command-validator': 'pre_command',
        'security': 'pre_file_edit',
    }
    
    # Check if name matches known patterns
    for pattern, trigger in trigger_patterns.items():
        if pattern in name.lower():
            return trigger
    
    # Try to read trigger from file header comment
    try:
        content = hook_file.read_text(encoding='utf-8')
        lines = content.split('\n')[:10]  # Check first 10 lines
        
        for line in lines:
            if 'trigger:' in line.lower():
                # Extract trigger from comment like "# trigger: pre_file_edit"
                parts = line.split('trigger:', 1)
                if len(parts) > 1:
                    return parts[1].strip().strip('"\'')
    except Exception:
        pass
    
    # Default trigger
    return 'pre_file_edit'


def get_all_hooks_with_plugins(
    registry: PluginRegistry,
    force_reload: bool = False
) -> HookRegistry:
    """Get all hooks including those from active plugins.
    
    Args:
        registry: Plugin registry instance
        force_reload: Force reload hooks
        
    Returns:
        HookRegistry with core and plugin hooks
    """
    # Load core hooks
    core_registry = get_all_hooks_sync()
    all_hooks = dict(core_registry.hooks)
    
    # Load hooks from active plugins
    active_plugins = registry.get_active_plugins()
    
    for plugin_name, plugin in active_plugins.items():
        if not plugin.install_path:
            continue
            
        plugin_dir = Path(plugin.install_path)
        if not plugin_dir.exists():
            warning(f"Plugin directory not found: {plugin_dir}")
            continue
        
        # Check if plugin provides hooks
        if not plugin.manifest.provides.hooks:
            continue
        
        debug(f"Loading hooks from plugin: {plugin_name}")
        plugin_hooks = load_plugin_hooks(plugin_dir)
        
        # Merge plugin hooks
        for hook_key, hook in plugin_hooks.items():
            if hook_key in all_hooks:
                warning(f"Plugin hook {hook_key} conflicts with existing hook")
            else:
                all_hooks[hook_key] = hook
        
        debug(f"Loaded {len(plugin_hooks)} hooks from {plugin_name}")
    
    return HookRegistry(hooks=all_hooks)


def register_plugin_hooks_in_settings(
    plugin_name: str,
    plugin_dir: Path,
    settings_file: Path
) -> int:
    """Register plugin hooks in settings.json.
    
    Args:
        plugin_name: Name of the plugin
        plugin_dir: Plugin installation directory
        settings_file: Path to settings.json
        
    Returns:
        Number of hooks registered
    """
    # Load plugin hooks
    plugin_hooks = load_plugin_hooks(plugin_dir)
    
    if not plugin_hooks:
        return 0
    
    # Load current settings
    try:
        settings = read_json_file(settings_file)
    except FileNotFoundError:
        settings = {}
    
    # Ensure hooks array exists
    if 'hooks' not in settings:
        settings['hooks'] = []
    
    # Convert existing hooks to dict for easier lookup
    existing_hooks = {h.get('script'): h for h in settings['hooks']}
    
    # Add plugin hooks
    registered = 0
    for hook_key, hook in plugin_hooks.items():
        hook_entry = {
            "trigger": hook.event.value,  # Use the event value
            "script": str(Path(plugin_dir) / "hooks" / Path(hook.config.command).name),
            "description": hook.description,
            "plugin": plugin_name,
            "enabled": True
        }
        
        # Check if hook already registered
        if hook_entry['script'] not in existing_hooks:
            settings['hooks'].append(hook_entry)
            registered += 1
            info(f"Registered hook: {hook_key}")
    
    # Save updated settings
    if registered > 0:
        write_json_file(settings_file, settings)
        info(f"Registered {registered} hooks from plugin {plugin_name}")
    
    return registered


def unregister_plugin_hooks_from_settings(
    plugin_name: str,
    settings_file: Path
) -> int:
    """Remove plugin hooks from settings.json.
    
    Args:
        plugin_name: Name of the plugin
        settings_file: Path to settings.json
        
    Returns:
        Number of hooks removed
    """
    try:
        settings = read_json_file(settings_file)
    except FileNotFoundError:
        return 0
    
    if 'hooks' not in settings:
        return 0
    
    # Filter out hooks from this plugin
    original_count = len(settings['hooks'])
    settings['hooks'] = [
        h for h in settings['hooks']
        if h.get('plugin') != plugin_name
    ]
    
    removed = original_count - len(settings['hooks'])
    
    if removed > 0:
        write_json_file(settings_file, settings)
        info(f"Removed {removed} hooks from plugin {plugin_name}")
    
    return removed


def validate_plugin_hooks(plugin_dir: Path) -> List[str]:
    """Validate plugin hooks are properly configured.
    
    Args:
        plugin_dir: Plugin directory
        
    Returns:
        List of validation errors
    """
    errors = []
    hooks_dir = plugin_dir / "hooks"
    
    if not hooks_dir.exists():
        return errors
    
    for hook_file in hooks_dir.iterdir():
        if hook_file.is_file() and hook_file.suffix in ['.py', '.sh', '.js']:
            # Check if file is executable
            if not hook_file.stat().st_mode & 0o111:
                errors.append(f"Hook {hook_file.name} is not executable")
            
            # Check shebang for scripts
            try:
                first_line = hook_file.read_text().split('\n')[0]
                if hook_file.suffix in ['.py', '.sh'] and not first_line.startswith('#!'):
                    errors.append(f"Hook {hook_file.name} missing shebang line")
            except Exception as e:
                errors.append(f"Cannot read hook {hook_file.name}: {e}")
    
    return errors