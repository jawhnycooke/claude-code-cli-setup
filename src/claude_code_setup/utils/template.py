"""Template utilities for claude-code-setup.

This module provides template loading, parsing, and validation functionality,
converted from TypeScript template.ts. Uses importlib.resources to access
bundled templates in the Python package.
"""

import re
import time
from pathlib import Path
from typing import Optional, List, Tuple, Dict
from functools import lru_cache
from threading import Lock

try:
    # Python 3.9+
    from importlib.resources import files
except ImportError:
    # Python 3.8 fallback - this is optional for our use case
    try:
        from importlib_resources import files  # type: ignore
    except ImportError:
        # If neither is available, we'll handle it in the functions
        files = None  # type: ignore

from ..types import Template, TemplateCategory, TemplateRegistry

# Template registry cache with timestamp
_template_registry: Optional[TemplateRegistry] = None
_cache_timestamp: float = 0
_cache_ttl: int = 300  # 5 minutes cache TTL
_cache_lock = Lock()


class TemplateLoadError(Exception):
    """Custom exception for template loading errors."""
    pass


@lru_cache(maxsize=128)
def _category_string_to_enum(category_str: str) -> TemplateCategory:
    """Convert category string to TemplateCategory enum with caching.
    
    Args:
        category_str: Category string from directory name
        
    Returns:
        TemplateCategory enum value
        
    Raises:
        ValueError: If category string is not recognized
    """
    category_map = {
        "python": TemplateCategory.PYTHON,
        "node": TemplateCategory.NODE,
        "project": TemplateCategory.PROJECT,
        "general": TemplateCategory.GENERAL,
    }
    
    normalized_category = category_str.lower().strip()
    
    if normalized_category not in category_map:
        valid_categories = ", ".join(sorted(category_map.keys()))
        raise ValueError(
            f"Unknown template category: '{category_str}'. "
            f"Valid categories are: {valid_categories}"
        )
    
    return category_map[normalized_category]


def get_templates_directory() -> Path:
    """Get the templates directory path from the package resources.
    
    Returns:
        Path to the templates directory within the package
        
    Raises:
        ImportError: If importlib.resources is not available
    """
    if files is None:
        raise ImportError(
            "importlib.resources is not available. "
            "Please install importlib-resources for Python < 3.9"
        )
    
    # Get templates directory from package resources
    package_templates = files("claude_code_setup") / "templates"
    return Path(str(package_templates))


async def load_templates_from_files() -> TemplateRegistry:
    """Load templates from files in the templates directory.
    
    Returns:
        Dictionary mapping template names to Template objects
        
    Raises:
        FileNotFoundError: If templates directory is not found
        OSError: If there are issues reading template files
    """
    templates: dict[str, Template] = {}
    
    try:
        # Get templates from package resources
        templates_package = files("claude_code_setup") / "templates"
        
        if not templates_package.is_dir():
            raise FileNotFoundError(f"Templates directory not found in package")
        
        # Get all category directories
        for category_resource in templates_package.iterdir():
            if not category_resource.is_dir():
                continue
            
            category = category_resource.name
            
            # Get all template files in this category
            for template_file in category_resource.iterdir():
                if not template_file.name.endswith('.md'):
                    continue
                
                # Read template content
                content = template_file.read_text(encoding='utf-8')
                name = template_file.name.replace('.md', '')
                
                # Create template key based on category and name
                if name == 'optimization':
                    # Handle special case for optimization templates
                    template_key = f"{category}-{name}"
                else:
                    template_key = name
                
                # Extract title from markdown content as description
                title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                description = title_match.group(1) if title_match else f"{category} {name}"
                
                # Create template object
                templates[template_key] = Template(
                    name=template_key,
                    description=description,
                    category=_category_string_to_enum(category),
                    content=content
                )
        
        return TemplateRegistry(templates=templates)
    
    except Exception as error:
        # Use our logger for error reporting
        from .logger import error as log_error
        log_error(f"Error loading templates: {error}")
        raise


def load_templates_from_files_sync() -> TemplateRegistry:
    """Synchronous version of load_templates_from_files with enhanced error handling.
    
    Returns:
        TemplateRegistry containing all loaded templates
        
    Raises:
        TemplateLoadError: If critical error occurs during loading
    """
    templates: dict[str, Template] = {}
    errors: List[str] = []
    
    try:
        if files is None:
            raise ImportError(
                "importlib.resources is not available. "
                "Please install importlib-resources for Python < 3.9"
            )
        
        # Get templates from package resources
        templates_package = files("claude_code_setup") / "templates"
        
        if not templates_package.is_dir():
            raise TemplateLoadError(
                "Templates directory not found in package. "
                "This may indicate a packaging issue."
            )
        
        # Get all category directories
        category_count = 0
        for category_resource in templates_package.iterdir():
            if not category_resource.is_dir():
                continue
            
            category_count += 1
            category = category_resource.name
            
            # Get all template files in this category
            template_count = 0
            for template_file in category_resource.iterdir():
                if not template_file.name.endswith('.md'):
                    continue
                
                try:
                    # Read template content with error handling
                    content = template_file.read_text(encoding='utf-8')
                    
                    # Validate content is not empty
                    if not content.strip():
                        errors.append(f"Template {template_file.name} is empty, skipping")
                        continue
                    
                    name = template_file.name.replace('.md', '')
                    
                    # Create template key based on category and name
                    if name == 'optimization':
                        # Handle special case for optimization templates
                        template_key = f"{category}-{name}"
                    else:
                        template_key = name
                    
                    # Extract title from markdown content as description
                    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                    description = title_match.group(1) if title_match else f"{category} {name}"
                    
                    # Create template object with validation
                    try:
                        category_enum = _category_string_to_enum(category)
                    except ValueError as e:
                        errors.append(f"Invalid category for template {name}: {e}")
                        continue
                    
                    templates[template_key] = Template(
                        name=template_key,
                        description=description,
                        category=category_enum,
                        content=content
                    )
                    template_count += 1
                    
                except Exception as e:
                    errors.append(f"Error loading template {template_file.name}: {e}")
            
            # Log category loading info
            from .logger import debug
            debug(f"Loaded {template_count} templates from category {category}")
        
        if category_count == 0:
            raise TemplateLoadError(
                "No category directories found in templates. "
                "Expected directories: python, node, project, general"
            )
        
        if not templates and errors:
            raise TemplateLoadError(
                f"Failed to load any templates. Errors: {'; '.join(errors)}"
            )
        
        # Log any non-critical errors
        if errors:
            from .logger import warning
            for error in errors:
                warning(f"Template loading warning: {error}")
        
        from .logger import debug
        debug(f"Successfully loaded {len(templates)} templates")
        return TemplateRegistry(templates=templates)
    
    except ImportError as e:
        from .logger import error as log_error
        log_error(f"Import error loading templates: {e}")
        raise TemplateLoadError(f"Missing required dependency: {e}")
    except Exception as e:
        from .logger import error as log_error
        log_error(f"Unexpected error loading templates: {e}")
        raise TemplateLoadError(f"Failed to load templates: {e}")


def _is_cache_valid() -> bool:
    """Check if the template cache is still valid."""
    if _template_registry is None:
        return False
    
    cache_age = time.time() - _cache_timestamp
    return cache_age < _cache_ttl


async def get_all_templates(force_reload: bool = False) -> TemplateRegistry:
    """Get all available templates with caching.
    
    Args:
        force_reload: Force reload templates even if cached
        
    Returns:
        TemplateRegistry containing all templates
    """
    global _template_registry, _cache_timestamp
    
    with _cache_lock:
        if not force_reload and _is_cache_valid():
            from .logger import debug
            debug("Using cached template registry")
            return _template_registry
        
        from .logger import debug
        debug("Loading template registry from files")
        _template_registry = await load_templates_from_files()
        _cache_timestamp = time.time()
        
        return _template_registry


def get_all_templates_sync(force_reload: bool = False) -> TemplateRegistry:
    """Synchronous version of get_all_templates with caching.
    
    Args:
        force_reload: Force reload templates even if cached
        
    Returns:
        TemplateRegistry containing all templates
    """
    global _template_registry, _cache_timestamp
    
    with _cache_lock:
        if not force_reload and _is_cache_valid():
            from .logger import debug
            debug("Using cached template registry")
            return _template_registry
        
        from .logger import debug
        debug("Loading template registry from files")
        _template_registry = load_templates_from_files_sync()
        _cache_timestamp = time.time()
        
        return _template_registry


async def get_template(template_name: str) -> Optional[Template]:
    """Get a specific template by name with error handling.
    
    Args:
        template_name: Name of the template to retrieve
        
    Returns:
        Template object if found, None otherwise
    """
    try:
        templates = await get_all_templates()
        return templates.templates.get(template_name)
    except TemplateLoadError as e:
        from .logger import error as log_error
        log_error(f"Failed to load templates: {e}")
        return None
    except Exception as e:
        from .logger import error as log_error
        log_error(f"Unexpected error getting template '{template_name}': {e}")
        return None


def get_template_sync(template_name: str) -> Optional[Template]:
    """Synchronous version of get_template with error handling.
    
    Args:
        template_name: Name of the template to retrieve
        
    Returns:
        Template object if found, None otherwise
    """
    try:
        templates = get_all_templates_sync()
        return templates.templates.get(template_name)
    except TemplateLoadError as e:
        from .logger import error as log_error
        log_error(f"Failed to load templates: {e}")
        return None
    except Exception as e:
        from .logger import error as log_error
        log_error(f"Unexpected error getting template '{template_name}': {e}")
        return None


async def get_templates_by_category(category: str) -> List[Template]:
    """Get templates by category with validation.
    
    Args:
        category: Category name or enum value
        
    Returns:
        List of templates in the category
    """
    try:
        # Handle both string and enum input
        if isinstance(category, str):
            try:
                category_enum = _category_string_to_enum(category)
            except ValueError:
                from .logger import warning
                warning(f"Invalid category '{category}', returning empty list")
                return []
        else:
            category_enum = category
        
        templates = await get_all_templates()
        return [
            template for template in templates.templates.values()
            if template.category == category_enum
        ]
    except TemplateLoadError as e:
        from .logger import error as log_error
        log_error(f"Failed to load templates: {e}")
        return []
    except Exception as e:
        from .logger import error as log_error
        log_error(f"Unexpected error getting templates by category: {e}")
        return []


def get_templates_by_category_sync(category: str) -> List[Template]:
    """Synchronous version of get_templates_by_category with validation.
    
    Args:
        category: Category name or enum value
        
    Returns:
        List of templates in the category
    """
    try:
        # Handle both string and enum input
        if isinstance(category, str):
            try:
                category_enum = _category_string_to_enum(category)
            except ValueError:
                from .logger import warning
                warning(f"Invalid category '{category}', returning empty list")
                return []
        else:
            category_enum = category
        
        templates = get_all_templates_sync()
        return [
            template for template in templates.templates.values()
            if template.category == category_enum
        ]
    except TemplateLoadError as e:
        from .logger import error as log_error
        log_error(f"Failed to load templates: {e}")
        return []
    except Exception as e:
        from .logger import error as log_error
        log_error(f"Unexpected error getting templates by category: {e}")
        return []


async def get_template_categories() -> List[str]:
    """Get all available template categories.
    
    Returns:
        Sorted list of category names
    """
    try:
        templates = await get_all_templates()
        categories = set(
            template.category.value for template in templates.templates.values()
        )
        return sorted(categories)
    except TemplateLoadError as e:
        from .logger import error as log_error
        log_error(f"Failed to load templates: {e}")
        return []
    except Exception as e:
        from .logger import error as log_error
        log_error(f"Unexpected error getting categories: {e}")
        return []


def get_template_categories_sync() -> List[str]:
    """Synchronous version of get_template_categories.
    
    Returns:
        Sorted list of category names
    """
    try:
        templates = get_all_templates_sync()
        categories = set(
            template.category.value for template in templates.templates.values()
        )
        return sorted(categories)
    except TemplateLoadError as e:
        from .logger import error as log_error
        log_error(f"Failed to load templates: {e}")
        return []
    except Exception as e:
        from .logger import error as log_error
        log_error(f"Unexpected error getting categories: {e}")
        return []


async def validate_template_content(content: str) -> Tuple[bool, List[str]]:
    """Validate template content with comprehensive checks.
    
    Args:
        content: Template content to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    return validate_template_content_sync(content)


def validate_template_content_sync(content: str) -> Tuple[bool, List[str]]:
    """Validate template content with comprehensive checks.
    
    Args:
        content: Template content to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors: List[str] = []
    
    # Check for required markdown structure
    if not content:
        errors.append("Template content is empty")
        return False, errors
    
    content_stripped = content.strip()
    if not content_stripped:
        errors.append("Template content contains only whitespace")
        return False, errors
    
    # Check for title (# heading)
    if not re.search(r'^#\s+.+$', content, re.MULTILINE):
        errors.append("Template must have a title (# heading)")
    
    # Check for minimum content length
    if len(content_stripped) < 10:
        errors.append("Template content is too short (minimum 10 characters)")
    
    # Check for maximum content length (prevent abuse)
    if len(content) > 1_000_000:  # 1MB limit
        errors.append("Template content is too large (maximum 1MB)")
    
    # Validate markdown structure
    lines = content.split('\n')
    has_content = False
    code_block_count = 0
    in_code_block = False
    
    for line in lines:
        # Track code blocks
        if line.strip().startswith('```'):
            if in_code_block:
                in_code_block = False
            else:
                in_code_block = True
                code_block_count += 1
        
        # Check for actual content
        if line.strip() and not line.strip().startswith('#') and not in_code_block:
            has_content = True
    
    if in_code_block:
        errors.append("Template has unclosed code block")
    
    if not has_content:
        errors.append("Template must have content beyond just headings")
    
    # Check for suspicious patterns
    suspicious_patterns = [
        (r'<script', "Template contains script tags"),
        (r'javascript:', "Template contains javascript: protocol"),
        (r'data:text/html', "Template contains data: HTML protocol"),
    ]
    
    for pattern, message in suspicious_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            errors.append(message)
    
    return len(errors) == 0, errors


def clear_template_cache() -> None:
    """Clear the template registry cache.
    
    Useful for testing or when templates are updated.
    """
    global _template_registry, _cache_timestamp
    with _cache_lock:
        _template_registry = None
        _cache_timestamp = 0
        _category_string_to_enum.cache_clear()
        from .logger import debug
        debug("Template cache cleared")


def set_cache_ttl(seconds: int) -> None:
    """Set the cache TTL in seconds.
    
    Args:
        seconds: Cache TTL in seconds (0 to disable caching)
    """
    global _cache_ttl
    _cache_ttl = max(0, seconds)
    from .logger import debug
    debug(f"Template cache TTL set to {_cache_ttl} seconds")


def get_cache_info() -> Dict[str, any]:
    """Get information about the template cache.
    
    Returns:
        Dictionary with cache information
    """
    with _cache_lock:
        if _template_registry is None:
            return {
                'cached': False,
                'ttl': _cache_ttl
            }
        
        age = time.time() - _cache_timestamp
        return {
            'cached': True,
            'age': age,
            'valid': age < _cache_ttl,
            'ttl': _cache_ttl,
            'template_count': len(_template_registry.templates)
        }