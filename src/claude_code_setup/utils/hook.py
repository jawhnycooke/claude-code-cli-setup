"""Hook loading and management utilities for claude-code-setup.

This module provides functionality to load, parse, and manage hooks from
the package resources, similar to the template system but for security and
automation hooks.
"""

import json
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

import importlib.resources
from pydantic import ValidationError

from ..types import Hook, HookMetadata, HookRegistry, HookEvent, HookConfig
from ..exceptions import HookLoadError, HookNotFoundError
from .logger import info, warning, error, debug

# Global hook registry cache
_hook_registry: Optional[HookRegistry] = None
_cache_timestamp: float = 0.0
_cache_ttl: float = 300.0  # 5 minutes default TTL
_cache_lock = threading.RLock()

# Hook categories mapping
HOOK_CATEGORIES = {
    "security": "Security hooks for command validation and protection",
    "testing": "Testing automation hooks",
    "aws": "AWS-specific deployment and validation hooks",
}




def _load_hook_metadata(metadata_path: Path) -> HookMetadata:
    """Load and validate hook metadata from a metadata.json file.
    
    Args:
        metadata_path: Path to the metadata.json file
        
    Returns:
        Validated HookMetadata object
        
    Raises:
        HookLoadError: If metadata is invalid or cannot be loaded
    """
    try:
        with metadata_path.open('r', encoding='utf-8') as f:
            metadata_dict = json.load(f)
        
        # Validate the metadata using Pydantic
        metadata = HookMetadata(**metadata_dict)
        return metadata
        
    except json.JSONDecodeError as e:
        raise HookLoadError(f"Invalid JSON in {metadata_path}: {e}")
    except ValidationError as e:
        raise HookLoadError(f"Invalid metadata format in {metadata_path}: {e}")
    except Exception as e:
        raise HookLoadError(f"Failed to load metadata from {metadata_path}: {e}")


def _load_hook_scripts(hook_dir: Path, hook_name: str) -> Dict[str, str]:
    """Load all script files for a hook.
    
    Args:
        hook_dir: Directory containing the hook files
        hook_name: Name of the hook
        
    Returns:
        Dictionary mapping script filenames to their content
    """
    scripts = {}
    
    # Common script extensions
    script_extensions = {'.py', '.sh', '.bash'}
    
    for file_path in hook_dir.iterdir():
        if file_path.is_file() and file_path.suffix in script_extensions:
            try:
                with file_path.open('r', encoding='utf-8') as f:
                    scripts[file_path.name] = f.read()
            except Exception as e:
                warning(f"Failed to load script {file_path.name} for hook {hook_name}: {e}")
                
    return scripts


def _discover_hooks_from_package() -> Dict[str, Hook]:
    """Discover and load all hooks from package resources.
    
    Returns:
        Dictionary mapping hook names to Hook objects
        
    Raises:
        HookLoadError: If hook discovery fails
    """
    hooks = {}
    
    try:
        # Use importlib.resources to access packaged hooks
        hooks_package = importlib.resources.files("claude_code_setup") / "hooks"
        
        if not hooks_package.is_dir():
            debug("No hooks directory found in package resources")
            return hooks
            
        # Iterate through category directories
        for category_dir in hooks_package.iterdir():
            if not category_dir.is_dir():
                continue
                
            category_name = category_dir.name
            debug(f"Scanning category: {category_name}")
            
            # Iterate through hooks in this category
            for hook_dir in category_dir.iterdir():
                if not hook_dir.is_dir():
                    continue
                    
                hook_name = hook_dir.name
                metadata_file = hook_dir / "metadata.json"
                
                if not metadata_file.is_file():
                    warning(f"Hook {hook_name} missing metadata.json, skipping")
                    continue
                    
                try:
                    # Load metadata
                    with metadata_file.open('r', encoding='utf-8') as f:
                        metadata_dict = json.load(f)
                    
                    # Load hook configuration
                    config_dict = metadata_dict.get('config', {})
                    config = HookConfig(**config_dict)
                    
                    # Create HookMetadata (excluding config)
                    metadata_only = {k: v for k, v in metadata_dict.items() if k != 'config'}
                    metadata = HookMetadata(**metadata_only)
                    
                    # Load scripts
                    scripts = {}
                    for file_path in hook_dir.iterdir():
                        if file_path.is_file() and file_path.suffix in {'.py', '.sh', '.bash'}:
                            with file_path.open('r', encoding='utf-8') as f:
                                scripts[file_path.name] = f.read()
                    
                    # Create complete Hook object
                    hook = Hook(
                        **metadata.model_dump(),
                        config=config,
                        scripts=scripts
                    )
                    
                    hooks[hook_name] = hook
                    debug(f"Loaded hook: {hook_name} (category: {category_name})")
                    
                except Exception as e:
                    error(f"Failed to load hook {hook_name}: {e}")
                    continue
                    
    except Exception as e:
        raise HookLoadError(f"Failed to discover hooks from package: {e}")
        
    info(f"Discovered {len(hooks)} hooks across {len(HOOK_CATEGORIES)} categories")
    return hooks


def _is_cache_valid() -> bool:
    """Check if the current hook registry cache is still valid.
    
    Returns:
        True if cache is valid, False otherwise
    """
    global _hook_registry, _cache_timestamp, _cache_ttl
    
    if _hook_registry is None:
        return False
        
    cache_age = time.time() - _cache_timestamp
    return cache_age < _cache_ttl


def get_all_hooks(force_reload: bool = False) -> HookRegistry:
    """Get all available hooks with caching.
    
    Args:
        force_reload: Force reload hooks even if cached
        
    Returns:
        HookRegistry containing all hooks
        
    Raises:
        HookLoadError: If hook loading fails
    """
    global _hook_registry, _cache_timestamp
    
    with _cache_lock:
        if not force_reload and _is_cache_valid():
            return _hook_registry
            
        debug("Loading hooks from package resources")
        
        try:
            hooks = _discover_hooks_from_package()
            _hook_registry = HookRegistry(hooks=hooks)
            _cache_timestamp = time.time()
            
            info(f"Loaded {len(hooks)} hooks successfully")
            return _hook_registry
            
        except Exception as e:
            error(f"Failed to load hooks: {e}")
            raise HookLoadError(f"Hook loading failed: {e}")


def get_all_hooks_sync(force_reload: bool = False) -> HookRegistry:
    """Synchronous version of get_all_hooks with caching.
    
    Args:
        force_reload: Force reload hooks even if cached
        
    Returns:
        HookRegistry containing all hooks
    """
    return get_all_hooks(force_reload)


def get_hook(hook_name: str) -> Optional[Hook]:
    """Get a specific hook by name.
    
    Args:
        hook_name: Name of the hook to retrieve
        
    Returns:
        Hook object if found, None otherwise
    """
    try:
        registry = get_all_hooks_sync()
        return registry.hooks.get(hook_name)
    except HookLoadError:
        return None


def get_hook_sync(hook_name: str) -> Optional[Hook]:
    """Synchronous version of get_hook.
    
    Args:
        hook_name: Name of the hook to retrieve
        
    Returns:
        Hook object if found, None otherwise
    """
    return get_hook(hook_name)


def get_hooks_by_category(category: str) -> List[Hook]:
    """Get all hooks in a specific category.
    
    Args:
        category: Category name to filter by
        
    Returns:
        List of Hook objects in the category
    """
    try:
        registry = get_all_hooks_sync()
        return [
            hook for hook in registry.hooks.values()
            if hook.category.lower() == category.lower()
        ]
    except HookLoadError:
        return []


def get_hooks_by_event(event: Union[str, HookEvent]) -> List[Hook]:
    """Get all hooks that respond to a specific event.
    
    Args:
        event: Event type to filter by
        
    Returns:
        List of Hook objects that handle the event
    """
    try:
        registry = get_all_hooks_sync()
        event_str = event.value if isinstance(event, HookEvent) else event
        
        return [
            hook for hook in registry.hooks.values()
            if hook.event.value == event_str
        ]
    except HookLoadError:
        return []


def get_hook_categories() -> Dict[str, str]:
    """Get available hook categories with descriptions.
    
    Returns:
        Dictionary mapping category names to descriptions
    """
    # Get actual categories from loaded hooks
    try:
        registry = get_all_hooks_sync()
        actual_categories = set(hook.category for hook in registry.hooks.values())
        
        # Return both predefined and discovered categories
        categories = HOOK_CATEGORIES.copy()
        for category in actual_categories:
            if category not in categories:
                categories[category] = f"{category.title()} hooks"
                
        return categories
    except HookLoadError:
        return HOOK_CATEGORIES


def validate_hook_metadata(metadata_dict: dict) -> Tuple[bool, List[str]]:
    """Validate hook metadata dictionary.
    
    Args:
        metadata_dict: Metadata dictionary to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        # Try to create HookMetadata object
        HookMetadata(**metadata_dict)
        
        # Additional validation
        if 'config' in metadata_dict:
            HookConfig(**metadata_dict['config'])
            
        return True, []
        
    except ValidationError as e:
        for error_item in e.errors():
            field = " -> ".join(str(loc) for loc in error_item['loc'])
            message = error_item['msg']
            errors.append(f"{field}: {message}")
        
        return False, errors
    except Exception as e:
        errors.append(f"Validation error: {e}")
        return False, errors


def clear_hook_cache() -> None:
    """Clear the hook registry cache."""
    global _hook_registry, _cache_timestamp
    
    with _cache_lock:
        _hook_registry = None
        _cache_timestamp = 0.0
        debug("Hook cache cleared")


def set_cache_ttl(ttl_seconds: float) -> None:
    """Set the cache TTL for hook registry.
    
    Args:
        ttl_seconds: Time to live in seconds
    """
    global _cache_ttl
    _cache_ttl = ttl_seconds
    debug(f"Hook cache TTL set to {ttl_seconds} seconds")


def get_cache_info() -> Dict[str, any]:
    """Get information about the current hook cache state.
    
    Returns:
        Dictionary with cache information
    """
    global _hook_registry, _cache_timestamp, _cache_ttl
    
    return {
        "cached": _hook_registry is not None,
        "cache_timestamp": _cache_timestamp,
        "cache_ttl": _cache_ttl,
        "cache_age": time.time() - _cache_timestamp if _cache_timestamp > 0 else 0,
        "is_valid": _is_cache_valid(),
        "hook_count": len(_hook_registry.hooks) if _hook_registry else 0,
    }