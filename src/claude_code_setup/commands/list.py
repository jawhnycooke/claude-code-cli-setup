"""List command implementation for claude-code-setup.

This module implements the list command, converted from TypeScript list.ts.
Displays available templates, hooks, and settings with rich formatting and interactive options.
"""

import sys
from pathlib import Path
from typing import Optional

from rich.progress import Progress, SpinnerColumn, TextColumn

from ..utils import (
    info,
    warning,
    error,
    CLAUDE_HOME,
    CLAUDE_COMMANDS_DIR,
)
from ..utils.template import (
    get_all_templates_sync,
    get_template_categories_sync,
)
from ..utils.settings import (
    get_available_themes_sync,
    get_available_permission_sets_sync,
)
from ..types import TemplateCategory

# Import styled console and components from centralized styles
from ..ui.styles import (
    console,
    error_console,
    create_table,
    create_panel,
    create_error_banner,
    format_error,
    create_command_error,
    COLORS,
    BOX_STYLES,
    style_header,
    style_status,
)


def determine_target_directory(test_dir: Optional[str], global_config: bool) -> Path:
    """Determine the target directory for checking installed items."""
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


def show_templates(
    category_filter: Optional[str] = None,
    installed_only: bool = False,
    target_dir: Optional[Path] = None,
) -> None:
    """Show available templates with installation status."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Loading templates...", total=None)
            
            # Get all templates
            template_registry = get_all_templates_sync()
            templates = template_registry.templates
            
            progress.stop()
            
        if not templates:
            warning("No templates found. Please ensure template files exist.")
            return
        
        # Get all categories
        categories = set(template.category for template in templates.values())
        
        # Filter by category if specified
        if category_filter:
            try:
                category_enum = TemplateCategory(category_filter.lower())
                filtered_categories = {category_enum}
            except ValueError:
                error_panel = create_error_banner(
                    title="⚠️  Invalid Category",
                    message=f"'{category_filter}' is not a valid category",
                    suggestions=[
                        f"Available categories: {', '.join(c.value for c in TemplateCategory)}",
                        "Run 'claude-setup list' without category filter to see all templates",
                    ],
                )
                console.print(error_panel)
                return
        else:
            filtered_categories = categories
        
        if not filtered_categories:
            warning(f"No templates found for category: {category_filter}")
            return
        
        # Display templates by category
        console.print("\n[bold cyan]📄 Available Templates[/bold cyan]")
        
        for category in sorted(filtered_categories, key=lambda x: x.value):
            category_templates = [
                template for template in templates.values()
                if template.category == category
            ]
            
            if not category_templates:
                continue
            
            # Create table for this category
            table = create_table(
                title=f"{category.value.upper()} Templates",
                show_header=True,
                header_style="bold",
                border_style=COLORS["primary"],
            )
            table.add_column("Name", style="green", width=20)
            table.add_column("Status", width=12, justify="center")
            table.add_column("Description", style="dim")
            
            has_templates = False
            
            for template in sorted(category_templates, key=lambda x: x.name):
                # Check if template is installed
                if target_dir:
                    commands_dir = target_dir / "commands"
                    template_path = commands_dir / category.value / f"{template.name}.md"
                    is_installed = template_path.exists()
                else:
                    is_installed = False
                
                # Skip if showing only installed and this one isn't
                if installed_only and not is_installed:
                    continue
                
                # Format installation status
                status = "[green]✓ installed[/green]" if is_installed else "[dim]not installed[/dim]"
                
                table.add_row(
                    template.name,
                    status,
                    template.description[:60] + "..." if len(template.description) > 60 else template.description
                )
                has_templates = True
            
            if has_templates:
                console.print(table)
                console.print()
        
        # Show usage information
        console.print("[dim]💡 To add a template, run:[/dim]")
        console.print("[blue]  claude-setup add template <template-name>[/blue]")
        
    except Exception as e:
        error_panel = create_command_error(
            "list",
            e,
            suggestions=[
                "Check that the template files are accessible",
                "Ensure the package was installed correctly",
            ]
        )
        error_console.print(error_panel)
        sys.exit(1)


def show_hooks(target_dir: Optional[Path] = None) -> None:
    """Show available hooks with installation status."""
    console.print("\n[bold magenta]🛡️ Available Hooks[/bold magenta]")
    
    # For now, show a placeholder as hooks aren't fully implemented yet
    table = create_table(
        show_header=True,
        header_style="bold",
        border_style=COLORS["secondary"],
    )
    table.add_column("Category", style="cyan", width=15)
    table.add_column("Hook", style="green", width=25)
    table.add_column("Status", width=12, justify="center")
    table.add_column("Description", style="dim")
    
    # Add some example hooks from the codebase structure
    hooks_data = [
        ("security", "file-change-limiter", False, "Limits the number of files that can be modified"),
        ("security", "command-validator", False, "Validates commands before execution"),
        ("security", "sensitive-file-protector", False, "Protects sensitive files from modification"),
        ("aws", "deployment-guard", False, "Guards against unsafe AWS deployments"),
        ("testing", "test-enforcement", False, "Enforces running tests on changes"),
    ]
    
    for category, hook_name, is_installed, description in hooks_data:
        if target_dir:
            hooks_dir = target_dir / "hooks" / category
            hook_path = hooks_dir / hook_name
            is_installed = hook_path.exists()
        
        status = "[green]✓ installed[/green]" if is_installed else "[dim]not installed[/dim]"
        table.add_row(category, hook_name, status, description)
    
    console.print(table)
    console.print()
    
    console.print("[dim]💡 To add hooks, run:[/dim]")
    console.print("[blue]  claude-setup hooks add <hook-name>[/blue]")


def show_settings(target_dir: Optional[Path] = None) -> None:
    """Show available settings and themes."""
    console.print("\n[bold yellow]⚙️  Available Settings[/bold yellow]")
    
    try:
        # Get available themes
        themes = get_available_themes_sync()
        permission_sets = get_available_permission_sets_sync()
        
        # Create settings table
        table = create_table(
            show_header=True,
            header_style="bold",
            border_style=COLORS["accent"],
        )
        table.add_column("Type", style="cyan", width=15)
        table.add_column("Name", style="green", width=20)
        table.add_column("Status", width=12, justify="center")
        table.add_column("Description", style="dim")
        
        # Show themes
        for theme in themes:
            if target_dir:
                settings_file = target_dir / "settings.json"
                is_configured = settings_file.exists()
            else:
                is_configured = False
            
            status = "[green]✓ available[/green]" if is_configured else "[dim]available[/dim]"
            description = f"Theme configuration for {theme} styling"
            table.add_row("theme", theme, status, description)
        
        # Show permission sets
        for perm_set in permission_sets[:5]:  # Show first 5 to avoid clutter
            status = "[green]✓ available[/green]"
            description = f"Permission set for {perm_set} commands"
            table.add_row("permissions", perm_set, status, description)
        
        if len(permission_sets) > 5:
            table.add_row("permissions", f"... and {len(permission_sets) - 5} more", "", "")
        
        console.print(table)
        console.print()
        
        # Show current settings status
        if target_dir:
            settings_file = target_dir / "settings.json"
            if settings_file.exists():
                console.print(f"[green]✓ Settings configured at: {settings_file}[/green]")
            else:
                console.print(f"[dim]Settings not yet configured. Run 'claude-setup init' to set up.[/dim]")
        
        console.print("\n[dim]💡 To configure settings, run:[/dim]")
        console.print("[blue]  claude-setup init[/blue]")
        
    except Exception as e:
        error_panel = create_command_error(
            "list",
            e,
            suggestions=[
                "Check that the settings files are accessible",
                "Try running 'claude-setup init' to create initial settings",
            ]
        )
        error_console.print(error_panel)
        sys.exit(1)


def show_all_resources(
    category_filter: Optional[str] = None,
    installed_only: bool = False,
    target_dir: Optional[Path] = None,
) -> None:
    """Show all available resources (templates, hooks, settings)."""
    console.print()
    console.print(create_panel(
        f"[{COLORS['header']}]📋 Claude Code Resources Overview[/{COLORS['header']}]\n"
        f"[{COLORS['muted']}]Available templates, hooks, and settings for your project[/{COLORS['muted']}]",
        border_style=COLORS["primary"],
        padding=(1, 2),
    ))
    
    # Show templates
    show_templates(category_filter, installed_only, target_dir)
    
    # Show hooks
    show_hooks(target_dir)
    
    # Show settings
    show_settings(target_dir)
    
    console.print("\n[dim]For more details on any section, use:[/dim]")
    console.print("[blue]  claude-setup list templates[/blue]")
    console.print("[blue]  claude-setup list hooks[/blue]")
    console.print("[blue]  claude-setup list settings[/blue]")


def run_list_command(
    resource_type: Optional[str] = None,
    category: Optional[str] = None,
    installed: bool = False,
    test_dir: Optional[str] = None,
    global_config: bool = False,
    interactive: bool = True,
) -> None:
    """Main entry point for the list command."""
    try:
        # Determine target directory
        target_dir = determine_target_directory(test_dir, global_config) if test_dir or global_config else None
        
        # Show appropriate resources based on type
        if resource_type == "templates":
            show_templates(category, installed, target_dir)
        elif resource_type == "hooks":
            show_hooks(target_dir)
        elif resource_type == "settings":
            show_settings(target_dir)
        else:
            # Show all resources
            show_all_resources(category, installed, target_dir)
        
        # Interactive actions (if enabled)
        if interactive and resource_type != "settings":
            console.print()
            console.print("[dim]💡 Tip: Use --no-interactive to skip interactive prompts[/dim]")
            # TODO: Add interactive actions in future enhancement
        
    except KeyboardInterrupt:
        console.print("\n")
        interrupted_panel = create_error_banner(
            title="⌨️  Operation Cancelled",
            message="List operation was interrupted by user",
        )
        console.print(interrupted_panel)
        sys.exit(1)
    except Exception as e:
        error_panel = format_error(
            e,
            title="Unexpected Error",
            suggestions=[
                "Please report this issue at https://github.com/anthropics/claude-code/issues",
                "Try running with '--help' to see available options",
            ],
            show_traceback=True,
        )
        error_console.print(error_panel)
        sys.exit(1)