"""Update command implementation for claude-code-setup."""

import sys
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Set

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..core.registry import register_command
from ..utils.template import get_all_templates_sync, get_template_sync
from ..utils.template_installer import TemplateInstaller, InstallationResult
from ..utils.fs import read_template_sync, template_exists_sync, get_default_settings
from ..utils.logger import error, info, success
from ..utils.settings import read_settings_sync, merge_settings_sync, save_settings_sync
from ..ui.prompts import MultiSelectPrompt, ConfirmationDialog
from ..ui.progress import MultiStepProgress, ProgressStep
from ..ui.styles import create_error_banner, create_panel

console = Console()


def compare_template_content(
    template_name: str, category: str, target_dir: Path
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Compare installed template with latest version.
    
    Args:
        template_name: Name of the template
        category: Template category
        target_dir: Target directory for templates
        
    Returns:
        Tuple of (needs_update, current_content, latest_content)
    """
    try:
        # Get current installed content
        current_content = read_template_sync(template_name, category, target_dir)
        if not current_content:
            return False, None, None
            
        # Get latest template content
        template = get_template_sync(template_name)
        if not template:
            return False, None, None
            
        latest_content = template.content
        
        # Compare content (strip whitespace for comparison)
        needs_update = current_content.strip() != latest_content.strip()
        
        return needs_update, current_content, latest_content
        
    except Exception as e:
        error(f"Error comparing template {template_name}: {e}")
        return False, None, None


def find_installed_templates(target_dir: Path) -> Dict[str, List[str]]:
    """Find all installed templates in the target directory.
    
    Args:
        target_dir: Target directory to scan
        
    Returns:
        Dictionary mapping categories to list of template names
    """
    installed = {}
    template_registry = get_all_templates_sync()
    
    for template in template_registry.templates.values():
        if template_exists_sync(template.name, template.category.value, str(target_dir)):
            if template.category.value not in installed:
                installed[template.category.value] = []
            installed[template.category.value].append(template.name)
            
    return installed


def get_updatable_templates(
    target_dir: Path, force: bool = False
) -> List[Tuple[str, str, bool]]:
    """Get list of templates that can be updated.
    
    Args:
        target_dir: Target directory to check
        force: Whether to include unchanged templates
        
    Returns:
        List of tuples (template_name, category, needs_update)
    """
    updatable = []
    installed = find_installed_templates(target_dir)
    
    for category, template_names in installed.items():
        for template_name in template_names:
            needs_update, _, _ = compare_template_content(
                template_name, category, target_dir
            )
            if needs_update or force:
                updatable.append((template_name, category, needs_update))
                
    return updatable


def update_templates_batch(
    templates: List[Tuple[str, str]],
    target_dir: Path,
    dry_run: bool = False,
    force: bool = False,
) -> Tuple[List[InstallationResult], List[str]]:
    """Update multiple templates in batch.
    
    Args:
        templates: List of (template_name, category) tuples
        target_dir: Target directory for installation
        dry_run: Whether to perform a dry run
        force: Whether to force update
        
    Returns:
        Tuple of (results, errors)
    """
    installer = TemplateInstaller(target_dir, dry_run=dry_run, force=force)
    results = []
    errors = []
    
    for template_name, category in templates:
        try:
            # Get the template
            template = get_template_sync(template_name)
            if not template:
                errors.append(f"Template '{template_name}' not found")
                continue
                
            # Install (update) the template
            result = installer.install_template(template)
            results.append(result)
            
        except Exception as e:
            errors.append(f"Error updating {template_name}: {str(e)}")
            
    return results, errors


def update_settings(
    target_dir: Path, global_settings: bool = False, dry_run: bool = False
) -> bool:
    """Update settings file with latest defaults while preserving customizations.
    
    Args:
        target_dir: Target directory for settings
        global_settings: Whether to update global settings
        dry_run: Whether to perform a dry run
        
    Returns:
        True if settings were updated successfully
    """
    try:
        # Read current settings
        settings_path = target_dir / "settings.json"
        current_settings = read_settings_sync(settings_path)
        
        # Get latest default settings
        default_settings = get_default_settings()
        
        # Convert current_settings to dict if it's a model
        if current_settings:
            current_dict = current_settings.model_dump()
        else:
            current_dict = {}
        
        # Merge settings (preserving user customizations)
        updated_settings = merge_settings_sync(default_settings, current_dict)
        
        # Check if there are any changes
        if current_dict == updated_settings:
            info("Settings are already up to date")
            return True
            
        if dry_run:
            info("[DRY RUN] Would update settings file")
            return True
            
        # Save updated settings
        save_settings_sync(updated_settings, settings_path)
        success("Settings updated successfully")
        return True
        
    except Exception as e:
        error(f"Failed to update settings: {e}")
        return False


def show_update_selection(
    updatable: List[Tuple[str, str, bool]], target_dir: Path
) -> Optional[List[Tuple[str, str]]]:
    """Show interactive template selection for updates.
    
    Args:
        updatable: List of updatable templates
        target_dir: Target directory
        
    Returns:
        Selected templates or None if cancelled
    """
    # Group by category
    by_category = {}
    for name, category, needs_update in updatable:
        if category not in by_category:
            by_category[category] = []
        by_category[category].append((name, needs_update))
    
    # Create choices
    choices = []
    for category in sorted(by_category.keys()):
        choices.append(f"[dim]{category.upper()}[/dim]")
        for name, needs_update in sorted(by_category[category]):
            status = "[red]•[/red]" if needs_update else "[green]✓[/green]"
            choices.append(f"  {status} {name}")
    
    prompt = MultiSelectPrompt(
        "Select templates to update:",
        choices=choices,
        default_selected=[
            f"  [red]•[/red] {name}"
            for name, _, needs_update in updatable
            if needs_update
        ],
    )
    
    selected = prompt.ask()
    if not selected:
        return None
        
    # Parse selected templates
    result = []
    for item in selected:
        if item.startswith("  "):
            # Extract template name (remove status indicator)
            parts = item.strip().split(" ", 1)
            if len(parts) == 2:
                template_name = parts[1]
                # Find category
                for name, category, _ in updatable:
                    if name == template_name:
                        result.append((template_name, category))
                        break
                        
    return result


@register_command("update", description="Update templates or settings to their latest versions", category="core")
@click.command()
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
    templates: Tuple[str, ...],
    all: bool,
    force: bool,
    test_dir: Optional[Path],
    dry_run: bool,
    settings: bool,
    global_settings: bool,
) -> None:
    """Update installed templates and settings with latest versions.
    
    Update specific templates by name or use --all to update everything.
    The command will check for changes and only update modified templates.
    
    Examples:
        claude-setup update new-python-project
        claude-setup update --all
        claude-setup update --settings
    """
    # Determine target directory
    if test_dir:
        target_dir = test_dir.resolve()
    else:
        target_dir = Path.home() / ".claude"
        
    # Handle settings update
    if settings:
        success = update_settings(target_dir, global_settings, dry_run)
        if not success:
            ctx.exit(1)
        return
        
    # Find updatable templates
    updatable = get_updatable_templates(target_dir, force)
    
    if not updatable:
        console.print(
            Panel(
                "[yellow]No installed templates found to update.[/yellow]\n\n"
                "Use [cyan]claude-setup add[/cyan] to install templates first.",
                title="No Updates Available",
                border_style="yellow",
            )
        )
        return
        
    # Determine which templates to update
    templates_to_update = []
    
    if all:
        # Update all updatable templates
        templates_to_update = [(name, cat) for name, cat, _ in updatable]
        
    elif templates:
        # Update specific templates
        template_set = set(templates)
        for name, category, _ in updatable:
            if name in template_set:
                templates_to_update.append((name, category))
                
        # Check for templates that weren't found
        found_names = {t[0] for t in templates_to_update}
        not_found = template_set - found_names
        if not_found:
            console.print(
                create_error_banner(
                    "Templates Not Found",
                    f"The following templates are not installed: {', '.join(not_found)}"
                )
            )
            
    else:
        # Interactive selection
        selected = show_update_selection(updatable, target_dir)
        if not selected:
            console.print("[yellow]Update cancelled.[/yellow]")
            return
        templates_to_update = selected
        
    if not templates_to_update:
        console.print("[yellow]No templates selected for update.[/yellow]")
        return
        
    # Create progress steps
    steps = [
        ProgressStep(f"Update {name}", f"Updating {name} from {cat}")
        for name, cat in templates_to_update
    ]
    
    # Create multi-step progress
    progress = MultiStepProgress(
        title=f"🔄 Updating {len(templates_to_update)} Template(s)",
        steps=steps,
        console_obj=console,
    )
    
    # Perform updates with progress tracking
    with progress:
        results, errors = [], []
        installer = TemplateInstaller(target_dir, dry_run=dry_run, force=force)
        
        for i, (template_name, category) in enumerate(templates_to_update):
            progress.start_step(i)
            
            try:
                # Get the template
                template = get_template_sync(template_name)
                if not template:
                    errors.append(f"Template '{template_name}' not found")
                    progress.complete_step(i, success=False)
                    continue
                    
                # Install (update) the template
                result = installer.install_template(template)
                results.append(result)
                progress.complete_step(i, success=result.success)
                
            except Exception as e:
                errors.append(f"Error updating {template_name}: {str(e)}")
                progress.complete_step(i, success=False)
        
        # Show installation report
        if results or errors:
            report_panel = progress.create_installation_report("templates")
            console.print("\n")
            console.print(report_panel)
        
    # Exit with error if any updates failed
    if errors and not dry_run:
        ctx.exit(1)


def run_update_command(
    ctx: click.Context,
    templates: Tuple[str, ...],
    all: bool,
    force: bool,
    test_dir: Optional[Path],
    dry_run: bool,
    settings: bool,
    global_settings: bool,
) -> None:
    """Run the update command with the given options.
    
    This function serves as a bridge between the CLI and the command implementation.
    """
    # Call the update command directly
    ctx.invoke(
        update,
        templates=templates,
        all=all,
        force=force,
        test_dir=test_dir,
        dry_run=dry_run,
        settings=settings,
        global_settings=global_settings,
    )