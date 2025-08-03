"""Hooks command implementation for claude-code-setup.

This module implements the hooks commands which allow users to manage
security and automation hooks in their Claude Code configuration.
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel

# UI components
from ..ui.prompts import (
    MultiSelectPrompt,
    ConfirmationDialog,
    ValidatedPrompt,
)
from ..ui.progress import (
    MultiStepProgress,
    ProgressStep,
    StepStatus,
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
    CLAUDE_HOME,
)
from ..utils.hook import (
    get_all_hooks_sync,
    get_hook_sync,
    get_hooks_by_category,
    get_hooks_by_event,
    get_hook_categories,
)
from ..utils.hook_installer import (
    HookInstaller,
    create_hook_installer,
    install_hook_simple,
)
from ..utils.fs import ensure_claude_directories, ensure_claude_directories_sync
from ..utils.settings import get_settings, save_settings
from ..types import Hook, HookEvent


def run_hooks_list_command(
    category: Optional[str] = None,
    event: Optional[str] = None,
    installed: bool = False,
    test_dir: Optional[str] = None,
    global_config: bool = False,
    interactive: bool = True,
) -> None:
    """Run the hooks list command.
    
    Args:
        category: Filter hooks by category
        event: Filter hooks by event type
        installed: Show only installed hooks
        test_dir: Use test directory instead of current directory
        global_config: Use global ~/.claude directory
        interactive: Enable interactive prompts
    """
    try:
        # Determine target directory
        if test_dir:
            test_path = Path(test_dir).resolve()
            # If test_dir already ends with .claude, use it directly, otherwise append .claude
            if test_path.name == ".claude":
                target_dir = test_path
            else:
                target_dir = test_path / ".claude"
        elif global_config:
            target_dir = Path.home() / ".claude"
        else:
            target_dir = Path.cwd() / ".claude"
        
        # Get all hooks
        registry = get_all_hooks_sync()
        hooks_list = list(registry.hooks.values())
        
        if not hooks_list:
            console.print("[yellow]⚠️ No hooks found in registry[/yellow]")
            return
        
        # Apply filters
        if category:
            hooks_list = [h for h in hooks_list if h.category.lower() == category.lower()]
            if not hooks_list:
                console.print(f"[yellow]⚠️ No hooks found in category '{category}'[/yellow]")
                return
        
        if event:
            try:
                event_filter = HookEvent(event) if isinstance(event, str) else event
                hooks_list = [h for h in hooks_list if h.event == event_filter]
            except ValueError:
                console.print(f"[red]❌ Invalid event type: {event}[/red]")
                return
            
            if not hooks_list:
                console.print(f"[yellow]⚠️ No hooks found for event '{event}'[/yellow]")
                return
        
        # Check installation status if requested
        installed_hooks = set()
        if installed:
            hooks_dir = target_dir / "hooks"
            if hooks_dir.exists():
                for category_dir in hooks_dir.iterdir():
                    if category_dir.is_dir():
                        for hook_dir in category_dir.iterdir():
                            if hook_dir.is_dir():
                                installed_hooks.add(hook_dir.name)
            
            hooks_list = [h for h in hooks_list if h.name in installed_hooks]
            if not hooks_list:
                console.print("[yellow]⚠️ No installed hooks found[/yellow]")
                return
        
        # Display hooks
        _display_hooks_list(hooks_list, target_dir, interactive)
        
    except Exception as e:
        console.print(create_command_error("Failed to list hooks", str(e)))
        sys.exit(1)


def run_hooks_add_command(
    hook_names: Tuple[str, ...],
    test_dir: Optional[str] = None,
    global_config: bool = False,
    force: bool = False,
    interactive: bool = True,
    dry_run: bool = False,
) -> None:
    """Run the hooks add command.
    
    Args:
        hook_names: Names of hooks to install
        test_dir: Use test directory instead of current directory
        global_config: Use global ~/.claude directory
        force: Force overwrite existing hooks
        interactive: Enable interactive prompts
        dry_run: Simulate installation without making changes
    """
    try:
        # Determine target directory
        if test_dir:
            test_path = Path(test_dir).resolve()
            # If test_dir already ends with .claude, use it directly, otherwise append .claude
            if test_path.name == ".claude":
                target_dir = test_path
            else:
                target_dir = test_path / ".claude"
        elif global_config:
            target_dir = Path.home() / ".claude"
        else:
            target_dir = Path.cwd() / ".claude"
        
        # Ensure target directory exists
        ensure_claude_directories_sync(target_dir)
        
        # Get available hooks
        registry = get_all_hooks_sync()
        
        # Determine hooks to install
        hooks_to_install = []
        
        if hook_names:
            # Validate provided hook names
            for hook_name in hook_names:
                hook = get_hook_sync(hook_name)
                if hook:
                    hooks_to_install.append(hook_name)
                else:
                    console.print(f"[red]❌ Hook '{hook_name}' not found[/red]")
                    return
        elif interactive:
            # Interactive hook selection
            hooks_to_install = _interactive_hook_selection(registry)
            if not hooks_to_install:
                console.print("[yellow]Operation cancelled by user[/yellow]")
                return
        else:
            console.print("[red]❌ No hooks specified. Use --help for usage.[/red]")
            return
        
        # Install hooks
        installer = HookInstaller(
            target_dir=target_dir,
            dry_run=dry_run,
            force=force,
            backup=True,
            validate_dependencies=True,
        )
        
        report = installer.install_hooks(hooks_to_install)
        
        # Display results
        _display_installation_results(report, dry_run)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(create_command_error("Failed to add hooks", str(e)))
        sys.exit(1)


def run_hooks_remove_command(
    hook_names: Tuple[str, ...],
    all_hooks: bool = False,
    test_dir: Optional[str] = None,
    global_config: bool = False,
    force: bool = False,
    interactive: bool = True,
    dry_run: bool = False,
) -> None:
    """Run the hooks remove command.
    
    Args:
        hook_names: Names of hooks to remove
        all_hooks: Remove all installed hooks
        test_dir: Use test directory instead of current directory
        global_config: Use global ~/.claude directory
        force: Force removal without confirmation
        interactive: Enable interactive prompts
        dry_run: Simulate removal without making changes
    """
    try:
        # Determine target directory
        if test_dir:
            test_path = Path(test_dir).resolve()
            # If test_dir already ends with .claude, use it directly, otherwise append .claude
            if test_path.name == ".claude":
                target_dir = test_path
            else:
                target_dir = test_path / ".claude"
        elif global_config:
            target_dir = Path.home() / ".claude"
        else:
            target_dir = Path.cwd() / ".claude"
        
        # Get installed hooks
        installed_hooks = _get_installed_hooks(target_dir)
        
        if not installed_hooks:
            console.print("[yellow]⚠️ No hooks are currently installed[/yellow]")
            return
        
        # Determine hooks to remove
        hooks_to_remove = []
        
        if all_hooks:
            hooks_to_remove = list(installed_hooks.keys())
            if not force and interactive:
                confirm = ConfirmationDialog(
                    "Remove all installed hooks?",
                    "This will permanently remove all hook files.",
                    danger=True
                )
                if not confirm.ask():
                    console.print("[yellow]Operation cancelled by user[/yellow]")
                    return
        elif hook_names:
            # Validate provided hook names
            for hook_name in hook_names:
                if hook_name in installed_hooks:
                    hooks_to_remove.append(hook_name)
                else:
                    console.print(f"[yellow]⚠️ Hook '{hook_name}' is not installed[/yellow]")
            
            if not hooks_to_remove:
                return
        elif interactive:
            # Interactive hook selection
            hooks_to_remove = _interactive_remove_selection(installed_hooks)
            if not hooks_to_remove:
                console.print("[yellow]Operation cancelled by user[/yellow]")
                return
        else:
            console.print("[red]❌ No hooks specified. Use --help for usage.[/red]")
            return
        
        # Confirm removal if not forced
        if not force and interactive and not all_hooks:
            hook_list = ', '.join(hooks_to_remove)
            confirm = ConfirmationDialog(
                f"Remove {len(hooks_to_remove)} hook(s)?",
                f"This will permanently remove: {hook_list}",
                danger=True
            )
            if not confirm.ask():
                console.print("[yellow]Operation cancelled by user[/yellow]")
                return
        
        # Remove hooks
        installer = HookInstaller(
            target_dir=target_dir,
            dry_run=dry_run,
            backup=True,
        )
        
        removed_count = 0
        failed_count = 0
        
        for hook_name in hooks_to_remove:
            result = installer.uninstall_hook(hook_name)
            if result.success:
                removed_count += 1
                if not dry_run:
                    success(f"Removed hook: {hook_name}")
            else:
                failed_count += 1
                error(f"Failed to remove hook '{hook_name}': {result.message}")
        
        # Display summary
        if dry_run:
            console.print(f"\n[dim]🔍 Dry run: Would remove {removed_count} hooks[/dim]")
        else:
            if removed_count > 0:
                console.print(f"\n[green]✅ Successfully removed {removed_count} hooks[/green]")
            if failed_count > 0:
                console.print(f"[red]❌ Failed to remove {failed_count} hooks[/red]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(create_command_error("Failed to remove hooks", str(e)))
        sys.exit(1)


def _display_hooks_list(hooks_list: List[Hook], target_dir: Path, interactive: bool) -> None:
    """Display the list of hooks in a formatted table."""
    # Group hooks by category
    categories = {}
    for hook in hooks_list:
        if hook.category not in categories:
            categories[hook.category] = []
        categories[hook.category].append(hook)
    
    # Get installed hooks for status
    installed_hooks = _get_installed_hooks(target_dir)
    
    console.print("\n🛡️ [bold cyan]Available Hooks[/bold cyan]")
    
    for category, hooks in sorted(categories.items()):
        # Create table for category
        table = Table(title=f"{category.title()} Hooks", box=BOX_STYLES["minimal"])
        table.add_column("Name", style="bold")
        table.add_column("Event", style="cyan")
        table.add_column("Matcher", style="dim")
        table.add_column("Status", style="green")
        table.add_column("Description")
        
        for hook in sorted(hooks, key=lambda h: h.name):
            # Check installation status
            status = "✅ Installed" if hook.name in installed_hooks else "⬜ Available"
            status_style = "green" if hook.name in installed_hooks else "dim"
            
            # Format matcher
            matcher = hook.matcher if hook.matcher else "Any"
            if len(matcher) > 20:
                matcher = matcher[:17] + "..."
            
            # Format description
            description = hook.description
            if len(description) > 50:
                description = description[:47] + "..."
            
            table.add_row(
                hook.name,
                hook.event.value,
                matcher,
                f"[{status_style}]{status}[/{status_style}]",
                description
            )
        
        console.print(table)
        console.print()
    
    # Show summary
    total_hooks = len(hooks_list)
    installed_count = sum(1 for h in hooks_list if h.name in installed_hooks)
    
    console.print(f"[dim]📊 Total: {total_hooks} hooks, {installed_count} installed[/dim]")
    
    if interactive and not installed_hooks:
        console.print("\n[dim]💡 Tip: Use 'claude-setup hooks add' to install hooks[/dim]")


def _interactive_hook_selection(registry) -> List[str]:
    """Interactive hook selection using MultiSelectPrompt."""
    # Group hooks by category for better organization
    categories = get_hook_categories()
    
    choices = []
    for category, description in categories.items():
        category_hooks = get_hooks_by_category(category)
        if category_hooks:
            choices.append(f"[bold cyan]━━━ {category.title()} ({description}) ━━━[/bold cyan]")
            for hook in sorted(category_hooks, key=lambda h: h.name):
                status = f"[dim]{hook.event.value}[/dim]"
                choices.append({
                    "name": f"{hook.name} - {hook.description}",
                    "value": hook.name,
                    "description": f"{status} | {hook.matcher or 'Any'}"
                })
    
    if not choices:
        console.print("[yellow]⚠️ No hooks available[/yellow]")
        return []
    
    prompt = MultiSelectPrompt(
        message="Select hooks to install:",
        choices=choices,
        min_selection=1,
        max_selection=None,
    )
    
    try:
        return prompt.ask()
    except KeyboardInterrupt:
        return []


def _interactive_remove_selection(installed_hooks: Dict[str, Dict]) -> List[str]:
    """Interactive hook removal selection."""
    choices = []
    
    for hook_name, hook_info in sorted(installed_hooks.items()):
        category = hook_info.get('category', 'unknown')
        description = hook_info.get('description', 'No description')
        choices.append({
            "name": f"{hook_name} ({category})",
            "value": hook_name,
            "description": description
        })
    
    if not choices:
        return []
    
    prompt = MultiSelectPrompt(
        message="Select hooks to remove:",
        choices=choices,
        min_selection=1,
        max_selection=None,
    )
    
    try:
        return prompt.ask()
    except KeyboardInterrupt:
        return []


def _get_installed_hooks(target_dir: Path) -> Dict[str, Dict]:
    """Get information about installed hooks."""
    installed_hooks = {}
    hooks_dir = target_dir / "hooks"
    
    if not hooks_dir.exists():
        return installed_hooks
    
    for category_dir in hooks_dir.iterdir():
        if not category_dir.is_dir():
            continue
        
        for hook_dir in category_dir.iterdir():
            if not hook_dir.is_dir():
                continue
            
            hook_name = hook_dir.name
            metadata_file = hook_dir / "metadata.json"
            
            hook_info = {
                'category': category_dir.name,
                'path': hook_dir,
                'description': 'No description available'
            }
            
            # Try to read metadata
            if metadata_file.exists():
                try:
                    import json
                    with metadata_file.open('r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        hook_info['description'] = metadata.get('description', hook_info['description'])
                        hook_info['event'] = metadata.get('event')
                        hook_info['matcher'] = metadata.get('matcher')
                except Exception:
                    pass  # Use default info if metadata can't be read
            
            installed_hooks[hook_name] = hook_info
    
    return installed_hooks


def _display_installation_results(report, dry_run: bool = False) -> None:
    """Display the results of hook installation."""
    prefix = "🔍 Dry run: Would install" if dry_run else "📦 Installation Summary"
    
    if report.successful_installs > 0:
        console.print(f"\n[green]✅ {prefix}: {report.successful_installs} hooks[/green]")
        
        # Show successful installations
        for result in report.results:
            if result.success:
                status = "would install" if dry_run else "installed"
                success(f"Hook '{result.hook_name}' {status} successfully")
    
    if report.failed_installs > 0:
        console.print(f"\n[red]❌ Failed: {report.failed_installs} hooks[/red]")
        
        # Show failures
        for result in report.results:
            if not result.success:
                error(f"Hook '{result.hook_name}': {result.message}")
    
    if report.skipped_installs > 0:
        console.print(f"\n[yellow]⏭️ Skipped: {report.skipped_installs} hooks (already exist)[/yellow]")
    
    # Show performance info
    if report.duration > 0:
        console.print(f"\n[dim]⏱️ Completed in {report.duration:.1f}s[/dim]")