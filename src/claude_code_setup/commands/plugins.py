"""Plugin management commands for claude-code-setup.

This module provides CLI commands for managing plugins including listing,
installing, removing, and getting information about plugins.
"""

from pathlib import Path
from typing import List, Optional

import click
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..constants import CLAUDE_DIR_NAME, EXIT_CODES
from ..utils.fs import get_claude_home
from ..plugins.loader import PluginLoader
from ..plugins.registry import PluginRegistry
from ..plugins.types import PluginStatus
from ..ui.progress import create_progress_spinner
from ..ui.styles import (
    CLAUDE_PURPLE,
    ERROR_STYLE,
    INFO_STYLE,
    SUCCESS_STYLE,
    WARNING_STYLE,
)
from ..utils.fs import get_claude_home
from ..utils.logger import error, info, success, warning


console = Console()


@click.group(name="plugins", help="Manage Claude Code Setup plugins")
@click.option(
    "--test-dir",
    type=click.Path(path_type=Path),
    help="Use a test directory instead of the actual directory",
)
@click.pass_context
def plugins_group(ctx: click.Context, test_dir: Optional[Path]) -> None:
    """Plugin management commands."""
    # Store config path in context for subcommands
    ctx.ensure_object(dict)
    if test_dir:
        ctx.obj["config_path"] = test_dir / CLAUDE_DIR_NAME
    else:
        ctx.obj["config_path"] = Path.cwd() / CLAUDE_DIR_NAME


@plugins_group.command(name="list")
@click.option(
    "--status",
    type=click.Choice(["all", "available", "installed", "active"]),
    default="all",
    help="Filter plugins by status",
)
@click.option(
    "--no-interactive",
    is_flag=True,
    help="Non-interactive mode",
)
@click.pass_context
def list_plugins(
    ctx: click.Context,
    status: str,
    no_interactive: bool,
) -> None:
    """List available and installed plugins."""
    config_path = ctx.obj["config_path"]
    plugin_dir = config_path / "plugins"
    
    # Initialize registry and loader
    registry_path = plugin_dir / "registry.json"
    registry = PluginRegistry(registry_path)
    loader = PluginLoader(plugin_dir, registry)
    
    # Sync plugins with registry
    with create_progress_spinner("Discovering plugins..."):
        loader.sync_with_registry()
    
    # Get plugins based on filter
    if status == "available":
        plugins = registry.get_available_plugins()
    elif status == "installed":
        plugins = registry.get_installed_plugins()
    elif status == "active":
        plugins = registry.get_active_plugins()
    else:  # all
        plugins = {
            name: plugin
            for name, plugin in registry._plugins.items()
        }
    
    if not plugins:
        console.print(f"No {status} plugins found", style=WARNING_STYLE)
        return
    
    # Create table
    table = Table(
        title=f"Claude Code Setup Plugins ({status.title()})",
        show_header=True,
        header_style="bold",
    )
    
    table.add_column("Plugin", style=CLAUDE_PURPLE, no_wrap=True)
    table.add_column("Version", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Description")
    table.add_column("Provides", style="dim")
    
    # Sort plugins by name
    sorted_plugins = sorted(plugins.items(), key=lambda x: x[0])
    
    for name, plugin in sorted_plugins:
        # Format status
        status_display = {
            PluginStatus.AVAILABLE: "[dim]Available[/dim]",
            PluginStatus.INSTALLED: "[yellow]Installed[/yellow]",
            PluginStatus.ACTIVE: "[green]Active[/green]",
            PluginStatus.DISABLED: "[red]Disabled[/red]",
            PluginStatus.ERROR: "[red]Error[/red]",
        }.get(plugin.status, plugin.status.value)
        
        # Format capabilities
        provides = []
        caps = plugin.manifest.provides
        if caps.templates:
            provides.append(f"{len(caps.templates)} templates")
        if caps.hooks:
            provides.append(f"{len(caps.hooks)} hooks")
        if caps.agents:
            provides.append(f"{len(caps.agents)} agents")
        if caps.workflows:
            provides.append(f"{len(caps.workflows)} workflows")
        if caps.commands:
            provides.append(f"{len(caps.commands)} commands")
        
        provides_str = ", ".join(provides) if provides else "[dim]None[/dim]"
        
        table.add_row(
            plugin.manifest.metadata.display_name,
            plugin.version,
            status_display,
            plugin.manifest.metadata.description,
            provides_str,
        )
    
    console.print(table)
    
    # Show stats
    stats = registry.get_stats()
    console.print(
        f"\nTotal: {stats['total']} plugins, "
        f"{stats['installed']} installed, "
        f"{stats['active']} active",
        style="dim",
    )
    
    # Interactive mode
    if not no_interactive and plugins:
        console.print()
        action = questionary.select(
            "What would you like to do?",
            choices=[
                "Install a plugin",
                "Remove a plugin",
                "Get plugin info",
                "Exit",
            ],
        ).ask()
        
        if action == "Install a plugin":
            available = registry.get_available_plugins()
            if not available:
                console.print("No plugins available to install", style=WARNING_STYLE)
                return
            
            plugin_name = questionary.select(
                "Select a plugin to install:",
                choices=list(available.keys()) + ["Cancel"],
            ).ask()
            
            if plugin_name != "Cancel":
                ctx.invoke(add_plugin, plugin_name=plugin_name)
        
        elif action == "Remove a plugin":
            installed = registry.get_installed_plugins()
            if not installed:
                console.print("No plugins installed", style=WARNING_STYLE)
                return
            
            plugin_name = questionary.select(
                "Select a plugin to remove:",
                choices=list(installed.keys()) + ["Cancel"],
            ).ask()
            
            if plugin_name != "Cancel":
                ctx.invoke(remove_plugin, plugin_name=plugin_name)
        
        elif action == "Get plugin info":
            plugin_name = questionary.select(
                "Select a plugin:",
                choices=list(plugins.keys()) + ["Cancel"],
            ).ask()
            
            if plugin_name != "Cancel":
                ctx.invoke(plugin_info, plugin_name=plugin_name)


@plugins_group.command(name="add")
@click.argument("plugin_name", required=False)
@click.option(
    "--from-file",
    type=click.Path(exists=True, path_type=Path),
    help="Install plugin from a file or directory",
)
@click.option(
    "--activate",
    is_flag=True,
    help="Activate plugin after installation",
)
@click.pass_context
def add_plugin(
    ctx: click.Context,
    plugin_name: Optional[str],
    from_file: Optional[Path],
    activate: bool,
) -> None:
    """Install a plugin."""
    config_path = ctx.obj["config_path"]
    plugin_dir = config_path / "plugins"
    
    # Initialize registry and loader
    registry_path = plugin_dir / "registry.json"
    registry = PluginRegistry(registry_path)
    loader = PluginLoader(plugin_dir, registry)
    
    try:
        if from_file:
            # Install from file
            with create_progress_spinner(f"Installing plugin from {from_file}..."):
                plugin = loader.install_from_file(from_file)
            
            success(f"Installed plugin: {plugin.name} v{plugin.version}")
            
        else:
            # Install from repository
            if not plugin_name:
                # Interactive selection
                loader.sync_with_registry()
                available = registry.get_available_plugins()
                
                if not available:
                    console.print("No plugins available to install", style=WARNING_STYLE)
                    return
                
                plugin_name = questionary.select(
                    "Select a plugin to install:",
                    choices=list(available.keys()),
                ).ask()
                
                if not plugin_name:
                    return
            
            with create_progress_spinner(f"Installing {plugin_name}..."):
                plugin = loader.install_plugin(plugin_name)
            
            success(f"Installed plugin: {plugin_name} v{plugin.version}")
        
        # Activate if requested
        if activate:
            with create_progress_spinner(f"Activating {plugin.name}..."):
                loader.activate_plugin(plugin.name)
            
            success(f"Activated plugin: {plugin.name}")
        
        # Show what the plugin provides
        caps = plugin.manifest.provides
        if not caps.is_empty():
            console.print("\nThis plugin provides:", style=INFO_STYLE)
            
            if caps.templates:
                console.print(f"  Templates: {', '.join(caps.templates)}")
            if caps.hooks:
                console.print(f"  Hooks: {', '.join(caps.hooks)}")
            if caps.agents:
                console.print(f"  Agents: {', '.join(caps.agents)}")
            if caps.workflows:
                console.print(f"  Workflows: {', '.join(caps.workflows)}")
            if caps.commands:
                console.print(f"  Commands: {', '.join(caps.commands)}")
        
    except Exception as e:
        error(f"Failed to install plugin: {e}")
        raise click.Exit(EXIT_CODES.ERROR)


@plugins_group.command(name="remove")
@click.argument("plugin_name", required=False)
@click.option(
    "--force",
    is_flag=True,
    help="Force removal even if other plugins depend on it",
)
@click.pass_context
def remove_plugin(
    ctx: click.Context,
    plugin_name: Optional[str],
    force: bool,
) -> None:
    """Remove an installed plugin."""
    config_path = ctx.obj["config_path"]
    plugin_dir = config_path / "plugins"
    
    # Initialize registry and loader
    registry_path = plugin_dir / "registry.json"
    registry = PluginRegistry(registry_path)
    loader = PluginLoader(plugin_dir, registry)
    
    if not plugin_name:
        # Interactive selection
        installed = registry.get_installed_plugins()
        
        if not installed:
            console.print("No plugins installed", style=WARNING_STYLE)
            return
        
        plugin_name = questionary.select(
            "Select a plugin to remove:",
            choices=list(installed.keys()),
        ).ask()
        
        if not plugin_name:
            return
    
    # Check if plugin exists
    plugin = registry.get_plugin(plugin_name)
    if not plugin or not plugin.is_installed:
        error(f"Plugin {plugin_name} is not installed")
        raise click.Exit(EXIT_CODES.ERROR)
    
    # Confirm removal
    if not force:
        # Check for dependents
        dependents = registry.get_dependents(plugin_name)
        if dependents:
            console.print(
                f"\n[yellow]Warning:[/yellow] The following plugins depend on {plugin_name}:",
                style=WARNING_STYLE,
            )
            for dep in dependents:
                console.print(f"  - {dep.name}")
            console.print()
        
        confirm = questionary.confirm(
            f"Remove plugin {plugin_name}?",
            default=False,
        ).ask()
        
        if not confirm:
            return
    
    try:
        with create_progress_spinner(f"Removing {plugin_name}..."):
            loader.uninstall_plugin(plugin_name, force=force)
        
        success(f"Removed plugin: {plugin_name}")
        
    except Exception as e:
        error(f"Failed to remove plugin: {e}")
        raise click.Exit(EXIT_CODES.ERROR)


@plugins_group.command(name="info")
@click.argument("plugin_name")
@click.pass_context
def plugin_info(ctx: click.Context, plugin_name: str) -> None:
    """Show detailed information about a plugin."""
    config_path = ctx.obj["config_path"]
    plugin_dir = config_path / "plugins"
    
    # Initialize registry
    registry_path = plugin_dir / "registry.json"
    registry = PluginRegistry(registry_path)
    registry.load()
    
    # Get plugin
    plugin = registry.get_plugin(plugin_name)
    if not plugin:
        error(f"Plugin {plugin_name} not found")
        raise click.Exit(EXIT_CODES.ERROR)
    
    # Create info panel
    metadata = plugin.manifest.metadata
    
    info_lines = [
        f"[bold]{metadata.display_name}[/bold] v{metadata.version}",
        f"[dim]{metadata.description}[/dim]",
        "",
        f"[bold]Author:[/bold] {metadata.author}",
        f"[bold]License:[/bold] {metadata.license}",
        f"[bold]Category:[/bold] {metadata.category}",
        f"[bold]Status:[/bold] {plugin.status.value}",
    ]
    
    if metadata.homepage:
        info_lines.append(f"[bold]Homepage:[/bold] {metadata.homepage}")
    
    if metadata.repository:
        info_lines.append(f"[bold]Repository:[/bold] {metadata.repository}")
    
    if metadata.keywords:
        info_lines.append(f"[bold]Keywords:[/bold] {', '.join(metadata.keywords)}")
    
    if plugin.install_date:
        info_lines.append(
            f"[bold]Installed:[/bold] {plugin.install_date.strftime('%Y-%m-%d %H:%M')}"
        )
    
    # Dependencies
    if plugin.manifest.dependencies:
        info_lines.extend(["", "[bold]Dependencies:[/bold]"])
        for dep in plugin.manifest.dependencies:
            optional = " (optional)" if dep.optional else ""
            info_lines.append(f"  - {dep.name} {dep.version}{optional}")
    
    # Capabilities
    caps = plugin.manifest.provides
    if not caps.is_empty():
        info_lines.extend(["", "[bold]Provides:[/bold]"])
        
        if caps.templates:
            info_lines.append(f"  Templates: {', '.join(caps.templates)}")
        if caps.hooks:
            info_lines.append(f"  Hooks: {', '.join(caps.hooks)}")
        if caps.agents:
            info_lines.append(f"  Agents: {', '.join(caps.agents)}")
        if caps.workflows:
            info_lines.append(f"  Workflows: {', '.join(caps.workflows)}")
        if caps.commands:
            info_lines.append(f"  Commands: {', '.join(caps.commands)}")
    
    # Errors
    if plugin.errors:
        info_lines.extend(["", "[bold red]Errors:[/bold red]"])
        for err in plugin.errors:
            info_lines.append(f"  - {err}")
    
    panel = Panel(
        "\n".join(info_lines),
        title=f"Plugin: {plugin_name}",
        border_style=CLAUDE_PURPLE,
    )
    
    console.print(panel)


@plugins_group.command(name="activate")
@click.argument("plugin_name")
@click.pass_context
def activate_plugin(ctx: click.Context, plugin_name: str) -> None:
    """Activate an installed plugin."""
    config_path = ctx.obj["config_path"]
    plugin_dir = config_path / "plugins"
    
    # Initialize registry and loader
    registry_path = plugin_dir / "registry.json"
    registry = PluginRegistry(registry_path)
    loader = PluginLoader(plugin_dir, registry)
    
    try:
        with create_progress_spinner(f"Activating {plugin_name}..."):
            loader.activate_plugin(plugin_name)
        
        success(f"Activated plugin: {plugin_name}")
        
    except Exception as e:
        error(f"Failed to activate plugin: {e}")
        raise click.Exit(EXIT_CODES.ERROR)


@plugins_group.command(name="deactivate")
@click.argument("plugin_name")
@click.pass_context
def deactivate_plugin(ctx: click.Context, plugin_name: str) -> None:
    """Deactivate a plugin."""
    config_path = ctx.obj["config_path"]
    plugin_dir = config_path / "plugins"
    
    # Initialize registry and loader
    registry_path = plugin_dir / "registry.json"
    registry = PluginRegistry(registry_path)
    loader = PluginLoader(plugin_dir, registry)
    
    try:
        with create_progress_spinner(f"Deactivating {plugin_name}..."):
            loader.deactivate_plugin(plugin_name)
        
        success(f"Deactivated plugin: {plugin_name}")
        
    except Exception as e:
        error(f"Failed to deactivate plugin: {e}")
        raise click.Exit(EXIT_CODES.ERROR)


def run_plugins_command(
    ctx: click.Context,
    args: List[str],
    prog_name: str,
) -> int:
    """Run the plugins command.
    
    Args:
        ctx: Click context
        args: Command arguments
        prog_name: Program name
        
    Returns:
        Exit code
    """
    return plugins_group(args, prog_name)