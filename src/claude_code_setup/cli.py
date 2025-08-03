"""Main CLI entry point for claude-code-setup.

This module defines the main CLI application structure using Click,
maintaining compatibility with the original Commander.js implementation.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from . import __version__
from .core.registry import get_registry
from .core.loader import create_command_loader
from .core.extensions import create_extension_manager

# Initialize rich console for styled output
console = Console()

# Initialize command registry and loader
registry = get_registry()
loader = create_command_loader(registry)
extension_manager = create_extension_manager(registry, loader)


# Global context for CLI options
class CLIContext:
    """Global context for CLI state."""

    def __init__(self) -> None:
        self.no_interactive: bool = False
        self.debug: bool = False
        self.current_dir: Path = Path.cwd()

    def is_interactive(self) -> bool:
        """Check if interactive mode is enabled."""
        return not self.no_interactive


# Global context instance
cli_context = CLIContext()


def show_welcome_banner() -> None:
    """Show the welcome banner using rich formatting."""
    console.print("🤖 [bold cyan]Claude Code Setup[/bold cyan]")
    console.print(
        "[dim]Setup and configure Claude Code commands, templates, and settings[/dim]\n"
    )


def show_examples() -> None:
    """Show usage examples."""
    console.print("[bold yellow]Examples:[/bold yellow]")
    console.print("  🚀 [bold]Getting Started (Interactive):[/bold]")
    console.print("    $ claude-setup init           # Interactive setup with guidance")
    console.print(
        "    $ claude-setup list           # Show available options with actions"
    )
    console.print(
        "    $ claude-setup add            # Interactive template/hooks/settings installation"
    )
    console.print()
    console.print("  ⚡ [bold]Power User (CLI-first):[/bold]")
    console.print("    $ claude-setup init --quick   # Quick setup with defaults")
    console.print("    $ claude-setup add template code-review")
    console.print("    $ claude-setup add hooks security/file-change-limiter")
    console.print('    $ claude-setup add permission "Bash(npm:*)"')
    console.print("    $ claude-setup update templates")
    console.print("    $ claude-setup hooks list     # View all available hooks")
    console.print("    $ claude-setup settings       # Interactive settings management")
    console.print()
    console.print(
        "  For more help: [link]https://github.com/jawhnycooke/claude-code-setup[/link]"
    )


def show_implementation_status(task: str, phase: str) -> None:
    """Show implementation status for commands not yet implemented."""
    console.print(
        f"\n[yellow]⚠️ This command will be fully implemented in {task}[/yellow]"
    )
    console.print(f"[dim]{phase}[/dim]")


@click.group(invoke_without_command=True)
@click.version_option(version=__version__)
@click.option(
    "--no-interactive",
    is_flag=True,
    help="Disable all interactive prompts (useful for scripts)",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug output",
)
@click.pass_context
def cli(ctx: click.Context, no_interactive: bool, debug: bool) -> None:
    """🤖 Setup and configure Claude Code commands, templates, and settings

    Interactive by default for beginners, with CLI flags for power users.

    Examples:
      🚀 Getting Started (Interactive):
        $ claude-setup init           # Interactive setup with guidance
        $ claude-setup list           # Show available options with actions
        $ claude-setup add            # Interactive template/hooks/settings installation

      ⚡ Power User (CLI-first):
        $ claude-setup init --quick   # Quick setup with defaults
        $ claude-setup add template code-review
        $ claude-setup add hooks security/file-change-limiter
        $ claude-setup add permission "Bash(npm:*)"
        $ claude-setup update templates
        $ claude-setup hooks list     # View all available hooks
        $ claude-setup settings       # Interactive settings management

      For more help: https://github.com/jawhnycooke/claude-code-setup
    """
    # Ensure context object exists for passing options to subcommands
    ctx.ensure_object(dict)
    ctx.obj["no_interactive"] = no_interactive
    ctx.obj["debug"] = debug

    # Update global context
    cli_context.no_interactive = no_interactive
    cli_context.debug = debug

    # If no command is provided, show welcome and examples
    if ctx.invoked_subcommand is None:
        show_welcome_banner()
        show_examples()

        if not no_interactive:
            console.print(
                "\n[dim]💡 Tip: Start with 'claude-setup init' for interactive setup[/dim]"
            )
            console.print(
                "[dim]Or run 'claude-setup --help' to see all available commands[/dim]"
            )


@cli.command()
@click.option("--quick", is_flag=True, help="Quick setup with defaults")
@click.option(
    "-f", "--force", is_flag=True, help="Force overwrite existing configuration"
)
@click.option("-d", "--dry-run", is_flag=True, help="Simulate without making changes")
@click.option(
    "--test-dir",
    type=click.Path(),
    help="Use test directory instead of current directory",
)
@click.option(
    "-g",
    "--global",
    "global_config",
    is_flag=True,
    help="Save configuration to global ~/.claude directory",
)
@click.option(
    "-p",
    "--permissions",
    default="python,node,git,shell,package-managers",
    help="Comma-separated list of permission sets to include",
)
@click.option(
    "--theme",
    default="default",
    help="Theme to use (default, dark)",
)
@click.option(
    "--no-check",
    is_flag=True,
    help="Skip checks for existing configuration",
)
@click.pass_context
def init(
    ctx: click.Context,
    quick: bool,
    force: bool,
    dry_run: bool,
    test_dir: Optional[str],
    global_config: bool,
    permissions: str,
    theme: str,
    no_check: bool,
) -> None:
    """Initialize Claude Code setup in your project or globally."""
    from .commands.init import run_init_command
    
    run_init_command(
        quick=quick,
        force=force,
        dry_run=dry_run,
        test_dir=test_dir,
        global_config=global_config,
        permissions=permissions,
        theme=theme,
        no_check=no_check,
        interactive=ctx.obj.get("no_interactive", False) == False,
    )


@cli.command()
@click.argument(
    "type", required=False, type=click.Choice(["templates", "hooks", "settings"])
)
@click.option(
    "-c", "--category", 
    help="Filter templates by category"
)
@click.option(
    "-i", "--installed", 
    is_flag=True, 
    help="Show only installed templates"
)
@click.option(
    "-t",
    "--test-dir",
    type=click.Path(),
    help="Use test directory instead of current directory",
)
@click.option(
    "-g",
    "--global",
    "global_config",
    is_flag=True,
    help="Use global ~/.claude directory",
)
@click.option(
    "--no-interactive", is_flag=True, help="Skip interactive prompts (show info only)"
)
@click.pass_context
def list(
    ctx: click.Context,
    type: Optional[str],
    category: Optional[str],
    installed: bool,
    test_dir: Optional[str],
    global_config: bool,
    no_interactive: bool,
) -> None:
    """📋 List templates, hooks, and settings with interactive options."""
    from .commands.list import run_list_command
    
    run_list_command(
        resource_type=type,
        category=category,
        installed=installed,
        test_dir=test_dir,
        global_config=global_config,
        interactive=not (no_interactive or ctx.obj.get("no_interactive", False)),
    )


@cli.command()
@click.argument(
    "type",
    required=False,
    type=click.Choice(["template", "hooks", "hook", "permission", "theme", "env"]),
)
@click.argument("value", required=False)
@click.argument("extra_value", required=False)
@click.option(
    "-t",
    "--test-dir",
    type=click.Path(),
    help="Use test directory instead of current directory",
)
@click.option(
    "-g",
    "--global",
    "global_config",
    is_flag=True,
    help="Use global ~/.claude directory",
)
@click.option("-f", "--force", is_flag=True, help="Force overwrite existing items")
@click.pass_context
def add(
    ctx: click.Context,
    type: Optional[str],
    value: Optional[str],
    extra_value: Optional[str],
    test_dir: Optional[str],
    global_config: bool,
    force: bool,
) -> None:
    """📦 Add templates, hooks, or settings with interactive selection."""
    # Load and execute the add command
    from .commands.add import run_add_command
    
    run_add_command(
        type_arg=type,
        value=value,
        extra_value=extra_value,
        test_dir=test_dir,
        global_config=global_config,
        force=force,
    )


@cli.command()
@click.argument("templates", nargs=-1)
@click.option(
    "--all",
    "-a",
    is_flag=True,
    help="Update all installed templates",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force update even if content is unchanged",
)
@click.option(
    "--test-dir",
    type=click.Path(path_type=Path),
    help="Use a test directory instead of the default",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be updated without making changes",
)
@click.option(
    "--settings",
    "-s",
    is_flag=True,
    help="Update settings file with latest defaults",
)
@click.option(
    "--global",
    "-g",
    "global_settings",
    is_flag=True,
    help="Update global settings",
)
@click.pass_context
def update(
    ctx: click.Context,
    templates: tuple,
    all: bool,
    force: bool,
    test_dir: Optional[Path],
    dry_run: bool,
    settings: bool,
    global_settings: bool,
) -> None:
    """🔄 Update templates or settings to their latest versions."""
    # Load and execute the update command
    from .commands.update import run_update_command
    
    run_update_command(
        ctx=ctx,
        templates=templates,
        all=all,
        force=force,
        test_dir=test_dir,
        dry_run=dry_run,
        settings=settings,
        global_settings=global_settings,
    )


@cli.command()
@click.argument("templates", nargs=-1)
@click.option(
    "--all",
    "-a",
    is_flag=True,
    help="Remove all installed templates (use with caution)",
)
@click.option(
    "--permission",
    "-p",
    help="Remove a specific permission from settings",
)
@click.option(
    "--test-dir",
    type=click.Path(path_type=Path),
    help="Use a test directory instead of the default",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be removed without making changes",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Skip confirmation prompts",
)
@click.pass_context
def remove(
    ctx: click.Context,
    templates: tuple,
    all: bool,
    permission: Optional[str],
    test_dir: Optional[Path],
    dry_run: bool,
    force: bool,
) -> None:
    """🗑️ Remove templates or permissions from your configuration."""
    # Load and execute the remove command
    from .commands.remove import run_remove_command
    
    run_remove_command(
        ctx=ctx,
        templates=templates,
        all=all,
        permission=permission,
        test_dir=test_dir,
        dry_run=dry_run,
        force=force,
    )


@cli.command()
@click.option(
    "--test-dir",
    type=click.Path(path_type=Path),
    help="Use a test directory instead of the default",
)
@click.pass_context
def interactive(ctx: click.Context, test_dir: Optional[Path]) -> None:
    """🎯 Interactive mode with guided workflows."""
    # Determine target directory
    if test_dir:
        target_dir = test_dir.resolve()
    else:
        target_dir = Path.home() / ".claude"
    
    # Run interactive mode
    from .commands.interactive import run_interactive_mode
    run_interactive_mode(ctx, target_dir)


@cli.group()
@click.pass_context
def hooks(ctx: click.Context) -> None:
    """🛡️ Manage security and automation hooks."""
    pass


@hooks.command("list")
@click.option(
    "-c", "--category", 
    help="Filter hooks by category (security, testing, aws)"
)
@click.option(
    "-e", "--event", 
    help="Filter hooks by event type (PreToolUse, PostToolUse, etc.)"
)
@click.option(
    "-i", "--installed", 
    is_flag=True, 
    help="Show only installed hooks"
)
@click.option(
    "-t",
    "--test-dir",
    type=click.Path(),
    help="Use test directory instead of current directory",
)
@click.option(
    "-g",
    "--global",
    "global_config",
    is_flag=True,
    help="Use global ~/.claude directory",
)
@click.option(
    "--no-interactive", is_flag=True, help="Skip interactive prompts"
)
@click.pass_context
def hooks_list(
    ctx: click.Context, 
    category: Optional[str],
    event: Optional[str],
    installed: bool,
    test_dir: Optional[str],
    global_config: bool,
    no_interactive: bool,
) -> None:
    """List all available hooks with filtering options."""
    from .commands.hooks import run_hooks_list_command
    
    run_hooks_list_command(
        category=category,
        event=event,
        installed=installed,
        test_dir=test_dir,
        global_config=global_config,
        interactive=not (no_interactive or ctx.obj.get("no_interactive", False)),
    )


@hooks.command("add")
@click.argument("hook_names", nargs=-1)
@click.option(
    "-t",
    "--test-dir",
    type=click.Path(),
    help="Use test directory instead of current directory",
)
@click.option(
    "-g",
    "--global",
    "global_config",
    is_flag=True,
    help="Use global ~/.claude directory",
)
@click.option("-f", "--force", is_flag=True, help="Force overwrite existing hooks")
@click.option("-d", "--dry-run", is_flag=True, help="Simulate installation without making changes")
@click.pass_context
def hooks_add(
    ctx: click.Context,
    hook_names: tuple[str, ...],
    test_dir: Optional[str],
    global_config: bool,
    force: bool,
    dry_run: bool,
) -> None:
    """Add security and automation hooks."""
    from .commands.hooks import run_hooks_add_command
    
    run_hooks_add_command(
        hook_names=hook_names,
        test_dir=test_dir,
        global_config=global_config,
        force=force,
        interactive=not ctx.obj.get("no_interactive", False),
        dry_run=dry_run,
    )


@hooks.command("remove")
@click.argument("hook_names", nargs=-1)
@click.option(
    "--all",
    "-a",
    is_flag=True,
    help="Remove all installed hooks (use with caution)",
)
@click.option(
    "-t",
    "--test-dir",
    type=click.Path(),
    help="Use test directory instead of current directory",
)
@click.option(
    "-g",
    "--global",
    "global_config",
    is_flag=True,
    help="Use global ~/.claude directory",
)
@click.option("-f", "--force", is_flag=True, help="Force removal without confirmation")
@click.option("-d", "--dry-run", is_flag=True, help="Simulate removal without making changes")
@click.pass_context
def hooks_remove(
    ctx: click.Context,
    hook_names: tuple[str, ...],
    all: bool,
    test_dir: Optional[str],
    global_config: bool,
    force: bool,
    dry_run: bool,
) -> None:
    """Remove installed hooks."""
    from .commands.hooks import run_hooks_remove_command
    
    run_hooks_remove_command(
        hook_names=hook_names,
        all_hooks=all,
        test_dir=test_dir,
        global_config=global_config,
        force=force,
        interactive=not ctx.obj.get("no_interactive", False),
        dry_run=dry_run,
    )


@cli.command()
@click.argument(
    "action",
    required=False,
    type=click.Choice(["show", "theme", "env", "permissions"]),
)
@click.option(
    "-t",
    "--test-dir",
    type=click.Path(),
    help="Use test directory instead of current directory",
)
@click.option(
    "-g",
    "--global",
    "global_config",
    is_flag=True,
    help="Use global ~/.claude directory",
)
@click.option(
    "--no-interactive", is_flag=True, help="Skip interactive prompts"
)
@click.pass_context
def settings(
    ctx: click.Context,
    action: Optional[str],
    test_dir: Optional[str],
    global_config: bool,
    no_interactive: bool,
) -> None:
    """⚙️ Manage Claude Code settings and configuration."""
    from .commands.settings import run_settings_command
    
    run_settings_command(
        action=action,
        test_dir=test_dir,
        global_config=global_config,
        interactive=not (no_interactive or ctx.obj.get("no_interactive", False)),
    )


@cli.group()
@click.pass_context
def plugins(ctx: click.Context) -> None:
    """🔌 Manage Claude Code Setup plugins."""
    pass


@plugins.command("list")
@click.option(
    "--status",
    type=click.Choice(["all", "available", "installed", "active"]),
    default="all",
    help="Filter plugins by status",
)
@click.option(
    "-t",
    "--test-dir",
    type=click.Path(),
    help="Use test directory instead of current directory",
)
@click.option(
    "--no-interactive", is_flag=True, help="Non-interactive mode"
)
@click.pass_context
def plugins_list(
    ctx: click.Context,
    status: str,
    test_dir: Optional[str],
    no_interactive: bool,
) -> None:
    """List available and installed plugins."""
    from .commands.plugins import plugins_group
    
    # Create a new context for the plugins group with test_dir
    plugins_ctx = plugins_group.make_context(
        'plugins', 
        ['--test-dir', test_dir] if test_dir else [],
        parent=ctx
    )
    
    # Now invoke the list command
    with plugins_ctx:
        list_cmd = plugins_group.commands['list']
        list_cmd.invoke(click.Context(
            list_cmd,
            parent=plugins_ctx,
            info_name='list',
            obj=plugins_ctx.obj
        ), status=status, no_interactive=no_interactive)


@plugins.command("add")
@click.argument("plugin_name", required=False)
@click.option(
    "--from-file",
    type=click.Path(exists=True),
    help="Install plugin from a file or directory",
)
@click.option(
    "--activate",
    is_flag=True,
    help="Activate plugin after installation",
)
@click.option(
    "-t",
    "--test-dir",
    type=click.Path(),
    help="Use test directory instead of current directory",
)
@click.pass_context
def plugins_add(
    ctx: click.Context,
    plugin_name: Optional[str],
    from_file: Optional[str],
    activate: bool,
    test_dir: Optional[str],
) -> None:
    """Install a plugin."""
    from .commands.plugins import plugins_group, add_plugin
    
    # Create a new context for the plugins group with test_dir
    plugins_ctx = plugins_group.make_context(
        'plugins', 
        ['--test-dir', test_dir] if test_dir else [],
        parent=ctx
    )
    
    # Now invoke the add command
    with plugins_ctx:
        add_plugin.invoke(click.Context(
            add_plugin,
            parent=plugins_ctx,
            info_name='add',
            obj=plugins_ctx.obj
        ), plugin_name=plugin_name, from_file=Path(from_file) if from_file else None, activate=activate)


@plugins.command("remove")
@click.argument("plugin_name", required=False)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force removal even if other plugins depend on it",
)
@click.option(
    "-t",
    "--test-dir",
    type=click.Path(),
    help="Use test directory instead of current directory",
)
@click.pass_context
def plugins_remove(
    ctx: click.Context,
    plugin_name: Optional[str],
    force: bool,
    test_dir: Optional[str],
) -> None:
    """Remove an installed plugin."""
    from .commands.plugins import plugins_group, remove_plugin
    
    # Create a new context for the plugins group with test_dir
    plugins_ctx = plugins_group.make_context(
        'plugins', 
        ['--test-dir', test_dir] if test_dir else [],
        parent=ctx
    )
    
    # Now invoke the remove command
    with plugins_ctx:
        remove_plugin.invoke(click.Context(
            remove_plugin,
            parent=plugins_ctx,
            info_name='remove',
            obj=plugins_ctx.obj
        ), plugin_name=plugin_name, force=force)


@plugins.command("info")
@click.argument("plugin_name")
@click.option(
    "-t",
    "--test-dir",
    type=click.Path(),
    help="Use test directory instead of current directory",
)
@click.pass_context
def plugins_info(
    ctx: click.Context,
    plugin_name: str,
    test_dir: Optional[str],
) -> None:
    """Show detailed information about a plugin."""
    from .commands.plugins import plugins_group, plugin_info
    
    # Create a new context for the plugins group with test_dir
    plugins_ctx = plugins_group.make_context(
        'plugins', 
        ['--test-dir', test_dir] if test_dir else [],
        parent=ctx
    )
    
    # Now invoke the info command
    with plugins_ctx:
        plugin_info.invoke(click.Context(
            plugin_info,
            parent=plugins_ctx,
            info_name='info',
            obj=plugins_ctx.obj
        ), plugin_name=plugin_name)


def load_commands() -> None:
    """Load all core commands and extensions into the registry."""
    try:
        # Load core commands
        loader.load_core_commands()
        
        # Load user extensions
        ext_count = extension_manager.discover_user_extensions()
        if ext_count > 0:
            console.print(f"[dim]✓ Loaded {ext_count} user extensions[/dim]")
        
        # Validate core commands
        if loader.validate_commands():
            console.print("[dim]✓ Command registration system initialized[/dim]")
    except Exception as e:
        console.print(f"[yellow]Warning: Command loading failed: {e}[/yellow]")


def main() -> None:
    """Main entry point for the CLI application."""
    try:
        # Load commands before running CLI
        load_commands()
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
