"""Remove command implementation for claude-code-setup."""

import os
from pathlib import Path
from typing import List, Optional, Tuple

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..core.registry import register_command
from ..utils.fs import template_exists_sync, ensure_claude_directories_sync
from ..utils.logger import error, info, success, warning
from ..utils.settings import read_settings_sync, save_settings_sync
from ..utils.hook_installer import create_hook_installer
from ..ui.prompts import MultiSelectPrompt, ConfirmationDialog
from ..ui.progress import MultiStepProgress, ProgressStep
from ..ui.styles import create_error_banner, create_panel

console = Console()


def find_installed_templates_for_removal(target_dir: Path) -> List[Tuple[str, str, Path]]:
    """Find all installed templates that can be removed.
    
    Args:
        target_dir: Target directory to scan
        
    Returns:
        List of tuples (template_name, category, file_path)
    """
    installed = []
    commands_dir = target_dir / "commands"
    
    if not commands_dir.exists():
        return installed
        
    # Scan all category directories
    for category_dir in commands_dir.iterdir():
        if not category_dir.is_dir():
            continue
            
        category = category_dir.name
        
        # Find all template files
        for template_file in category_dir.glob("*.md"):
            template_name = template_file.stem
            installed.append((template_name, category, template_file))
            
    return installed


def find_installed_hooks_for_removal(target_dir: Path) -> List[Tuple[str, str, Path]]:
    """Find all installed hooks that can be removed.
    
    Args:
        target_dir: Target directory to scan
        
    Returns:
        List of tuples (hook_name, category, directory_path)
    """
    installed = []
    hooks_dir = target_dir / "hooks"
    
    if not hooks_dir.exists():
        return installed
        
    # Scan all category directories
    for category_dir in hooks_dir.iterdir():
        if not category_dir.is_dir():
            continue
            
        category = category_dir.name
        
        # Find all hook directories
        for hook_dir in category_dir.iterdir():
            if not hook_dir.is_dir():
                continue
                
            hook_name = hook_dir.name
            # Check if it has metadata.json to confirm it's a hook
            if (hook_dir / "metadata.json").exists():
                installed.append((hook_name, category, hook_dir))
            
    return installed


def remove_template_file(template_path: Path, dry_run: bool = False) -> bool:
    """Remove a template file from the filesystem.
    
    Args:
        template_path: Path to the template file
        dry_run: Whether to perform a dry run
        
    Returns:
        True if removal was successful
    """
    try:
        if dry_run:
            info(f"[DRY RUN] Would remove: {template_path}")
            return True
            
        if template_path.exists():
            template_path.unlink()
            success(f"Removed template: {template_path.name}")
            
            # Remove empty category directory
            category_dir = template_path.parent
            if category_dir.is_dir() and not list(category_dir.iterdir()):
                category_dir.rmdir()
                info(f"Removed empty category directory: {category_dir.name}")
                
            return True
        else:
            warning(f"Template file not found: {template_path}")
            return False
            
    except Exception as e:
        error(f"Failed to remove template: {e}")
        return False


def remove_templates_batch(
    templates: List[Tuple[str, str, Path]],
    dry_run: bool = False,
) -> Tuple[List[str], List[str]]:
    """Remove multiple templates in batch.
    
    Args:
        templates: List of (template_name, category, file_path) tuples
        dry_run: Whether to perform a dry run
        
    Returns:
        Tuple of (successes, errors)
    """
    successes = []
    errors = []
    
    for template_name, category, file_path in templates:
        try:
            if remove_template_file(file_path, dry_run):
                successes.append(f"{template_name} ({category})")
            else:
                errors.append(f"{template_name} ({category}): File not found")
                
        except Exception as e:
            errors.append(f"{template_name} ({category}): {str(e)}")
            
    return successes, errors


def remove_permission_from_settings(
    permission: str,
    target_dir: Path,
    dry_run: bool = False,
) -> bool:
    """Remove a permission from settings file.
    
    Args:
        permission: Permission to remove
        target_dir: Target directory containing settings
        dry_run: Whether to perform a dry run
        
    Returns:
        True if permission was removed successfully
    """
    try:
        settings_path = target_dir / "settings.json"
        
        # Read raw settings to handle both formats
        if not settings_path.exists():
            warning("No settings file found")
            return False
            
        import json
        with open(settings_path) as f:
            settings_dict = json.load(f)
            
        # Check for permissions in different formats
        allowed_tools = []
        permission_found = False
        
        # Check TypeScript format (flat array)
        if "allowedTools" in settings_dict:
            allowed_tools = settings_dict.get("allowedTools", [])
            if permission in allowed_tools:
                permission_found = True
                allowed_tools.remove(permission)
                settings_dict["allowedTools"] = allowed_tools
                
        # Check Python format (nested permissions.allow)
        elif "permissions" in settings_dict and "allow" in settings_dict["permissions"]:
            allowed_tools = settings_dict["permissions"]["allow"]
            if permission in allowed_tools:
                permission_found = True
                allowed_tools.remove(permission)
                settings_dict["permissions"]["allow"] = allowed_tools
                
        if not permission_found:
            warning(f"Permission not found: {permission}")
            return False
            
        if dry_run:
            info(f"[DRY RUN] Would remove permission: {permission}")
            return True
            
        # Save updated settings
        with open(settings_path, 'w') as f:
            json.dump(settings_dict, f, indent=2)
            
        success(f"Removed permission: {permission}")
        return True
        
    except Exception as e:
        error(f"Failed to remove permission: {e}")
        return False


def show_removal_selection(
    installed: List[Tuple[str, str, Path]]
) -> Optional[List[Tuple[str, str, Path]]]:
    """Show interactive template selection for removal.
    
    Args:
        installed: List of installed templates
        
    Returns:
        Selected templates or None if cancelled
    """
    # Group by category
    by_category = {}
    for name, category, path in installed:
        if category not in by_category:
            by_category[category] = []
        by_category[category].append((name, path))
    
    # Create choices
    choices = []
    choice_map = {}
    
    for category in sorted(by_category.keys()):
        choices.append(f"[dim]{category.upper()}[/dim]")
        for name, path in sorted(by_category[category]):
            choice_key = f"  {name}"
            choices.append(choice_key)
            choice_map[choice_key] = (name, category, path)
    
    prompt = MultiSelectPrompt(
        "Select templates to remove:",
        choices=choices,
        default_selected=[],  # Don't select anything by default
    )
    
    selected = prompt.ask()
    if not selected:
        return None
        
    # Parse selected templates
    result = []
    for item in selected:
        if item.startswith("  "):
            if item in choice_map:
                result.append(choice_map[item])
                
    return result


def handle_template_removal(
    installed: List[Tuple[str, str, Path]],
    items: Tuple[str, ...],
    all: bool,
    force: bool,
    dry_run: bool
) -> List[Tuple[str, str, Path]]:
    """Handle template removal logic."""
    items_to_remove = []
    
    if all:
        # Remove all items
        items_to_remove = installed
        
    elif items:
        # Remove specific items
        item_set = set(items)
        for name, category, path in installed:
            if name in item_set:
                items_to_remove.append((name, category, path))
                
        # Check for items that weren't found
        found_names = {t[0] for t in items_to_remove}
        not_found = item_set - found_names
        if not_found:
            console.print(
                create_error_banner(
                    "Templates Not Found",
                    f"The following templates are not installed: {', '.join(not_found)}"
                )
            )
            
    else:
        # Interactive selection
        selected = show_removal_selection(installed)
        if not selected:
            console.print("[yellow]Removal cancelled.[/yellow]")
            return []
        items_to_remove = selected
        
    if not items_to_remove:
        console.print("[yellow]No templates selected for removal.[/yellow]")
        return []
        
    # Confirm removal (unless --force or --dry-run)
    if not force and not dry_run:
        # Create confirmation message
        item_list = "\n".join(
            f"  • {name} ({category})" 
            for name, category, _ in items_to_remove
        )
        
        confirm = ConfirmationDialog(
            title="Confirm Removal",
            message=f"Are you sure you want to remove {len(items_to_remove)} template(s)?",
            details={"Templates": item_list},
            default=False,
            danger=True,
        )
        
        if not confirm.ask():
            console.print("[yellow]Removal cancelled.[/yellow]")
            return []
            
    # Perform removal with progress tracking
    perform_template_removal(items_to_remove, dry_run)
    return items_to_remove


def handle_hook_removal(
    installed: List[Tuple[str, str, Path]],
    items: Tuple[str, ...],
    all: bool,
    force: bool,
    dry_run: bool,
    target_dir: Path
) -> List[Tuple[str, str, Path]]:
    """Handle hook removal logic."""
    items_to_remove = []
    
    if all:
        # Remove all items
        items_to_remove = installed
        
    elif items:
        # Remove specific items
        item_set = set(items)
        for name, category, path in installed:
            if name in item_set:
                items_to_remove.append((name, category, path))
                
        # Check for items that weren't found
        found_names = {t[0] for t in items_to_remove}
        not_found = item_set - found_names
        if not_found:
            console.print(
                create_error_banner(
                    "Hooks Not Found",
                    f"The following hooks are not installed: {', '.join(not_found)}"
                )
            )
            
    else:
        # Interactive selection
        selected = show_hook_removal_selection(installed)
        if not selected:
            console.print("[yellow]Removal cancelled.[/yellow]")
            return []
        items_to_remove = selected
        
    if not items_to_remove:
        console.print("[yellow]No hooks selected for removal.[/yellow]")
        return []
        
    # Confirm removal (unless --force or --dry-run)
    if not force and not dry_run:
        # Create confirmation message
        item_list = "\n".join(
            f"  • {name} ({category})" 
            for name, category, _ in items_to_remove
        )
        
        confirm = ConfirmationDialog(
            title="Confirm Removal",
            message=f"Are you sure you want to remove {len(items_to_remove)} hook(s)?",
            details={"Hooks": item_list},
            default=False,
            danger=True,
        )
        
        if not confirm.ask():
            console.print("[yellow]Removal cancelled.[/yellow]")
            return []
            
    # Perform removal with progress tracking
    perform_hook_removal(items_to_remove, target_dir, dry_run)
    return items_to_remove


def show_hook_removal_selection(
    installed: List[Tuple[str, str, Path]]
) -> Optional[List[Tuple[str, str, Path]]]:
    """Show interactive hook selection for removal."""
    # Group by category
    by_category = {}
    for name, category, path in installed:
        if category not in by_category:
            by_category[category] = []
        by_category[category].append((name, path))
    
    # Create choices
    choices = []
    choice_map = {}
    
    for category in sorted(by_category.keys()):
        choices.append(f"[dim]{category.upper()}[/dim]")
        for name, path in sorted(by_category[category]):
            choice_key = f"  {name}"
            choices.append(choice_key)
            choice_map[choice_key] = (name, category, path)
    
    prompt = MultiSelectPrompt(
        "Select hooks to remove:",
        choices=choices,
        default_selected=[],  # Don't select anything by default
    )
    
    selected = prompt.ask()
    if not selected:
        return None
        
    # Parse selected hooks
    result = []
    for item in selected:
        if item.startswith("  "):
            if item in choice_map:
                result.append(choice_map[item])
                
    return result


def perform_template_removal(items_to_remove: List[Tuple[str, str, Path]], dry_run: bool):
    """Perform template removal with progress tracking."""
    # Create progress steps
    steps = [
        ProgressStep(f"remove_{i}", f"Remove {name} from {cat}")
        for i, (name, cat, _) in enumerate(items_to_remove)
    ]
    
    # Create multi-step progress
    progress = MultiStepProgress(
        title=f"🗑️  Removing {len(items_to_remove)} Template(s)",
        steps=steps,
        console_obj=console,
    )
    
    # Perform removal with progress tracking
    with progress.live_display() as (live, update):
        successes = []
        errors = []
        
        for i, (item_name, category, file_path) in enumerate(items_to_remove):
            step_id = f"remove_{i}"
            progress.start_step(step_id)
            update()
            
            try:
                if remove_template_file(file_path, dry_run):
                    successes.append(f"{item_name} ({category})")
                    progress.complete_step(step_id, success=True)
                else:
                    errors.append(f"{item_name} ({category}): File not found")
                    progress.complete_step(step_id, success=False)
                    
            except Exception as e:
                errors.append(f"{item_name} ({category}): {str(e)}")
                progress.complete_step(step_id, success=False)
            
            update()
        
        show_removal_summary(successes, errors, "template")


def perform_hook_removal(items_to_remove: List[Tuple[str, str, Path]], target_dir: Path, dry_run: bool):
    """Perform hook removal with progress tracking."""
    # Create hook installer for removal
    installer = create_hook_installer(
        target_dir=target_dir,
        dry_run=dry_run,
        force=True,  # Force removal
        backup=True,
        validate_dependencies=False  # Skip validation on removal
    )
    
    # Create progress steps
    steps = [
        ProgressStep(f"remove_{i}", f"Remove {name} from {cat}")
        for i, (name, cat, _) in enumerate(items_to_remove)
    ]
    
    # Create multi-step progress
    progress = MultiStepProgress(
        title=f"🗑️  Removing {len(items_to_remove)} Hook(s)",
        steps=steps,
        console_obj=console,
    )
    
    # Perform removal with progress tracking
    with progress.live_display() as (live, update):
        successes = []
        errors = []
        
        for i, (hook_name, category, hook_path) in enumerate(items_to_remove):
            step_id = f"remove_{i}"
            progress.start_step(step_id)
            update()
            
            try:
                result = installer.uninstall_hook(hook_name)
                if result.success:
                    successes.append(f"{hook_name} ({category})")
                    progress.complete_step(step_id, success=True)
                else:
                    errors.append(f"{hook_name} ({category}): {result.message}")
                    progress.complete_step(step_id, success=False)
                    
            except Exception as e:
                errors.append(f"{hook_name} ({category}): {str(e)}")
                progress.complete_step(step_id, success=False)
            
            update()
        
        show_removal_summary(successes, errors, "hook")


def show_removal_summary(successes: List[str], errors: List[str], item_type: str):
    """Show removal summary."""
    if successes or errors:
        # Create summary panel
        summary_text = ""
        
        if successes:
            summary_text += f"[green]✓ Successfully removed {len(successes)} {item_type}(s)[/green]\n"
            
        if errors:
            summary_text += f"[red]✗ Failed to remove {len(errors)} {item_type}(s)[/red]\n"
            for err in errors:
                summary_text += f"  • {err}\n"
                
        console.print("\n")
        console.print(
            Panel(
                summary_text.strip(),
                title="Removal Summary",
                border_style="green" if not errors else "red",
            )
        )


@register_command("remove", description="Remove templates or settings", category="core")
@click.command()
@click.argument("items", nargs=-1)
@click.option(
    "--type",
    "-t",
    type=click.Choice(["template", "hook", "permission"], case_sensitive=False),
    help="Type of item to remove",
)
@click.option(
    "--all",
    "-a",
    is_flag=True,
    help="Remove all installed items of the specified type (use with caution)",
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
    items: Tuple[str, ...],
    type: Optional[str],
    all: bool,
    permission: Optional[str],
    test_dir: Optional[Path],
    dry_run: bool,
    force: bool,
) -> None:
    """Remove installed templates, hooks, or permissions.
    
    Remove specific items by name or use --all to remove everything of a type.
    Use --permission to remove a specific permission from settings.
    
    Examples:
        claude-setup remove template new-python-project
        claude-setup remove hook validate-aws-command
        claude-setup remove --type template --all
        claude-setup remove --permission "Bash(npm:*)"
    """
    # Determine target directory
    if test_dir:
        target_dir = test_dir.resolve()
    else:
        target_dir = Path.home() / ".claude"
        
    # Handle permission removal
    if permission:
        success = remove_permission_from_settings(permission, target_dir, dry_run)
        if not success:
            ctx.exit(1)
        return
    
    # Determine item type
    item_type = type or "template"  # Default to template for backward compatibility
    if not type and items:
        # Try to infer type from context or ask user
        if not force:
            from rich.prompt import Prompt
            item_type = Prompt.ask(
                "What type of items to remove?",
                choices=["template", "hook"],
                default="template"
            )
    
    # Handle different item types
    if item_type == "template":
        # Find installed templates
        installed = find_installed_templates_for_removal(target_dir)
        
        if not installed:
            console.print(
                Panel(
                    "[yellow]No installed templates found to remove.[/yellow]\n\n"
                    "Use [cyan]claude-setup list[/cyan] to see available templates.",
                    title="No Templates Installed",
                    border_style="yellow",
                )
            )
            return
            
        # Handle template removal
        items_to_remove = handle_template_removal(installed, items, all, force, dry_run)
        
    elif item_type == "hook":
        # Find installed hooks
        installed = find_installed_hooks_for_removal(target_dir)
        
        if not installed:
            console.print(
                Panel(
                    "[yellow]No installed hooks found to remove.[/yellow]\n\n"
                    "Use [cyan]claude-setup hooks list[/cyan] to see available hooks.",
                    title="No Hooks Installed",
                    border_style="yellow",
                )
            )
            return
            
        # Handle hook removal
        items_to_remove = handle_hook_removal(installed, items, all, force, dry_run, target_dir)
        
    else:
        error(f"Unknown item type: {item_type}")
        ctx.exit(1)


def run_remove_command(
    ctx: click.Context,
    items: Tuple[str, ...],
    type: Optional[str],
    all: bool,
    permission: Optional[str],
    test_dir: Optional[Path],
    dry_run: bool,
    force: bool,
) -> None:
    """Run the remove command with the given options.
    
    This function serves as a bridge between the CLI and the command implementation.
    """
    # Call the remove command directly
    ctx.invoke(
        remove,
        items=items,
        type=type,
        all=all,
        permission=permission,
        test_dir=test_dir,
        dry_run=dry_run,
        force=force,
    )