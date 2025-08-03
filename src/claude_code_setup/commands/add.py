"""Add command implementation for claude-code-setup.

This module implements the add command which allows users to install
templates, hooks, and settings to their Claude Code configuration.
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum

from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt

# UI components
from ..ui.prompts import (
    MultiSelectPrompt,
    ConfirmationDialog,
)
from ..ui.progress import (
    MultiStepProgress,
    ProgressStep,
)
from ..ui.styles import (
    console,
    error_console,
    create_panel,
    create_table,
    create_command_error,
    create_success_banner,
    create_step_indicator,
    COLORS,
    BOX_STYLES,
)

# Utilities
from ..utils import (
    info,
    success,
    warning,
    error,
    get_all_templates_sync,
    get_template_categories_sync,
    CLAUDE_HOME,
)
from ..utils.plugin_template_loader import (
    get_all_templates_with_plugins,
)
from ..plugins.registry import PluginRegistry
from ..plugins.loader import PluginLoader
from ..utils.template_installer import (
    TemplateInstaller,
    install_templates_interactive,
)
from ..utils.hook_installer import (
    HookInstaller,
    create_hook_installer,
)
from ..utils.hook import get_all_hooks_sync


class ResourceType(Enum):
    """Types of resources that can be added."""
    TEMPLATE = "template"
    TEMPLATES = "templates"
    HOOK = "hook"
    HOOKS = "hooks"
    PERMISSION = "permission"
    SETTINGS = "settings"
    
    @classmethod
    def from_string(cls, value: str) -> Optional['ResourceType']:
        """Convert string to ResourceType."""
        value_lower = value.lower()
        for resource_type in cls:
            if resource_type.value == value_lower:
                return resource_type
        return None


def determine_target_directory(
    test_dir: Optional[str], 
    global_config: bool
) -> Path:
    """Determine the target directory based on options."""
    if test_dir:
        target_home = Path(test_dir) / ".claude"
        info(f"Using test directory: {target_home}")
    elif global_config:
        target_home = CLAUDE_HOME
        info(f"Using global directory: {target_home}")
    else:
        target_home = Path.cwd() / ".claude"
        info(f"Using local directory: {target_home}")
    
    return target_home


def show_resource_type_selection() -> ResourceType:
    """Show interactive resource type selection."""
    console.print(create_step_indicator(1, 3, "Choose Resource Type"))
    
    choices = [
        ("templates", "📄 Templates - Command templates for Claude Code"),
        ("hooks", "🛡️ Hooks - Security and automation scripts"),
        ("permission", "🔐 Permission - Add specific permissions to settings"),
        ("settings", "⚙️ Settings - Configure themes and options"),
    ]
    
    table = create_table(
        show_header=False,
        box=BOX_STYLES["minimal"],
        show_edge=False,
    )
    table.add_column("Choice", style=COLORS["primary"])
    table.add_column("Description")
    
    for i, (value, description) in enumerate(choices, 1):
        table.add_row(f"[bold]{i}[/bold]", description)
    
    console.print(table)
    console.print()
    
    while True:
        choice = Prompt.ask(
            "What would you like to add?",
            choices=[str(i) for i in range(1, len(choices) + 1)],
            default="1"
        )
        try:
            choice_idx = int(choice) - 1
            resource_type_str = choices[choice_idx][0]
            return ResourceType.from_string(resource_type_str)
        except (ValueError, IndexError):
            warning("Invalid choice. Please try again.")


def select_templates_to_install(
    target_dir: Path,
    category_filter: Optional[str] = None
) -> List[str]:
    """Show template selection interface."""
    console.print(create_step_indicator(2, 3, "Select Templates"))
    
    # Load available templates
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Loading templates...", total=None)
        
        try:
            # Check if we should use plugin-aware loading
            plugins_dir = target_dir / "plugins"
            if plugins_dir.exists():
                # Load with plugin support
                registry = PluginRegistry(plugins_dir)
                loader = PluginLoader(registry, plugins_dir)
                loader.discover_plugins()
                template_registry = get_all_templates_with_plugins(registry)
            else:
                # Fall back to core templates only
                template_registry = get_all_templates_sync()
            
            templates = template_registry.templates
            categories = get_template_categories_sync()
        except Exception as e:
            error(f"Failed to load templates: {e}")
            return []
    
    # Filter by category if specified
    if category_filter:
        filtered_templates = {
            name: tmpl for name, tmpl in templates.items()
            if tmpl.category.value == category_filter.lower()
        }
        if not filtered_templates:
            warning(f"No templates found in category: {category_filter}")
            return []
        templates = filtered_templates
    
    # Group templates by category
    templates_by_category: Dict[str, List[Tuple[str, Any]]] = {}
    for name, template in templates.items():
        category = template.category.value
        if category not in templates_by_category:
            templates_by_category[category] = []
        templates_by_category[category].append((name, template))
    
    # Create selection prompt
    choices = []
    choice_map = {}
    
    for category in sorted(templates_by_category.keys()):
        # Add category header
        choices.append({
            "name": f"\n[bold {COLORS['header']}]{category.upper()} TEMPLATES[/bold {COLORS['header']}]",
            "value": None,
            "disabled": True
        })
        
        # Add templates in category
        for name, template in sorted(templates_by_category[category]):
            # Check if it's a plugin template
            if '/' in name:
                plugin_name, template_name = name.split('/', 1)
                display_name = f"  [{plugin_name}] {template_name:<20} {template.description[:40]}"
            else:
                display_name = f"  {name:<30} {template.description[:50]}"
            choices.append({
                "name": display_name,
                "value": name
            })
            choice_map[name] = template
    
    # Use MultiSelectPrompt
    prompt = MultiSelectPrompt(
        "Select templates to install",
        choices,
        hint="Use arrow keys to navigate, space to select, enter to confirm"
    )
    
    selected = prompt.ask()
    
    # Filter out None values (category headers)
    return [name for name in selected if name is not None]


def select_hooks_to_install(
    target_dir: Path,
    category_filter: Optional[str] = None
) -> List[str]:
    """Show hook selection interface."""
    console.print(create_step_indicator(2, 3, "Select Hooks"))
    
    # Load available hooks
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Loading hooks...", total=None)
        
        try:
            hook_registry = get_all_hooks_sync()
            hooks = hook_registry.hooks
        except Exception as e:
            error(f"Failed to load hooks: {e}")
            return []
    
    # Filter by category if specified
    if category_filter:
        filtered_hooks = {
            name: hook for name, hook in hooks.items()
            if hook.category == category_filter.lower()
        }
        if not filtered_hooks:
            warning(f"No hooks found in category: {category_filter}")
            return []
        hooks = filtered_hooks
    
    # Group hooks by category
    hooks_by_category: Dict[str, List[Tuple[str, Any]]] = {}
    for name, hook in hooks.items():
        category = hook.category
        if category not in hooks_by_category:
            hooks_by_category[category] = []
        hooks_by_category[category].append((name, hook))
    
    # Create selection prompt
    choices = []
    choice_map = {}
    
    for category in sorted(hooks_by_category.keys()):
        # Add category header
        choices.append({
            "name": f"\n[bold {COLORS['header']}]{category.upper()} HOOKS[/bold {COLORS['header']}]",
            "value": None,
            "disabled": True
        })
        
        # Add hooks in category
        for name, hook in sorted(hooks_by_category[category]):
            display_name = f"  {name:<30} {hook.description[:50]}"
            choices.append({
                "name": display_name,
                "value": name
            })
            choice_map[name] = hook
    
    # Use MultiSelectPrompt
    prompt = MultiSelectPrompt(
        "Select hooks to install",
        choices,
        hint="Use arrow keys to navigate, space to select, enter to confirm"
    )
    
    selected = prompt.ask()
    
    # Filter out None values (category headers)
    return [name for name in selected if name is not None]


def add_templates(
    template_names: List[str],
    target_dir: Path,
    force: bool,
    dry_run: bool = False
) -> int:
    """Install selected templates."""
    if not template_names:
        warning("No templates selected")
        return 0
    
    console.print(create_step_indicator(3, 3, "Install Templates"))
    
    # Use interactive installation with progress tracking
    report = install_templates_interactive(
        template_names,
        target_dir=target_dir,
        dry_run=dry_run,
        force=force
    )
    
    # Show summary
    if report.successful_installs > 0:
        success_panel = create_success_banner(
            title="✅ Templates Installed",
            message=f"Successfully installed {report.successful_installs} template(s)",
            details={
                "Location": str(target_dir / "commands"),
                "Installed": ", ".join([r.template_name for r in report.results if r.success]),
                "Failed": str(report.failed_installs) if report.failed_installs > 0 else "None",
                "Skipped": str(report.skipped_installs) if report.skipped_installs > 0 else "None",
            }
        )
        console.print(success_panel)
    
    return report.successful_installs


def add_hooks(
    hook_names: List[str],
    target_dir: Path,
    force: bool,
    dry_run: bool = False
) -> int:
    """Install selected hooks."""
    if not hook_names:
        warning("No hooks selected")
        return 0
    
    console.print(create_step_indicator(3, 3, "Install Hooks"))
    
    # Create hook installer
    installer = create_hook_installer(
        target_dir=target_dir,
        dry_run=dry_run,
        force=force,
        backup=True,
        validate_dependencies=True
    )
    
    # Install hooks with progress tracking
    report = installer.install_hooks(hook_names)
    
    # Show summary
    if report.successful_installs > 0:
        success_panel = create_success_banner(
            title="✅ Hooks Installed",
            message=f"Successfully installed {report.successful_installs} hook(s)",
            details={
                "Location": str(target_dir / "hooks"),
                "Installed": ", ".join([r.hook_name for r in report.results if r.success]),
                "Failed": str(report.failed_installs) if report.failed_installs > 0 else "None",
                "Settings Updated": "Yes" if not dry_run else "No (dry run)",
                "Duration": f"{report.duration:.2f}s",
            }
        )
        console.print(success_panel)
    
    # Show any installation errors
    for result in report.results:
        if not result.success:
            error(f"Failed to install {result.hook_name}: {result.message}")
    
    return report.successful_installs


def add_permission(
    permission: str,
    target_dir: Path,
    force: bool
) -> bool:
    """Add a permission to settings.json."""
    settings_file = target_dir / "settings.json"
    
    if not settings_file.exists():
        error(f"Settings file not found at {settings_file}")
        info("Run 'claude-setup init' first to create the configuration")
        return False
    
    try:
        import json
        
        # Read existing settings
        with open(settings_file, 'r') as f:
            settings = json.load(f)
        
        # Ensure permissions structure exists
        if "permissions" not in settings:
            settings["permissions"] = {}
        if "allow" not in settings["permissions"]:
            settings["permissions"]["allow"] = []
        
        # Check if permission already exists
        if permission in settings["permissions"]["allow"] and not force:
            warning(f"Permission already exists: {permission}")
            info("Use --force to add it anyway")
            return False
        
        # Add permission
        if permission not in settings["permissions"]["allow"]:
            settings["permissions"]["allow"].append(permission)
            settings["permissions"]["allow"].sort()
        
        # Save settings
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        
        success(f"Added permission: {permission}")
        return True
        
    except Exception as e:
        error(f"Failed to add permission: {e}")
        return False


def run_add_command(
    type_arg: Optional[str],
    value: Optional[str],
    extra_value: Optional[str],
    test_dir: Optional[str],
    global_config: bool,
    force: bool,
) -> None:
    """Main entry point for the add command."""
    try:
        # Determine target directory
        target_dir = determine_target_directory(test_dir, global_config)
        
        # Check if configuration exists
        if not target_dir.exists():
            error(f"Configuration not found at {target_dir}")
            info("Run 'claude-setup init' first to create the configuration")
            sys.exit(1)
        
        # Determine resource type
        resource_type = None
        if type_arg:
            resource_type = ResourceType.from_string(type_arg)
            if not resource_type:
                error(f"Invalid resource type: {type_arg}")
                info("Valid types: template, hook, permission, settings")
                sys.exit(1)
        
        # Interactive mode if no type specified
        if not resource_type:
            resource_type = show_resource_type_selection()
        
        # Handle different resource types
        if resource_type in [ResourceType.TEMPLATE, ResourceType.TEMPLATES]:
            # Handle template installation
            if value:
                # Direct template name(s) provided
                template_names = [value]
                if extra_value:
                    template_names.append(extra_value)
            else:
                # Interactive selection
                template_names = select_templates_to_install(target_dir)
            
            if template_names:
                count = add_templates(template_names, target_dir, force)
                if count > 0:
                    console.print(f"\n[{COLORS['success']}]✓ Successfully installed {count} template(s)[/{COLORS['success']}]")
                else:
                    console.print(f"\n[{COLORS['warning']}]No templates were installed[/{COLORS['warning']}]")
        
        elif resource_type == ResourceType.PERMISSION:
            # Handle permission addition
            if not value:
                value = Prompt.ask("Enter permission to add (e.g., 'Bash(docker:*)')")
            
            if add_permission(value, target_dir, force):
                console.print(f"\n[{COLORS['success']}]✓ Permission added to settings[/{COLORS['success']}]")
            else:
                sys.exit(1)
        
        elif resource_type in [ResourceType.HOOK, ResourceType.HOOKS]:
            # Handle hook installation
            if value:
                # Direct hook name(s) provided
                hook_names = [value]
                if extra_value:
                    hook_names.append(extra_value)
            else:
                # Interactive selection
                hook_names = select_hooks_to_install(target_dir)
            
            if hook_names:
                count = add_hooks(hook_names, target_dir, force)
                if count > 0:
                    console.print(f"\n[{COLORS['success']}]✓ Successfully installed {count} hook(s)[/{COLORS['success']}]")
                    info("Hooks have been registered in your settings.json and are ready to use")
                else:
                    console.print(f"\n[{COLORS['warning']}]No hooks were installed[/{COLORS['warning']}]")
        
        elif resource_type == ResourceType.SETTINGS:
            # Redirect to settings command
            info("Redirecting to settings management...")
            from .settings import run_settings_command
            run_settings_command(
                action=None,
                test_dir=test_dir,
                global_config=global_config,
                interactive=True,
            )
        
    except KeyboardInterrupt:
        console.print("\n")
        warning("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        error_panel = create_command_error(
            "add",
            e,
            suggestions=[
                "Check that the configuration directory exists",
                "Run 'claude-setup init' if you haven't set up yet",
                "Use --global to add to global configuration",
            ]
        )
        error_console.print(error_panel)
        sys.exit(1)