# Plugin API Reference

This document provides a technical reference for the Claude Code Setup Plugin API.

## Plugin Types

### PluginVersion

Represents a semantic version with comparison capabilities.

```python
class PluginVersion:
    major: int  # Major version number (>=0)
    minor: int  # Minor version number (>=0)
    patch: int  # Patch version number (>=0)
    
    def satisfies(self, requirement: str) -> bool:
        """Check if version satisfies a requirement."""
    
    @classmethod
    def from_string(cls, version_str: str) -> PluginVersion:
        """Parse version from string like '1.2.3'."""
```

### PluginMetadata

Core plugin information.

```python
class PluginMetadata:
    name: str               # Unique identifier (lowercase, hyphens)
    display_name: str       # Human-readable name
    version: str           # Version string (e.g., "1.0.0")
    description: str       # Plugin description
    author: str           # Author name
    license: str = "MIT"  # License identifier
    homepage: Optional[str]  # Plugin website
    repository: Optional[str]  # Source repository
    keywords: List[str]    # Search keywords
    category: str         # Plugin category
```

### PluginCapabilities

What the plugin provides.

```python
class PluginCapabilities:
    templates: List[str]   # Template names
    hooks: List[str]      # Hook names
    agents: List[str]     # Agent names (future)
    workflows: List[str]  # Workflow names (future)
```

### PluginManifest

Complete plugin manifest structure.

```python
class PluginManifest:
    metadata: PluginMetadata
    dependencies: List[PluginDependency]
    provides: PluginCapabilities
    requires_python: Optional[str]
    config_schema: Optional[Dict]
```

### Plugin

Complete plugin with runtime information.

```python
class Plugin:
    manifest: PluginManifest
    status: PluginStatus
    install_path: Optional[str]
    install_date: Optional[datetime]
    config: Dict
    errors: List[str]
    
    @property
    def name(self) -> str
    
    @property
    def version(self) -> str
    
    @property
    def is_installed(self) -> bool
    
    @property
    def is_active(self) -> bool
```

### PluginStatus

Plugin state enumeration.

```python
class PluginStatus(Enum):
    AVAILABLE = "available"      # In repository
    INSTALLED = "installed"      # Installed locally
    ACTIVE = "active"           # Installed and active
    DISABLED = "disabled"       # Installed but disabled
    ERROR = "error"            # Has errors
```

## Plugin Registry API

### PluginRegistry

Central registry for managing plugins.

```python
class PluginRegistry:
    def __init__(self, registry_path: Path) -> None:
        """Initialize registry with path to registry.json."""
    
    def load(self) -> None:
        """Load registry from disk."""
    
    def save(self) -> None:
        """Save registry to disk."""
    
    def register_plugin(self, plugin: Plugin) -> None:
        """Register a new plugin."""
    
    def unregister_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Remove plugin from registry."""
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get plugin by name."""
    
    def get_installed_plugins(self) -> Dict[str, Plugin]:
        """Get all installed plugins."""
    
    def get_active_plugins(self) -> Dict[str, Plugin]:
        """Get all active plugins."""
    
    def update_plugin_status(
        self,
        plugin_name: str,
        status: PluginStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """Update plugin status."""
    
    def check_dependencies(
        self,
        plugin: Plugin
    ) -> Tuple[bool, List[str]]:
        """Check if dependencies are satisfied."""
    
    def get_dependents(self, plugin_name: str) -> List[Plugin]:
        """Get plugins that depend on this plugin."""
```

## Plugin Loader API

### PluginLoader

Handles plugin discovery and loading.

```python
class PluginLoader:
    def __init__(
        self,
        plugin_dir: Path,
        registry: PluginRegistry
    ) -> None:
        """Initialize loader with plugin directory and registry."""
    
    def discover_repository_plugins(self) -> Dict[str, Plugin]:
        """Discover plugins in repository directory."""
    
    def discover_installed_plugins(self) -> Dict[str, Plugin]:
        """Discover installed plugins."""
    
    def sync_with_registry(self) -> None:
        """Sync discovered plugins with registry."""
    
    def install_plugin(self, plugin_name: str) -> Plugin:
        """Install plugin from repository."""
    
    def uninstall_plugin(
        self,
        plugin_name: str,
        force: bool = False
    ) -> None:
        """Uninstall plugin."""
    
    def activate_plugin(self, plugin_name: str) -> None:
        """Activate an installed plugin."""
    
    def deactivate_plugin(self, plugin_name: str) -> None:
        """Deactivate a plugin."""
    
    def install_from_file(self, plugin_path: Path) -> Plugin:
        """Install plugin from file or directory."""
```

## Plugin Template Integration

### get_all_templates_with_plugins

Get templates including those from active plugins.

```python
def get_all_templates_with_plugins(
    registry: PluginRegistry,
    force_reload: bool = False
) -> TemplateRegistry:
    """
    Load all templates including plugin templates.
    
    Plugin templates are namespaced as: plugin-name/template-name
    """
```

### load_plugin_templates

Load templates from a specific plugin.

```python
def load_plugin_templates(plugin_dir: Path) -> Dict[str, Template]:
    """
    Load templates from plugin's templates/ directory.
    
    Returns dict mapping namespaced names to Template objects.
    """
```

## Hook Registration

When a plugin with hooks is activated, they are registered in settings.json:

```json
{
  "hooks": [
    {
      "trigger": "pre_file_edit",
      "script": ".claude/plugins/installed/my-plugin/hooks/validator.py",
      "description": "Validate files",
      "plugin": "my-plugin",
      "enabled": true
    }
  ]
}
```

## Plugin CLI Commands

### List Command
```python
@plugins_group.command()
@click.option("--installed", is_flag=True)
@click.option("--active", is_flag=True)
@click.option("--available", is_flag=True)
def list(installed: bool, active: bool, available: bool) -> None:
    """List plugins with filtering options."""
```

### Add Command
```python
@plugins_group.command()
@click.argument("plugin_names", nargs=-1, required=True)
@click.option("--force", is_flag=True)
def add(plugin_names: Tuple[str, ...], force: bool) -> None:
    """Install one or more plugins."""
```

### Remove Command
```python
@plugins_group.command()
@click.argument("plugin_name")
@click.option("--force", is_flag=True)
def remove(plugin_name: str, force: bool) -> None:
    """Uninstall a plugin."""
```

### Info Command
```python
@plugins_group.command()
@click.argument("plugin_name")
@click.option("--dependencies", is_flag=True)
def info(plugin_name: str, dependencies: bool) -> None:
    """Show detailed plugin information."""
```

### Activate/Deactivate Commands
```python
@plugins_group.command()
@click.argument("plugin_name")
def activate(plugin_name: str) -> None:
    """Activate an installed plugin."""

@plugins_group.command()
@click.argument("plugin_name")
def deactivate(plugin_name: str) -> None:
    """Deactivate a plugin."""
```

## Error Handling

### PluginLoadError
Raised when plugin loading fails.

```python
class PluginLoadError(ClaudeSetupError):
    """Plugin loading specific errors."""
```

### PluginRegistryError
Raised for registry operations.

```python
class PluginRegistryError(ClaudeSetupError):
    """Plugin registry specific errors."""
```

## Future API Extensions

### Agent API (Planned)
```python
class PluginAgent:
    name: str
    description: str
    capabilities: List[str]
    entry_point: str
```

### Workflow API (Planned)
```python
class PluginWorkflow:
    name: str
    description: str
    steps: List[WorkflowStep]
    triggers: List[str]
```

### Event System (Planned)
```python
class PluginEventEmitter:
    def emit(self, event: str, data: Dict) -> None
    def on(self, event: str, handler: Callable) -> None
```