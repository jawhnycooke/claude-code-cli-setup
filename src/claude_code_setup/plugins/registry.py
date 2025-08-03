"""Plugin registry for managing installed and available plugins.

This module provides a centralized registry for tracking plugin installations,
versions, dependencies, and status.
"""

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from pydantic import ValidationError

from ..exceptions import ClaudeSetupError
from ..utils.fs import ensure_directory, read_json_file, write_json_file
from ..utils.logger import debug, error, info, warning
from .types import (
    Plugin,
    PluginBundle,
    PluginManifest,
    PluginStatus,
    PluginVersion,
)


class PluginRegistryError(ClaudeSetupError):
    """Plugin registry specific errors."""
    pass


class PluginRegistry:
    """Central registry for managing plugins."""
    
    def __init__(self, registry_path: Path) -> None:
        """Initialize plugin registry.
        
        Args:
            registry_path: Path to registry file (usually .claude/plugins/registry.json)
        """
        self.registry_path = registry_path
        self._plugins: Dict[str, Plugin] = {}
        self._bundles: Dict[str, PluginBundle] = {}
        self._lock = threading.RLock()
        self._loaded = False
        
        # Ensure registry directory exists
        ensure_directory(registry_path.parent)
    
    def load(self) -> None:
        """Load registry from disk."""
        with self._lock:
            if self._loaded:
                return
            
            if self.registry_path.exists():
                try:
                    data = read_json_file(self.registry_path)
                    
                    # Load plugins
                    for plugin_data in data.get("plugins", []):
                        try:
                            plugin = Plugin.model_validate(plugin_data)
                            self._plugins[plugin.name] = plugin
                        except ValidationError as e:
                            error(f"Invalid plugin data: {e}")
                    
                    # Load bundles
                    for bundle_data in data.get("bundles", []):
                        try:
                            bundle = PluginBundle.model_validate(bundle_data)
                            self._bundles[bundle.name] = bundle
                        except ValidationError as e:
                            error(f"Invalid bundle data: {e}")
                    
                    info(f"Loaded {len(self._plugins)} plugins from registry")
                    
                except Exception as e:
                    error(f"Failed to load plugin registry: {e}")
                    # Start with empty registry on error
                    self._plugins = {}
                    self._bundles = {}
            
            self._loaded = True
    
    def save(self) -> None:
        """Save registry to disk."""
        with self._lock:
            data = {
                "version": "1.0.0",
                "updated": datetime.utcnow().isoformat(),
                "plugins": [
                    plugin.model_dump(mode="json")
                    for plugin in self._plugins.values()
                ],
                "bundles": [
                    bundle.model_dump(mode="json")
                    for bundle in self._bundles.values()
                ],
            }
            
            try:
                write_json_file(self.registry_path, data)
                debug(f"Saved plugin registry with {len(self._plugins)} plugins")
            except Exception as e:
                raise PluginRegistryError(f"Failed to save registry: {e}")
    
    def register_plugin(self, plugin: Plugin) -> None:
        """Register a plugin in the registry.
        
        Args:
            plugin: Plugin to register
        """
        with self._lock:
            self.load()
            
            # Check for conflicts
            if plugin.name in self._plugins:
                existing = self._plugins[plugin.name]
                if existing.is_installed and plugin.is_installed:
                    raise PluginRegistryError(
                        f"Plugin {plugin.name} is already installed"
                    )
            
            self._plugins[plugin.name] = plugin
            self.save()
            info(f"Registered plugin: {plugin.name} v{plugin.version}")
    
    def unregister_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Remove a plugin from the registry.
        
        Args:
            plugin_name: Name of plugin to remove
            
        Returns:
            Removed plugin or None if not found
        """
        with self._lock:
            self.load()
            
            plugin = self._plugins.pop(plugin_name, None)
            if plugin:
                self.save()
                info(f"Unregistered plugin: {plugin_name}")
            
            return plugin
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin or None if not found
        """
        with self._lock:
            self.load()
            return self._plugins.get(name)
    
    def get_installed_plugins(self) -> Dict[str, Plugin]:
        """Get all installed plugins.
        
        Returns:
            Dictionary of installed plugins by name
        """
        with self._lock:
            self.load()
            return {
                name: plugin
                for name, plugin in self._plugins.items()
                if plugin.is_installed
            }
    
    def get_active_plugins(self) -> Dict[str, Plugin]:
        """Get all active plugins.
        
        Returns:
            Dictionary of active plugins by name
        """
        with self._lock:
            self.load()
            return {
                name: plugin
                for name, plugin in self._plugins.items()
                if plugin.is_active
            }
    
    def get_available_plugins(self) -> Dict[str, Plugin]:
        """Get all available (not installed) plugins.
        
        Returns:
            Dictionary of available plugins by name
        """
        with self._lock:
            self.load()
            return {
                name: plugin
                for name, plugin in self._plugins.items()
                if plugin.status == PluginStatus.AVAILABLE
            }
    
    def update_plugin_status(
        self, 
        plugin_name: str, 
        status: PluginStatus,
        errors: Optional[List[str]] = None
    ) -> None:
        """Update plugin status.
        
        Args:
            plugin_name: Plugin to update
            status: New status
            errors: Optional error messages
        """
        with self._lock:
            self.load()
            
            plugin = self._plugins.get(plugin_name)
            if not plugin:
                raise PluginRegistryError(f"Plugin {plugin_name} not found")
            
            plugin.status = status
            if errors:
                plugin.errors = errors
            elif status == PluginStatus.ACTIVE:
                plugin.errors = []  # Clear errors on activation
                
            self.save()
            debug(f"Updated plugin {plugin_name} status to {status}")
    
    def check_dependencies(self, plugin: Plugin) -> Tuple[bool, List[str]]:
        """Check if plugin dependencies are satisfied.
        
        Args:
            plugin: Plugin to check
            
        Returns:
            Tuple of (all_satisfied, list_of_errors)
        """
        with self._lock:
            self.load()
            
            installed = self.get_installed_plugins()
            errors = plugin.manifest.validate_dependencies(installed)
            
            return len(errors) == 0, errors
    
    def get_dependents(self, plugin_name: str) -> List[Plugin]:
        """Get plugins that depend on the given plugin.
        
        Args:
            plugin_name: Plugin to check dependents for
            
        Returns:
            List of dependent plugins
        """
        with self._lock:
            self.load()
            
            dependents = []
            for plugin in self.get_installed_plugins().values():
                for dep in plugin.manifest.dependencies:
                    if dep.name == plugin_name and not dep.optional:
                        dependents.append(plugin)
                        break
            
            return dependents
    
    def register_bundle(self, bundle: PluginBundle) -> None:
        """Register a plugin bundle.
        
        Args:
            bundle: Bundle to register
        """
        with self._lock:
            self.load()
            
            self._bundles[bundle.name] = bundle
            self.save()
            info(f"Registered bundle: {bundle.name}")
    
    def get_bundle(self, name: str) -> Optional[PluginBundle]:
        """Get a bundle by name.
        
        Args:
            name: Bundle name
            
        Returns:
            Bundle or None if not found
        """
        with self._lock:
            self.load()
            return self._bundles.get(name)
    
    def get_all_bundles(self) -> Dict[str, PluginBundle]:
        """Get all registered bundles.
        
        Returns:
            Dictionary of bundles by name
        """
        with self._lock:
            self.load()
            return self._bundles.copy()
    
    def resolve_bundle(self, bundle: PluginBundle) -> Tuple[List[Plugin], List[str]]:
        """Resolve bundle to list of plugins to install.
        
        Args:
            bundle: Bundle to resolve
            
        Returns:
            Tuple of (plugins_to_install, error_messages)
        """
        with self._lock:
            self.load()
            
            plugins_to_install = []
            errors = []
            
            for plugin_name, version_req in bundle.plugins.items():
                plugin = self.get_plugin(plugin_name)
                
                if not plugin:
                    errors.append(f"Plugin {plugin_name} not found in registry")
                    continue
                
                # Check version requirement
                plugin_version = plugin.manifest.metadata.get_version()
                if not plugin_version.satisfies(version_req):
                    errors.append(
                        f"Plugin {plugin_name} version {plugin_version} "
                        f"does not satisfy bundle requirement {version_req}"
                    )
                    continue
                
                # Check if already installed
                if not plugin.is_installed:
                    plugins_to_install.append(plugin)
            
            return plugins_to_install, errors
    
    def get_stats(self) -> Dict[str, int]:
        """Get registry statistics.
        
        Returns:
            Dictionary with counts by status
        """
        with self._lock:
            self.load()
            
            stats = {
                "total": len(self._plugins),
                "available": 0,
                "installed": 0,
                "active": 0,
                "disabled": 0,
                "error": 0,
                "bundles": len(self._bundles),
            }
            
            for plugin in self._plugins.values():
                stats[plugin.status.value] += 1
            
            return stats