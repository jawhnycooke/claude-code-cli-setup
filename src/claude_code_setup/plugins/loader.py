"""Plugin loader for discovering and loading plugins.

This module handles plugin discovery, validation, loading, and activation
within the Claude Code Setup plugin system.
"""

import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml
from pydantic import ValidationError

from ..exceptions import ClaudeSetupError
from ..utils.fs import ensure_directory
from ..utils.logger import debug, error, info, warning
from .registry import PluginRegistry
from .types import Plugin, PluginManifest, PluginStatus
from ..utils.plugin_hook_loader import (
    register_plugin_hooks_in_settings,
    unregister_plugin_hooks_from_settings,
    validate_plugin_hooks,
)


class PluginLoadError(ClaudeSetupError):
    """Plugin loading specific errors."""
    pass


class PluginLoader:
    """Loads and manages plugins from various sources."""
    
    def __init__(self, 
                 plugin_dir: Path,
                 registry: PluginRegistry) -> None:
        """Initialize plugin loader.
        
        Args:
            plugin_dir: Base directory for plugins (usually .claude/plugins)
            registry: Plugin registry instance
        """
        self.plugin_dir = plugin_dir
        self.registry = registry
        
        # Create plugin directory structure
        self.repository_dir = plugin_dir / "repository"
        self.installed_dir = plugin_dir / "installed"
        self.temp_dir = plugin_dir / "temp"
        
        ensure_directory(self.repository_dir)
        ensure_directory(self.installed_dir)
        ensure_directory(self.temp_dir)
    
    def discover_repository_plugins(self) -> Dict[str, Plugin]:
        """Discover available plugins from the repository.
        
        Returns:
            Dictionary of discovered plugins by name
        """
        discovered = {}
        
        # Look for plugin manifests in repository
        for manifest_path in self.repository_dir.glob("*/plugin.yaml"):
            try:
                plugin = self._load_plugin_manifest(manifest_path)
                plugin.status = PluginStatus.AVAILABLE
                discovered[plugin.name] = plugin
                debug(f"Discovered plugin: {plugin.name} v{plugin.version}")
            except Exception as e:
                error(f"Failed to load plugin from {manifest_path}: {e}")
        
        info(f"Discovered {len(discovered)} plugins in repository")
        return discovered
    
    def discover_installed_plugins(self) -> Dict[str, Plugin]:
        """Discover installed plugins.
        
        Returns:
            Dictionary of installed plugins by name
        """
        installed = {}
        
        # Look for installed plugins
        for plugin_path in self.installed_dir.iterdir():
            if not plugin_path.is_dir():
                continue
                
            manifest_path = plugin_path / "plugin.yaml"
            if manifest_path.exists():
                try:
                    plugin = self._load_plugin_manifest(manifest_path)
                    plugin.status = PluginStatus.INSTALLED
                    plugin.install_path = str(plugin_path)
                    
                    # Check for installation metadata
                    install_info_path = plugin_path / ".install.json"
                    if install_info_path.exists():
                        try:
                            import json
                            with open(install_info_path) as f:
                                install_info = json.load(f)
                            plugin.install_date = datetime.fromisoformat(
                                install_info.get("date", datetime.utcnow().isoformat())
                            )
                        except Exception:
                            pass
                    
                    installed[plugin.name] = plugin
                    debug(f"Found installed plugin: {plugin.name} v{plugin.version}")
                except Exception as e:
                    error(f"Failed to load installed plugin from {plugin_path}: {e}")
        
        info(f"Found {len(installed)} installed plugins")
        return installed
    
    def sync_with_registry(self) -> None:
        """Sync discovered plugins with registry."""
        # Discover all plugins
        repository_plugins = self.discover_repository_plugins()
        installed_plugins = self.discover_installed_plugins()
        
        # Update registry
        all_plugins = {**repository_plugins}
        
        # Installed plugins override repository versions
        for name, plugin in installed_plugins.items():
            all_plugins[name] = plugin
        
        # Register all plugins
        for plugin in all_plugins.values():
            try:
                existing = self.registry.get_plugin(plugin.name)
                if existing:
                    # Update existing plugin info but preserve status
                    plugin.status = existing.status
                    if existing.is_active:
                        plugin.status = PluginStatus.ACTIVE
                    plugin.config = existing.config
                    plugin.errors = existing.errors
                
                self.registry.register_plugin(plugin)
            except Exception as e:
                error(f"Failed to register plugin {plugin.name}: {e}")
    
    def install_plugin(self, plugin_name: str) -> Plugin:
        """Install a plugin from the repository.
        
        Args:
            plugin_name: Name of plugin to install
            
        Returns:
            Installed plugin
            
        Raises:
            PluginLoadError: If installation fails
        """
        # Get plugin from registry
        plugin = self.registry.get_plugin(plugin_name)
        if not plugin:
            raise PluginLoadError(f"Plugin {plugin_name} not found")
        
        if plugin.is_installed:
            raise PluginLoadError(f"Plugin {plugin_name} is already installed")
        
        # Check dependencies
        deps_ok, dep_errors = self.registry.check_dependencies(plugin)
        if not deps_ok:
            raise PluginLoadError(
                f"Cannot install {plugin_name}: Dependencies not met:\n" +
                "\n".join(dep_errors)
            )
        
        # Install from repository
        source_path = self.repository_dir / plugin_name
        if not source_path.exists():
            raise PluginLoadError(
                f"Plugin source not found at {source_path}"
            )
        
        target_path = self.installed_dir / plugin_name
        
        try:
            # Copy plugin files
            if target_path.exists():
                shutil.rmtree(target_path)
            shutil.copytree(source_path, target_path)
            
            # Create installation metadata
            import json
            install_info = {
                "date": datetime.utcnow().isoformat(),
                "version": plugin.version,
                "source": "repository"
            }
            with open(target_path / ".install.json", "w") as f:
                json.dump(install_info, f, indent=2)
            
            # Update plugin status
            plugin.status = PluginStatus.INSTALLED
            plugin.install_path = str(target_path)
            plugin.install_date = datetime.utcnow()
            
            self.registry.register_plugin(plugin)
            info(f"Installed plugin: {plugin_name} v{plugin.version}")
            
            return plugin
            
        except Exception as e:
            # Clean up on failure
            if target_path.exists():
                shutil.rmtree(target_path)
            raise PluginLoadError(f"Failed to install {plugin_name}: {e}")
    
    def uninstall_plugin(self, plugin_name: str, force: bool = False) -> None:
        """Uninstall a plugin.
        
        Args:
            plugin_name: Plugin to uninstall
            force: Force uninstall even if other plugins depend on it
            
        Raises:
            PluginLoadError: If uninstall fails
        """
        plugin = self.registry.get_plugin(plugin_name)
        if not plugin or not plugin.is_installed:
            raise PluginLoadError(f"Plugin {plugin_name} is not installed")
        
        # Check for dependents
        if not force:
            dependents = self.registry.get_dependents(plugin_name)
            if dependents:
                dep_names = [p.name for p in dependents]
                raise PluginLoadError(
                    f"Cannot uninstall {plugin_name}: Other plugins depend on it: "
                    f"{', '.join(dep_names)}"
                )
        
        # Remove plugin files
        if plugin.install_path:
            install_path = Path(plugin.install_path)
            if install_path.exists():
                shutil.rmtree(install_path)
        
        # Update registry
        plugin.status = PluginStatus.AVAILABLE
        plugin.install_path = None
        plugin.install_date = None
        self.registry.register_plugin(plugin)
        
        info(f"Uninstalled plugin: {plugin_name}")
    
    def activate_plugin(self, plugin_name: str) -> None:
        """Activate an installed plugin.
        
        Args:
            plugin_name: Plugin to activate
            
        Raises:
            PluginLoadError: If activation fails
        """
        plugin = self.registry.get_plugin(plugin_name)
        if not plugin:
            raise PluginLoadError(f"Plugin {plugin_name} not found")
        
        if not plugin.is_installed:
            raise PluginLoadError(f"Plugin {plugin_name} is not installed")
        
        if plugin.is_active:
            warning(f"Plugin {plugin_name} is already active")
            return
        
        # Validate plugin can be activated
        errors = self._validate_plugin_activation(plugin)
        if errors:
            raise PluginLoadError(
                f"Cannot activate {plugin_name}:\n" + "\n".join(errors)
            )
        
        # Register plugin hooks if any
        if plugin.manifest.provides.hooks and plugin.install_path:
            settings_file = self.plugin_dir.parent / "settings.json"
            plugin_path = Path(plugin.install_path)
            hooks_registered = register_plugin_hooks_in_settings(
                plugin_name, plugin_path, settings_file
            )
            if hooks_registered > 0:
                info(f"Registered {hooks_registered} hooks from {plugin_name}")
        
        # Activate plugin
        self.registry.update_plugin_status(plugin_name, PluginStatus.ACTIVE)
        info(f"Activated plugin: {plugin_name}")
    
    def deactivate_plugin(self, plugin_name: str) -> None:
        """Deactivate a plugin.
        
        Args:
            plugin_name: Plugin to deactivate
        """
        plugin = self.registry.get_plugin(plugin_name)
        if not plugin or not plugin.is_active:
            warning(f"Plugin {plugin_name} is not active")
            return
        
        # Unregister plugin hooks if any
        if plugin.manifest.provides.hooks:
            settings_file = self.plugin_dir.parent / "settings.json"
            hooks_removed = unregister_plugin_hooks_from_settings(
                plugin_name, settings_file
            )
            if hooks_removed > 0:
                info(f"Removed {hooks_removed} hooks from {plugin_name}")
        
        self.registry.update_plugin_status(plugin_name, PluginStatus.DISABLED)
        info(f"Deactivated plugin: {plugin_name}")
    
    def install_from_file(self, plugin_path: Path) -> Plugin:
        """Install a plugin from a file (zip or directory).
        
        Args:
            plugin_path: Path to plugin file or directory
            
        Returns:
            Installed plugin
            
        Raises:
            PluginLoadError: If installation fails
        """
        if not plugin_path.exists():
            raise PluginLoadError(f"Plugin path does not exist: {plugin_path}")
        
        # Extract to temporary directory if zip
        if plugin_path.is_file() and plugin_path.suffix == ".zip":
            temp_extract = self.temp_dir / f"extract_{plugin_path.stem}"
            if temp_extract.exists():
                shutil.rmtree(temp_extract)
            
            try:
                with zipfile.ZipFile(plugin_path, 'r') as zf:
                    zf.extractall(temp_extract)
                
                # Find plugin.yaml
                manifest_paths = list(temp_extract.glob("**/plugin.yaml"))
                if not manifest_paths:
                    raise PluginLoadError("No plugin.yaml found in archive")
                
                plugin_dir = manifest_paths[0].parent
                
            except Exception as e:
                if temp_extract.exists():
                    shutil.rmtree(temp_extract)
                raise PluginLoadError(f"Failed to extract plugin: {e}")
        
        elif plugin_path.is_dir():
            plugin_dir = plugin_path
        else:
            raise PluginLoadError(
                f"Invalid plugin path: {plugin_path} (must be directory or .zip)"
            )
        
        # Load and validate plugin
        manifest_path = plugin_dir / "plugin.yaml"
        if not manifest_path.exists():
            raise PluginLoadError(f"No plugin.yaml found in {plugin_dir}")
        
        try:
            plugin = self._load_plugin_manifest(manifest_path)
            
            # Check if already installed
            existing = self.registry.get_plugin(plugin.name)
            if existing and existing.is_installed:
                raise PluginLoadError(
                    f"Plugin {plugin.name} is already installed"
                )
            
            # Install to plugins directory
            target_path = self.installed_dir / plugin.name
            if target_path.exists():
                shutil.rmtree(target_path)
            
            shutil.copytree(plugin_dir, target_path)
            
            # Create installation metadata
            import json
            install_info = {
                "date": datetime.utcnow().isoformat(),
                "version": plugin.version,
                "source": str(plugin_path)
            }
            with open(target_path / ".install.json", "w") as f:
                json.dump(install_info, f, indent=2)
            
            # Update plugin
            plugin.status = PluginStatus.INSTALLED
            plugin.install_path = str(target_path)
            plugin.install_date = datetime.utcnow()
            
            self.registry.register_plugin(plugin)
            info(f"Installed plugin from file: {plugin.name} v{plugin.version}")
            
            return plugin
            
        finally:
            # Clean up temporary files
            if 'temp_extract' in locals() and temp_extract.exists():
                shutil.rmtree(temp_extract)
    
    def _load_plugin_manifest(self, manifest_path: Path) -> Plugin:
        """Load plugin manifest from file.
        
        Args:
            manifest_path: Path to plugin.yaml
            
        Returns:
            Loaded plugin
            
        Raises:
            PluginLoadError: If manifest is invalid
        """
        try:
            content = manifest_path.read_text(encoding='utf-8')
            data = yaml.safe_load(content)
            
            if not data:
                raise PluginLoadError("Empty plugin manifest")
            
            # Convert flat format to nested format if needed
            if "name" in data and "metadata" not in data:
                # Old flat format - convert to new format
                metadata = {
                    "name": data.get("name"),
                    "display_name": data.get("display_name", data.get("name")),
                    "version": data.get("version"),
                    "description": data.get("description"),
                    "author": data.get("author"),
                    "license": data.get("license", "MIT"),
                    "homepage": data.get("homepage"),
                    "repository": data.get("repository"),
                    "keywords": data.get("keywords", []),
                    "category": data.get("category", "general"),
                }
                
                manifest_data = {
                    "metadata": metadata,
                    "dependencies": data.get("dependencies", []),
                    "provides": data.get("provides", {}),
                    "requires_python": data.get("requires_python"),
                    "config_schema": data.get("config_schema"),
                }
            else:
                manifest_data = data
            
            manifest = PluginManifest.model_validate(manifest_data)
            
            return Plugin(manifest=manifest)
            
        except yaml.YAMLError as e:
            raise PluginLoadError(f"Invalid YAML in plugin manifest: {e}")
        except ValidationError as e:
            raise PluginLoadError(f"Invalid plugin manifest: {e}")
        except Exception as e:
            raise PluginLoadError(f"Failed to load plugin manifest: {e}")
    
    def _validate_plugin_activation(self, plugin: Plugin) -> List[str]:
        """Validate a plugin can be activated.
        
        Args:
            plugin: Plugin to validate
            
        Returns:
            List of error messages
        """
        errors = []
        
        # Check dependencies
        deps_ok, dep_errors = self.registry.check_dependencies(plugin)
        if not deps_ok:
            errors.extend(dep_errors)
        
        # Validate plugin hooks if any
        if plugin.manifest.provides.hooks and plugin.install_path:
            plugin_path = Path(plugin.install_path)
            hook_errors = validate_plugin_hooks(plugin_path)
            if hook_errors:
                errors.extend([f"Hook validation: {e}" for e in hook_errors])
        
        # Check for conflicts
        active_plugins = self.registry.get_active_plugins()
        for active_name, active_plugin in active_plugins.items():
            # Check if plugins provide conflicting capabilities
            # This is a simplified check - could be more sophisticated
            if active_name != plugin.name:
                active_caps = active_plugin.manifest.provides
                plugin_caps = plugin.manifest.provides
                
                # Check for duplicate template names
                common_templates = set(active_caps.templates) & set(plugin_caps.templates)
                if common_templates:
                    errors.append(
                        f"Template conflicts with {active_name}: "
                        f"{', '.join(common_templates)}"
                    )
        
        return errors