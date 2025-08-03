"""Settings utilities for claude-code-setup.

This module provides settings loading, validation, merging, and persistence functionality,
converted from TypeScript settings.ts. Uses importlib.resources to access
bundled settings files and Pydantic models for validation.
"""

import json
from pathlib import Path
from typing import Any, Optional

try:
    # Python 3.9+
    from importlib.resources import files
except ImportError:
    # Python 3.8 fallback
    try:
        from importlib_resources import files  # type: ignore
    except ImportError:
        files = None  # type: ignore

from ..types import ClaudeSettings, PermissionsSettings, SettingsHooks, HookSettings, HookConfig, Hook, HookEvent
from .fs import CLAUDE_SETTINGS_FILE
from .logger import error as log_error, warning as log_warning


def get_settings_directory() -> Path:
    """Get the settings directory path from the package resources.
    
    Returns:
        Path to the settings directory within the package
    """
    # Get settings directory from package resources
    package_settings = files("claude_code_setup") / "settings"
    return Path(str(package_settings))


async def load_all_permissions() -> list[str]:
    """Load all available permission sets from settings/permissions directory.
    
    Returns:
        List of permission strings with Bash() prefix
    """
    permission_sets: list[str] = []
    
    try:
        # Get permissions from package resources
        permissions_package = files("claude_code_setup") / "settings" / "permissions"
        
        if not permissions_package.is_dir():
            log_error("Permissions directory not found in package")
            return []
        
        # Read all permission files
        for permission_file in permissions_package.iterdir():
            if not permission_file.name.endswith('.json'):
                continue
            
            try:
                # Read and parse permission file
                content = json.loads(permission_file.read_text(encoding='utf-8'))
                
                # Validate permission set structure
                if 'bash' in content and isinstance(content['bash'], list):
                    # Add prefixed permissions
                    for perm in content['bash']:
                        permission_sets.append(f"Bash({perm})")
                        
            except json.JSONDecodeError as error:
                log_warning(f"Invalid JSON in {permission_file.name}: {error}")
            except Exception as error:
                log_warning(f"Error loading permission set from {permission_file.name}: {error}")
        
        return permission_sets
        
    except Exception as error:
        log_error(f"Error loading permissions: {error}")
        return []


def load_all_permissions_sync() -> list[str]:
    """Synchronous version of load_all_permissions.
    
    Returns:
        List of permission strings with Bash() prefix
    """
    permission_sets: list[str] = []
    
    try:
        # Get permissions from package resources
        permissions_package = files("claude_code_setup") / "settings" / "permissions"
        
        if not permissions_package.is_dir():
            log_error("Permissions directory not found in package")
            return []
        
        # Read all permission files
        for permission_file in permissions_package.iterdir():
            if not permission_file.name.endswith('.json'):
                continue
            
            try:
                # Read and parse permission file
                content = json.loads(permission_file.read_text(encoding='utf-8'))
                
                # Validate permission set structure
                if 'bash' in content and isinstance(content['bash'], list):
                    # Add prefixed permissions
                    for perm in content['bash']:
                        permission_sets.append(f"Bash({perm})")
                        
            except json.JSONDecodeError as error:
                log_warning(f"Invalid JSON in {permission_file.name}: {error}")
            except Exception as error:
                log_warning(f"Error loading permission set from {permission_file.name}: {error}")
        
        return permission_sets
        
    except Exception as error:
        log_error(f"Error loading permissions: {error}")
        return []


async def load_theme(theme_name: str = "default") -> Optional[dict[str, Any]]:
    """Load a theme by name.
    
    Args:
        theme_name: Name of the theme to load
        
    Returns:
        Theme data dictionary, or None if not found
    """
    try:
        # Get theme from package resources
        themes_package = files("claude_code_setup") / "settings" / "themes"
        theme_file = themes_package / f"{theme_name}.json"
        
        if theme_file.is_file():
            content = theme_file.read_text(encoding='utf-8')
            theme_data: dict[str, Any] = json.loads(content)
            return theme_data
        
        return None
        
    except Exception as error:
        log_error(f"Error loading theme {theme_name}: {error}")
        return None


def load_theme_sync(theme_name: str = "default") -> Optional[dict[str, Any]]:
    """Synchronous version of load_theme.
    
    Args:
        theme_name: Name of the theme to load
        
    Returns:
        Theme data dictionary, or None if not found
    """
    try:
        # Get theme from package resources
        themes_package = files("claude_code_setup") / "settings" / "themes"
        theme_file = themes_package / f"{theme_name}.json"
        
        if theme_file.is_file():
            content = theme_file.read_text(encoding='utf-8')
            theme_data: dict[str, Any] = json.loads(content)
            return theme_data
        
        return None
        
    except Exception as error:
        log_error(f"Error loading theme {theme_name}: {error}")
        return None


async def load_default_settings() -> dict[str, Any]:
    """Load default settings from package resources.
    
    Returns:
        Default settings dictionary
    """
    try:
        # Get defaults from package resources
        settings_package = files("claude_code_setup") / "settings"
        defaults_file = settings_package / "defaults.json"
        
        if defaults_file.is_file():
            content = defaults_file.read_text(encoding='utf-8')
            defaults: dict[str, Any] = json.loads(content)
            return defaults
        
        return {}
        
    except Exception as error:
        log_error(f"Error loading default settings: {error}")
        return {}


def load_default_settings_sync() -> dict[str, Any]:
    """Synchronous version of load_default_settings.
    
    Returns:
        Default settings dictionary
    """
    try:
        # Get defaults from package resources
        settings_package = files("claude_code_setup") / "settings"
        defaults_file = settings_package / "defaults.json"
        
        if defaults_file.is_file():
            content = defaults_file.read_text(encoding='utf-8')
            defaults: dict[str, Any] = json.loads(content)
            return defaults
        
        return {}
        
    except Exception as error:
        log_error(f"Error loading default settings: {error}")
        return {}


async def get_settings(
    permission_sets: Optional[list[str]] = None,
    theme: Optional[str] = None
) -> ClaudeSettings:
    """Build the complete settings object.
    
    Args:
        permission_sets: List of permission set names to include
        theme: Theme name to use
        
    Returns:
        Complete ClaudeSettings object
        
    Raises:
        ValueError: If settings cannot be validated
    """
    # Load default settings
    defaults = await load_default_settings()
    
    # Selected permission sets or default list
    if permission_sets is None:
        permission_sets = [
            'python',
            'node',
            'git',
            'shell',
            'package-managers'
        ]
    
    # Build the permission set
    all_permissions = await load_all_permissions()
    selected_permissions = [
        perm for perm in all_permissions
        if any(set_name.lower() in perm.lower() for set_name in permission_sets)
    ]
    
    # Load the selected theme or default
    theme_name = theme or 'default'
    theme_data = await load_theme(theme_name)
    
    # Create permissions object
    permissions = PermissionsSettings(
        allow=selected_permissions,
        deny=[]
    )
    
    # Combine everything into a single settings object
    settings_data = {
        **defaults,
        "theme": theme_data.get("theme", "default") if theme_data else "default",
        "permissions": permissions.model_dump(),
    }
    
    # Validate and return the final settings object
    try:
        return ClaudeSettings(**settings_data)
    except Exception as error:
        log_error(f"Invalid settings: {error}")
        raise ValueError("Failed to generate valid settings") from error


def get_settings_sync(
    permission_sets: Optional[list[str]] = None,
    theme: Optional[str] = None
) -> ClaudeSettings:
    """Synchronous version of get_settings.
    
    Args:
        permission_sets: List of permission set names to include
        theme: Theme name to use
        
    Returns:
        Complete ClaudeSettings object
        
    Raises:
        ValueError: If settings cannot be validated
    """
    # Load default settings
    defaults = load_default_settings_sync()
    
    # Selected permission sets or default list
    if permission_sets is None:
        permission_sets = [
            'python',
            'node',
            'git',
            'shell',
            'package-managers'
        ]
    
    # Build the permission set
    all_permissions = load_all_permissions_sync()
    selected_permissions = [
        perm for perm in all_permissions
        if any(set_name.lower() in perm.lower() for set_name in permission_sets)
    ]
    
    # Load the selected theme or default
    theme_name = theme or 'default'
    theme_data = load_theme_sync(theme_name)
    
    # Create permissions object
    permissions = PermissionsSettings(
        allow=selected_permissions,
        deny=[]
    )
    
    # Combine everything into a single settings object
    settings_data = {
        **defaults,
        "theme": theme_data.get("theme", "default") if theme_data else "default",
        "permissions": permissions.model_dump(),
    }
    
    # Validate and return the final settings object
    try:
        return ClaudeSettings(**settings_data)
    except Exception as error:
        log_error(f"Invalid settings: {error}")
        raise ValueError("Failed to generate valid settings") from error


async def read_settings(settings_path: Optional[Path] = None) -> Optional[ClaudeSettings]:
    """Read existing settings file.
    
    Args:
        settings_path: Path to settings file, defaults to CLAUDE_SETTINGS_FILE
        
    Returns:
        ClaudeSettings object if file exists and valid, None otherwise
    """
    if settings_path is None:
        settings_path = CLAUDE_SETTINGS_FILE
    
    try:
        if settings_path.exists():
            content = settings_path.read_text(encoding='utf-8')
            data = json.loads(content)
            return ClaudeSettings(**data)
        
        return None
        
    except Exception as error:
        log_error(f"Error reading settings from {settings_path}: {error}")
        return None


def read_settings_sync(settings_path: Optional[Path] = None) -> Optional[ClaudeSettings]:
    """Synchronous version of read_settings.
    
    Args:
        settings_path: Path to settings file, defaults to CLAUDE_SETTINGS_FILE
        
    Returns:
        ClaudeSettings object if file exists and valid, None otherwise
    """
    if settings_path is None:
        settings_path = CLAUDE_SETTINGS_FILE
    
    try:
        if settings_path.exists():
            content = settings_path.read_text(encoding='utf-8')
            data = json.loads(content)
            return ClaudeSettings(**data)
        
        return None
        
    except Exception as error:
        log_error(f"Error reading settings from {settings_path}: {error}")
        return None


async def merge_settings(
    existing_settings: ClaudeSettings,
    new_settings: ClaudeSettings
) -> ClaudeSettings:
    """Merge new settings with existing settings.
    
    Args:
        existing_settings: Current settings
        new_settings: New settings to merge
        
    Returns:
        Merged ClaudeSettings object with deduplicated arrays
    """
    # Convert to dictionaries for easier merging
    existing_dict = existing_settings.model_dump()
    new_dict = new_settings.model_dump()
    
    # Merge top-level properties
    merged = {
        **existing_dict,
        **new_dict,
    }
    
    # Merge environment variables
    if 'env' in existing_dict or 'env' in new_dict:
        merged['env'] = {
            **(existing_dict.get('env') or {}),
            **(new_dict.get('env') or {})
        }
    
    # Merge permissions
    existing_perms = existing_dict.get('permissions', {})
    new_perms = new_dict.get('permissions', {})
    
    merged['permissions'] = {
        'allow': list(set([
            *(existing_perms.get('allow') or []),
            *(new_perms.get('allow') or [])
        ])),
        'deny': list(set([
            *(existing_perms.get('deny') or []),
            *(new_perms.get('deny') or [])
        ]))
    }
    
    # Merge ignore patterns
    merged['ignorePatterns'] = list(set([
        *(existing_dict.get('ignorePatterns') or []),
        *(new_dict.get('ignorePatterns') or [])
    ]))
    
    # Merge hooks if present
    existing_hooks = existing_dict.get('hooks')
    new_hooks = new_dict.get('hooks')
    
    if existing_hooks or new_hooks:
        merged['hooks'] = {
            **(existing_hooks or {}),
            **(new_hooks or {})
        }
    
    return ClaudeSettings(**merged)


def merge_settings_sync(
    existing_settings: ClaudeSettings,
    new_settings: ClaudeSettings
) -> ClaudeSettings:
    """Synchronous version of merge_settings.
    
    Args:
        existing_settings: Current settings
        new_settings: New settings to merge
        
    Returns:
        Merged ClaudeSettings object with deduplicated arrays
    """
    # Convert to dictionaries for easier merging
    existing_dict = existing_settings.model_dump()
    new_dict = new_settings.model_dump()
    
    # Merge top-level properties
    merged = {
        **existing_dict,
        **new_dict,
    }
    
    # Merge environment variables
    if 'env' in existing_dict or 'env' in new_dict:
        merged['env'] = {
            **(existing_dict.get('env') or {}),
            **(new_dict.get('env') or {})
        }
    
    # Merge permissions
    existing_perms = existing_dict.get('permissions', {})
    new_perms = new_dict.get('permissions', {})
    
    merged['permissions'] = {
        'allow': list(set([
            *(existing_perms.get('allow') or []),
            *(new_perms.get('allow') or [])
        ])),
        'deny': list(set([
            *(existing_perms.get('deny') or []),
            *(new_perms.get('deny') or [])
        ]))
    }
    
    # Merge ignore patterns
    merged['ignorePatterns'] = list(set([
        *(existing_dict.get('ignorePatterns') or []),
        *(new_dict.get('ignorePatterns') or [])
    ]))
    
    # Merge hooks if present
    existing_hooks = existing_dict.get('hooks')
    new_hooks = new_dict.get('hooks')
    
    if existing_hooks or new_hooks:
        merged['hooks'] = {
            **(existing_hooks or {}),
            **(new_hooks or {})
        }
    
    return ClaudeSettings(**merged)


async def save_settings(
    settings: ClaudeSettings,
    settings_path: Optional[Path] = None
) -> None:
    """Save settings to file.
    
    Args:
        settings: ClaudeSettings object to save
        settings_path: Path to save to, defaults to CLAUDE_SETTINGS_FILE
        
    Raises:
        OSError: If file cannot be written
    """
    if settings_path is None:
        settings_path = CLAUDE_SETTINGS_FILE
    
    try:
        # Create directory if it doesn't exist
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dictionary and save as JSON
        settings_dict = settings.model_dump()
        content = json.dumps(settings_dict, indent=2, ensure_ascii=False)
        settings_path.write_text(content, encoding='utf-8')
        
    except Exception as error:
        log_error(f"Error saving settings to {settings_path}: {error}")
        raise OSError(f"Failed to save settings: {error}") from error


def save_settings_sync(
    settings: ClaudeSettings,
    settings_path: Optional[Path] = None
) -> None:
    """Synchronous version of save_settings.
    
    Args:
        settings: ClaudeSettings object to save
        settings_path: Path to save to, defaults to CLAUDE_SETTINGS_FILE
        
    Raises:
        OSError: If file cannot be written
    """
    if settings_path is None:
        settings_path = CLAUDE_SETTINGS_FILE
    
    try:
        # Create directory if it doesn't exist
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dictionary and save as JSON
        settings_dict = settings.model_dump()
        content = json.dumps(settings_dict, indent=2, ensure_ascii=False)
        settings_path.write_text(content, encoding='utf-8')
        
    except Exception as error:
        log_error(f"Error saving settings to {settings_path}: {error}")
        raise OSError(f"Failed to save settings: {error}") from error


async def get_available_themes() -> list[str]:
    """Get list of available theme names.
    
    Returns:
        List of available theme names
    """
    try:
        themes_package = files("claude_code_setup") / "settings" / "themes"
        
        if not themes_package.is_dir():
            return []
        
        theme_names = [
            theme_file.name.replace('.json', '')
            for theme_file in themes_package.iterdir()
            if theme_file.name.endswith('.json')
        ]
        
        return sorted(theme_names)
        
    except Exception as error:
        log_error(f"Error loading available themes: {error}")
        return []


def get_available_themes_sync() -> list[str]:
    """Synchronous version of get_available_themes.
    
    Returns:
        List of available theme names
    """
    try:
        themes_package = files("claude_code_setup") / "settings" / "themes"
        
        if not themes_package.is_dir():
            return []
        
        theme_names = [
            theme_file.name.replace('.json', '')
            for theme_file in themes_package.iterdir()
            if theme_file.name.endswith('.json')
        ]
        
        return sorted(theme_names)
        
    except Exception as error:
        log_error(f"Error loading available themes: {error}")
        return []


async def get_available_permission_sets() -> list[str]:
    """Get list of available permission set names.
    
    Returns:
        List of available permission set names
    """
    try:
        permissions_package = files("claude_code_setup") / "settings" / "permissions"
        
        if not permissions_package.is_dir():
            return []
        
        permission_set_names = [
            perm_file.name.replace('.json', '')
            for perm_file in permissions_package.iterdir()
            if perm_file.name.endswith('.json')
        ]
        
        return sorted(permission_set_names)
        
    except Exception as error:
        log_error(f"Error loading available permission sets: {error}")
        return []


def get_available_permission_sets_sync() -> list[str]:
    """Synchronous version of get_available_permission_sets.
    
    Returns:
        List of available permission set names  
    """
    try:
        permissions_package = files("claude_code_setup") / "settings" / "permissions"
        
        if not permissions_package.is_dir():
            return []
        
        permission_set_names = [
            perm_file.name.replace('.json', '')
            for perm_file in permissions_package.iterdir()
            if perm_file.name.endswith('.json')
        ]
        
        return sorted(permission_set_names)
        
    except Exception as error:
        log_error(f"Error loading available permission sets: {error}")
        return []

# Hook integration functions

def register_hook_in_settings(
    hook: Hook,
    settings_path: Optional[Path] = None
) -> bool:
    """Register a hook in the settings file.
    
    Args:
        hook: Hook to register
        settings_path: Path to settings file, defaults to CLAUDE_SETTINGS_FILE
        
    Returns:
        True if hook was registered successfully, False otherwise
    """
    try:
        # Read existing settings or create default
        existing_settings = read_settings_sync(settings_path)
        if existing_settings is None:
            existing_settings = get_settings_sync()
        
        # Create hook configuration
        hook_config = HookConfig(
            type="command",
            command=hook.config.command
        )
        
        hook_settings = HookSettings(
            matcher=hook.matcher or "",
            hooks=[hook_config]
        )
        
        # Get existing hooks structure or create new one
        current_hooks = existing_settings.hooks or SettingsHooks()
        current_hooks_dict = current_hooks.model_dump() if current_hooks else {}
        
        # Add hook to the appropriate event
        event_key = hook.event.value
        event_hooks = current_hooks_dict.get(event_key, [])
        
        # Check if hook already exists (by matcher and command)
        hook_exists = any(
            hook_entry.get('matcher') == hook.matcher and
            any(h.get('command') == hook.config.command for h in hook_entry.get('hooks', []))
            for hook_entry in event_hooks
        )
        
        if not hook_exists:
            event_hooks.append(hook_settings.model_dump())
            current_hooks_dict[event_key] = event_hooks
        
        # Update settings
        existing_settings.hooks = SettingsHooks(**current_hooks_dict)
        
        # Save settings
        save_settings_sync(existing_settings, settings_path)
        
        return True
        
    except Exception as error:
        log_error(f"Error registering hook '{hook.name}' in settings: {error}")
        return False


def unregister_hook_from_settings(
    hook: Hook,
    settings_path: Optional[Path] = None
) -> bool:
    """Unregister a hook from the settings file.
    
    Args:
        hook: Hook to unregister
        settings_path: Path to settings file, defaults to CLAUDE_SETTINGS_FILE
        
    Returns:
        True if hook was unregistered successfully, False otherwise
    """
    try:
        # Read existing settings
        existing_settings = read_settings_sync(settings_path)
        if existing_settings is None or existing_settings.hooks is None:
            return True  # Nothing to remove
        
        current_hooks_dict = existing_settings.hooks.model_dump()
        event_key = hook.event.value
        
        if event_key not in current_hooks_dict:
            return True  # Event not present
        
        event_hooks = current_hooks_dict[event_key]
        
        # Remove hooks matching the command
        updated_event_hooks = []
        for hook_entry in event_hooks:
            # Filter out hooks with matching command
            filtered_hooks = [
                h for h in hook_entry.get('hooks', [])
                if h.get('command') != hook.config.command
            ]
            
            # Keep the entry if it still has hooks
            if filtered_hooks:
                hook_entry_copy = hook_entry.copy()
                hook_entry_copy['hooks'] = filtered_hooks
                updated_event_hooks.append(hook_entry_copy)
        
        # Update the event hooks
        if updated_event_hooks:
            current_hooks_dict[event_key] = updated_event_hooks
        else:
            # Remove the event entirely if no hooks left
            del current_hooks_dict[event_key]
        
        # Update settings
        if current_hooks_dict:
            existing_settings.hooks = SettingsHooks(**current_hooks_dict)
        else:
            existing_settings.hooks = None
        
        # Save settings
        save_settings_sync(existing_settings, settings_path)
        
        return True
        
    except Exception as error:
        log_error(f"Error unregistering hook '{hook.name}' from settings: {error}")
        return False


def get_registered_hooks(
    settings_path: Optional[Path] = None
) -> dict[str, list[dict]]:
    """Get all registered hooks from settings.
    
    Args:
        settings_path: Path to settings file, defaults to CLAUDE_SETTINGS_FILE
        
    Returns:
        Dictionary mapping event types to list of hook configurations
    """
    try:
        settings = read_settings_sync(settings_path)
        if settings is None or settings.hooks is None:
            return {}
        
        return settings.hooks.model_dump()
        
    except Exception as error:
        log_error(f"Error reading registered hooks from settings: {error}")
        return {}


def validate_hook_settings(
    hook: Hook
) -> tuple[bool, list[str]]:
    """Validate a hook configuration for settings integration.
    
    Args:
        hook: Hook to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required fields
    if not hook.name:
        errors.append("Hook name is required")
    
    if not hook.event:
        errors.append("Hook event is required")
    
    if not hook.config or not hook.config.command:
        errors.append("Hook command is required")
    
    # Validate event type
    try:
        HookEvent(hook.event)
    except ValueError:
        errors.append(f"Invalid hook event: {hook.event}")
    
    # Validate command format
    if hook.config and hook.config.command:
        command = hook.config.command
        if not command.strip():
            errors.append("Hook command cannot be empty")
        
        # Check for basic command structure
        if not any(cmd in command.lower() for cmd in ['python', 'bash', 'sh', 'node']):
            errors.append("Hook command should specify interpreter (python, bash, sh, node)")
    
    # Validate matcher if present
    if hook.matcher and not hook.matcher.strip():
        errors.append("Hook matcher cannot be empty if specified")
    
    return len(errors) == 0, errors


def create_hook_settings_structure(
    hooks_data: dict[str, list[Hook]]
) -> SettingsHooks:
    """Create a SettingsHooks structure from a dictionary of hooks grouped by event.
    
    Args:
        hooks_data: Dictionary mapping event names to lists of hooks
        
    Returns:
        SettingsHooks object
    """
    settings_dict = {}
    
    for event_name, hooks in hooks_data.items():
        event_settings = []
        
        # Group hooks by matcher
        matcher_groups = {}
        for hook in hooks:
            matcher = hook.matcher or ""
            if matcher not in matcher_groups:
                matcher_groups[matcher] = []
            matcher_groups[matcher].append(hook)
        
        # Create HookSettings for each matcher group
        for matcher, grouped_hooks in matcher_groups.items():
            hook_configs = [
                HookConfig(type="command", command=hook.config.command)
                for hook in grouped_hooks
                if hook.config and hook.config.command
            ]
            
            if hook_configs:
                hook_setting = HookSettings(
                    matcher=matcher,
                    hooks=hook_configs
                )
                event_settings.append(hook_setting)
        
        if event_settings:
            settings_dict[event_name] = event_settings
    
    return SettingsHooks(**settings_dict)