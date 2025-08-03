"""Interactive command workflows for claude-code-setup."""

from pathlib import Path
from typing import Optional, List, Dict, Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text

from ..ui.prompts import MultiSelectPrompt, ValidatedPrompt
from ..ui.progress import MultiStepProgress, ProgressStep
from ..ui.styles import (
    create_panel,
    create_gradient_text,
    console as styled_console,
)
from ..utils.logger import info, success, warning
from ..core.registry import get_registry

console = Console()


def show_main_menu() -> Optional[str]:
    """Show the main interactive menu.
    
    Returns:
        Selected action or None if cancelled
    """
    # Create header
    header = create_gradient_text(
        "Claude Code Setup - Interactive Mode",
        style="bold",
    )
    console.print("\n")
    console.print(header, justify="center")
    console.print("\n")
    
    # Create menu options
    options = [
        ("🚀", "Quick Setup", "Initialize with recommended settings"),
        ("📝", "Manage Templates", "Add, update, or remove templates"),
        ("🛡️", "Manage Hooks", "Configure automation and security hooks"),
        ("⚙️", "Configure Settings", "Customize themes and permissions"),
        ("📋", "View Configuration", "List installed templates and settings"),
        ("🔄", "Update All", "Update all installed templates"),
        ("❌", "Exit", "Exit interactive mode"),
    ]
    
    # Create options table
    table = Table(
        show_header=False,
        box=None,
        padding=(0, 2),
        expand=True,
    )
    
    for icon, title, description in options:
        table.add_row(
            f"[cyan]{icon}[/cyan]",
            f"[bold]{title}[/bold]",
            f"[dim]{description}[/dim]",
        )
    
    console.print(
        Panel(
            table,
            title="What would you like to do?",
            border_style="cyan",
            padding=(1, 2),
        )
    )
    
    # Create prompt
    prompt = ValidatedPrompt(
        message="Select an option (1-7)",
        validator=lambda x: (
            x.isdigit() and 1 <= int(x) <= 7,
            None if x.isdigit() and 1 <= int(x) <= 7 else "Please enter a number between 1-7"
        ),
    )
    
    choice = prompt.ask()
    if not choice:
        return None
        
    action_map = {
        "1": "quick-setup",
        "2": "manage-templates",
        "3": "manage-hooks",
        "4": "configure-settings",
        "5": "view-config",
        "6": "update-all",
        "7": None,
    }
    
    return action_map.get(choice)


def template_management_menu() -> Optional[str]:
    """Show template management submenu.
    
    Returns:
        Selected action or None if cancelled
    """
    console.print("\n[bold cyan]Template Management[/bold cyan]\n")
    
    options = [
        ("➕", "Add Templates", "Install new templates"),
        ("🔄", "Update Templates", "Update installed templates"),
        ("➖", "Remove Templates", "Remove installed templates"),
        ("🔍", "Search Templates", "Search for specific templates"),
        ("👁️", "Preview Template", "View template content before installing"),
        ("⬅️", "Back to Main Menu", "Return to main menu"),
    ]
    
    # Create options table
    table = Table(
        show_header=False,
        box=None,
        padding=(0, 2),
    )
    
    for icon, title, description in options:
        table.add_row(
            f"[yellow]{icon}[/yellow]",
            f"[bold]{title}[/bold]",
            f"[dim]{description}[/dim]",
        )
    
    console.print(table)
    
    prompt = ValidatedPrompt(
        message="Select an option (1-6)",
        validator=lambda x: (
            x.isdigit() and 1 <= int(x) <= 6,
            None if x.isdigit() and 1 <= int(x) <= 6 else "Please enter a number between 1-6"
        ),
    )
    
    choice = prompt.ask()
    if not choice:
        return None
        
    action_map = {
        "1": "add-templates",
        "2": "update-templates",
        "3": "remove-templates",
        "4": "search-templates",
        "5": "preview-template",
        "6": "main-menu",
    }
    
    return action_map.get(choice)


def settings_configuration_menu() -> Optional[str]:
    """Show settings configuration submenu.
    
    Returns:
        Selected action or None if cancelled
    """
    console.print("\n[bold cyan]Settings Configuration[/bold cyan]\n")
    
    options = [
        ("🎨", "Change Theme", "Select a different UI theme"),
        ("🔑", "Manage Permissions", "Add or remove tool permissions"),
        ("🌍", "Environment Variables", "Configure environment variables"),
        ("💾", "Export Settings", "Export settings to share"),
        ("📥", "Import Settings", "Import settings from file"),
        ("🔄", "Reset to Defaults", "Reset all settings to defaults"),
        ("⬅️", "Back to Main Menu", "Return to main menu"),
    ]
    
    # Create options table
    table = Table(
        show_header=False,
        box=None,
        padding=(0, 2),
    )
    
    for icon, title, description in options:
        table.add_row(
            f"[green]{icon}[/green]",
            f"[bold]{title}[/bold]",
            f"[dim]{description}[/dim]",
        )
    
    console.print(table)
    
    prompt = ValidatedPrompt(
        message="Select an option (1-7)",
        validator=lambda x: (
            x.isdigit() and 1 <= int(x) <= 7,
            None if x.isdigit() and 1 <= int(x) <= 7 else "Please enter a number between 1-7"
        ),
    )
    
    choice = prompt.ask()
    if not choice:
        return None
        
    action_map = {
        "1": "change-theme",
        "2": "manage-permissions",
        "3": "env-variables",
        "4": "export-settings",
        "5": "import-settings",
        "6": "reset-settings",
        "7": "main-menu",
    }
    
    return action_map.get(choice)


def search_templates_interactive(templates: List[Any]) -> Optional[List[str]]:
    """Interactive template search with filtering.
    
    Args:
        templates: List of available templates
        
    Returns:
        Selected template names or None if cancelled
    """
    console.print("\n[bold cyan]Search Templates[/bold cyan]\n")
    
    # Get search query
    search_prompt = ValidatedPrompt(
        message="Enter search terms (or press Enter to browse all)",
        validator=lambda x: (True, None),  # Accept any input
        default="",
    )
    
    query = search_prompt.ask()
    if query is None:
        return None
        
    # Filter templates
    filtered_templates = []
    query_lower = query.lower()
    
    for template in templates:
        if not query or (
            query_lower in template.name.lower() or
            query_lower in template.description.lower() or
            query_lower in template.category.lower()
        ):
            filtered_templates.append(template)
    
    if not filtered_templates:
        warning("No templates found matching your search.")
        return None
        
    # Group by category
    by_category = {}
    for template in filtered_templates:
        if template.category not in by_category:
            by_category[template.category] = []
        by_category[template.category].append(template)
    
    # Create selection choices
    choices = []
    for category in sorted(by_category.keys()):
        choices.append(f"[dim]{category.upper()}[/dim]")
        for template in sorted(by_category[category], key=lambda t: t.name):
            choices.append(f"  {template.name} - {template.description}")
    
    # Show multi-select
    prompt = MultiSelectPrompt(
        title="Select templates to install",
        options=choices,
        min_selections=0,
    )
    
    selected = prompt.ask()
    if not selected:
        return None
        
    # Extract template names
    template_names = []
    for choice in selected:
        if choice.startswith("  "):
            name = choice[2:].split(" - ")[0]
            template_names.append(name)
            
    return template_names


def preview_template_interactive(templates: List[Any]) -> bool:
    """Show template content preview.
    
    Args:
        templates: List of available templates
        
    Returns:
        True to continue browsing, False to exit
    """
    from ..utils.template import get_template_sync
    
    console.print("\n[bold cyan]Template Preview[/bold cyan]\n")
    
    # Get template name
    name_prompt = ValidatedPrompt(
        message="Enter template name to preview (or 'list' to see available)",
        validator=lambda x: (True, None),  # Accept any input
    )
    
    name = name_prompt.ask()
    if not name:
        return False
        
    if name.lower() == "list":
        # Show available templates
        table = Table(title="Available Templates", show_header=True)
        table.add_column("Name", style="cyan")
        table.add_column("Category", style="yellow")
        table.add_column("Description", style="dim")
        
        for template in sorted(templates, key=lambda t: (t.category, t.name)):
            table.add_row(
                template.name,
                template.category,
                template.description,
            )
        
        console.print(table)
        return True
        
    # Get template
    template = get_template_sync(name)
    if not template:
        warning(f"Template '{name}' not found.")
        return True
        
    # Show template content
    console.print(
        Panel(
            template.content,
            title=f"Template: {template.name}",
            subtitle=f"Category: {template.category}",
            border_style="cyan",
            padding=(1, 2),
        )
    )
    
    # Ask if they want to install
    install_prompt = ValidatedPrompt(
        message="Would you like to install this template? (y/n)",
        validator=lambda x: (
            x.lower() in ["y", "n", "yes", "no"],
            "Please enter 'y' or 'n'"
        ),
    )
    
    response = install_prompt.ask()
    if response and response.lower() in ["y", "yes"]:
        info(f"Use 'claude-setup add {template.name}' to install this template.")
    
    return True


def create_configuration_summary(target_dir: Path) -> Panel:
    """Create a summary panel of current configuration.
    
    Args:
        target_dir: Target directory for configuration
        
    Returns:
        Rich panel with configuration summary
    """
    from ..utils.settings import read_settings_sync
    from ..commands.remove import find_installed_templates_for_removal
    
    # Read settings
    settings = read_settings_sync(target_dir / "settings.json")
    
    # Find installed templates
    installed = find_installed_templates_for_removal(target_dir)
    
    # Create summary content
    summary_parts = []
    
    # Settings info
    if settings:
        theme = getattr(settings, 'theme', 'default')
        summary_parts.append(f"[cyan]Theme:[/cyan] {theme}")
        
        # Count permissions
        permission_count = 0
        if hasattr(settings, 'permissions') and settings.permissions:
            permission_count = len(getattr(settings.permissions, 'allow', []))
        elif hasattr(settings, 'allowedTools'):
            permission_count = len(settings.allowedTools)
            
        summary_parts.append(f"[cyan]Permissions:[/cyan] {permission_count} allowed tools")
    
    # Template info
    template_count = len(installed)
    summary_parts.append(f"[cyan]Templates:[/cyan] {template_count} installed")
    
    if installed:
        # Group by category
        by_category = {}
        for name, category, _ in installed:
            if category not in by_category:
                by_category[category] = 0
            by_category[category] += 1
            
        category_summary = ", ".join(
            f"{cat}: {count}" for cat, count in sorted(by_category.items())
        )
        summary_parts.append(f"[dim]Categories: {category_summary}[/dim]")
    
    # Create panel
    return Panel(
        "\n".join(summary_parts),
        title="Current Configuration",
        border_style="green",
        padding=(1, 2),
    )


def run_interactive_mode(ctx: click.Context, target_dir: Path) -> None:
    """Run the main interactive mode.
    
    Args:
        ctx: Click context
        target_dir: Target directory for operations
    """
    # Show welcome
    welcome = create_gradient_text(
        "Welcome to Claude Code Setup Interactive Mode",
        style="bold",
    )
    console.print("\n")
    console.print(welcome, justify="center")
    console.print("\n")
    
    # Show current configuration
    console.print(create_configuration_summary(target_dir))
    
    # Main loop
    while True:
        action = show_main_menu()
        
        if not action:
            break
            
        if action == "quick-setup":
            # Run init command
            from .init import run_init_command
            run_init_command(
                ctx=ctx,
                quick=True,
                force=False,
                test_dir=None,
                global_config=target_dir == Path.home() / ".claude",
                permissions=None,
                theme=None,
                no_check=False,
                no_interactive=False,
                dry_run=False,
            )
            
        elif action == "manage-templates":
            # Template submenu
            while True:
                sub_action = template_management_menu()
                if not sub_action or sub_action == "main-menu":
                    break
                    
                if sub_action == "add-templates":
                    from .add import run_add_command
                    run_add_command(
                        ctx=ctx,
                        resource_type=None,
                        names=(),
                        test_dir=target_dir if target_dir != Path.home() / ".claude" else None,
                        force=False,
                        dry_run=False,
                    )
                    
                elif sub_action == "update-templates":
                    from .update import run_update_command
                    run_update_command(
                        ctx=ctx,
                        templates=(),
                        all=False,
                        force=False,
                        test_dir=target_dir if target_dir != Path.home() / ".claude" else None,
                        dry_run=False,
                        settings=False,
                        global_settings=False,
                    )
                    
                elif sub_action == "remove-templates":
                    from .remove import run_remove_command
                    run_remove_command(
                        ctx=ctx,
                        templates=(),
                        all=False,
                        permission=None,
                        test_dir=target_dir if target_dir != Path.home() / ".claude" else None,
                        dry_run=False,
                        force=False,
                    )
                    
                elif sub_action == "search-templates":
                    from ..utils.template import get_all_templates_sync
                    templates = get_all_templates_sync()
                    selected = search_templates_interactive(
                        list(templates.templates.values())
                    )
                    if selected:
                        info(f"Selected {len(selected)} template(s) for installation.")
                        # Could trigger add command with selected templates
                        
                elif sub_action == "preview-template":
                    from ..utils.template import get_all_templates_sync
                    templates = get_all_templates_sync()
                    while preview_template_interactive(
                        list(templates.templates.values())
                    ):
                        pass
                        
        elif action == "manage-hooks":
            warning("Hook management will be available in Phase 8.")
            
        elif action == "configure-settings":
            # Settings submenu
            while True:
                sub_action = settings_configuration_menu()
                if not sub_action or sub_action == "main-menu":
                    break
                    
                if sub_action == "change-theme":
                    info("Use 'claude-setup init --theme <name>' to change theme.")
                elif sub_action == "manage-permissions":
                    info("Use 'claude-setup add --permission' or 'remove --permission' to manage permissions.")
                elif sub_action == "reset-settings":
                    warning("This will reset all settings to defaults. Use 'claude-setup init --force' to reset.")
                else:
                    info(f"Feature '{sub_action}' coming soon!")
                    
        elif action == "view-config":
            from .list import run_list_command
            run_list_command(
                ctx=ctx,
                resource_type=None,
                category=None,
                installed=False,
                test_dir=target_dir if target_dir != Path.home() / ".claude" else None,
                global_config=False,
                no_interactive=True,
            )
            
        elif action == "update-all":
            from .update import run_update_command
            run_update_command(
                ctx=ctx,
                templates=(),
                all=True,
                force=False,
                test_dir=target_dir if target_dir != Path.home() / ".claude" else None,
                dry_run=False,
                settings=False,
                global_settings=False,
            )
    
    # Show outro
    console.print("\n")
    success("Thank you for using Claude Code Setup!")
    console.print("[dim]Run 'claude-setup --help' for more options.[/dim]\n")