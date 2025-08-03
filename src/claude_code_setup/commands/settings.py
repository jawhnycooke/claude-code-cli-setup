"""Settings command implementation for claude-code-setup.

This module implements the settings command which allows users to manage
their Claude Code configuration including themes, permissions, and environment variables.
"""

import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

from ..core.registry import register_command
from ..utils.logger import error, info, success, warning
from ..utils.settings import (
    read_settings_sync,
    save_settings_sync,
    get_available_themes_sync,
    get_available_permission_sets_sync,
    get_settings_sync,
    merge_settings_sync,
)
from ..utils.fs import CLAUDE_SETTINGS_FILE
from ..ui.prompts import MultiSelectPrompt, ConfirmationDialog, SelectOption
from ..ui.styles import (
    console,
    create_panel,
    create_table,
    create_command_error,
    create_success_banner,
    COLORS,
    BOX_STYLES,
)


def determine_settings_path(test_dir: Optional[str], global_config: bool) -> Path:
    """Determine the settings file path based on options."""
    if test_dir:
        settings_path = Path(test_dir) / ".claude" / "settings.json"
        info(f"Using test directory settings: {settings_path}")
    elif global_config:
        settings_path = Path.home() / ".claude" / "settings.json"
        info(f"Using global settings: {settings_path}")
    else:
        settings_path = Path.cwd() / ".claude" / "settings.json"
        info(f"Using local settings: {settings_path}")
    
    return settings_path


def show_current_settings(settings_path: Path) -> None:
    """Display current settings in a formatted table."""
    console.print(f"\n[bold {COLORS['header']}]Current Settings[/bold {COLORS['header']}]")
    console.print(f"[dim]Location: {settings_path}[/dim]\n")
    
    if not settings_path.exists():
        console.print(Panel(
            "[yellow]No settings file found.[/yellow]\n"
            "Use [cyan]claude-setup init[/cyan] to create initial configuration.",
            title="Settings Not Found",
            border_style="yellow"
        ))
        return
    
    try:
        settings = read_settings_sync(settings_path)
        if not settings:
            error("Failed to read settings file")
            return
        
        # Create settings table
        table = create_table(
            title="Configuration",
            show_header=True,
            box=BOX_STYLES["default"],
        )
        table.add_column("Setting", style=COLORS["primary"], width=20)
        table.add_column("Value", style="white")
        
        # Add basic settings
        table.add_row("Theme", settings.theme or "default")
        table.add_row("Auto Updater", "Enabled" if settings.autoUpdaterStatus else "Disabled")
        table.add_row("Notifications", settings.preferredNotifChannel or "terminal")
        table.add_row("Verbose Logging", "Enabled" if settings.verbose else "Disabled")
        
        # Add permissions count
        perm_count = len(settings.permissions.allow) if settings.permissions else 0
        table.add_row("Permissions", f"{perm_count} allowed")
        
        # Add environment variables count
        env_count = len(settings.env) if settings.env else 0
        table.add_row("Environment Variables", f"{env_count} defined")
        
        # Add hooks count
        hooks_count = 0
        if settings.hooks:
            hooks_dict = settings.hooks.model_dump()
            for event_hooks in hooks_dict.values():
                if event_hooks:
                    for hook_group in event_hooks:
                        hooks_count += len(hook_group.get('hooks', []))
        table.add_row("Hooks", f"{hooks_count} registered")
        
        # Add ignore patterns count
        ignore_count = len(settings.ignorePatterns) if settings.ignorePatterns else 0
        table.add_row("Ignore Patterns", f"{ignore_count} patterns")
        
        console.print(table)
        
    except Exception as e:
        error(f"Error reading settings: {e}")


def manage_theme(settings_path: Path) -> bool:
    """Manage theme selection."""
    console.print(f"\n[bold {COLORS['header']}]Theme Management[/bold {COLORS['header']}]")
    
    # Get available themes
    try:
        available_themes = get_available_themes_sync()
        if not available_themes:
            warning("No themes available")
            return False
        
        # Get current theme
        current_settings = read_settings_sync(settings_path)
        current_theme = current_settings.theme if current_settings else "default"
        
        console.print(f"Current theme: [bold {COLORS['primary']}]{current_theme}[/bold {COLORS['primary']}]")
        console.print(f"Available themes: {', '.join(available_themes)}")
        
        # Prompt for new theme
        new_theme = Prompt.ask(
            "Select new theme",
            choices=available_themes,
            default=current_theme
        )
        
        if new_theme == current_theme:
            info("Theme unchanged")
            return False
        
        # Update settings
        if current_settings:
            current_settings.theme = new_theme
            save_settings_sync(current_settings, settings_path)
        else:
            # Create new settings with theme
            new_settings = get_settings_sync(theme=new_theme)
            save_settings_sync(new_settings, settings_path)
        
        success(f"Theme updated to: {new_theme}")
        return True
        
    except Exception as e:
        error(f"Failed to update theme: {e}")
        return False


def manage_environment_variables(settings_path: Path) -> bool:
    """Manage environment variables."""
    console.print(f"\n[bold {COLORS['header']}]Environment Variables[/bold {COLORS['header']}]")
    
    try:
        current_settings = read_settings_sync(settings_path)
        if not current_settings:
            warning("No settings file found")
            return False
        
        env_vars = current_settings.env or {}
        
        # Show current environment variables
        if env_vars:
            table = create_table(
                title="Current Environment Variables",
                show_header=True,
                box=BOX_STYLES["minimal"],
            )
            table.add_column("Variable", style=COLORS["primary"])
            table.add_column("Value", style="white")
            
            for key, value in env_vars.items():
                # Mask sensitive values
                display_value = value if len(value) <= 20 else f"{value[:10]}...{value[-5:]}"
                table.add_row(key, display_value)
            
            console.print(table)
        else:
            console.print("[dim]No environment variables defined[/dim]")
        
        # Environment variable management menu
        while True:
            console.print("\n[bold]Environment Variable Actions:[/bold]")
            console.print("  1. Add/Update variable")
            console.print("  2. Remove variable")
            console.print("  3. Clear all variables")
            console.print("  4. Back to main menu")
            
            choice = Prompt.ask("Choose action", choices=["1", "2", "3", "4"], default="4")
            
            if choice == "1":
                # Add/Update variable
                var_name = Prompt.ask("Variable name")
                if not var_name.strip():
                    warning("Variable name cannot be empty")
                    continue
                
                var_value = Prompt.ask("Variable value")
                env_vars[var_name] = var_value
                success(f"Set {var_name} = {var_value}")
                
            elif choice == "2":
                # Remove variable
                if not env_vars:
                    warning("No variables to remove")
                    continue
                
                var_name = Prompt.ask(
                    "Variable to remove",
                    choices=list(env_vars.keys())
                )
                if var_name in env_vars:
                    del env_vars[var_name]
                    success(f"Removed variable: {var_name}")
                
            elif choice == "3":
                # Clear all variables
                if env_vars and Confirm.ask("Clear all environment variables?"):
                    env_vars.clear()
                    success("Cleared all environment variables")
                
            elif choice == "4":
                break
        
        # Save updated settings
        current_settings.env = env_vars if env_vars else None
        save_settings_sync(current_settings, settings_path)
        
        return True
        
    except Exception as e:
        error(f"Failed to manage environment variables: {e}")
        return False


def manage_permissions(settings_path: Path) -> bool:
    """Manage permission sets."""
    console.print(f"\n[bold {COLORS['header']}]Permission Management[/bold {COLORS['header']}]")
    
    try:
        current_settings = read_settings_sync(settings_path)
        if not current_settings:
            warning("No settings file found")
            return False
        
        current_permissions = current_settings.permissions.allow if current_settings.permissions else []
        available_permission_sets = get_available_permission_sets_sync()
        
        # Show current permissions
        console.print(f"Current permissions: {len(current_permissions)} allowed")
        if current_permissions:
            # Group by permission set
            permission_groups = {}
            for perm in current_permissions:
                if perm.startswith("Bash(") and perm.endswith(")"):
                    prefix = perm.split("(")[1].split(":")[0] if ":" in perm else "misc"
                    if prefix not in permission_groups:
                        permission_groups[prefix] = []
                    permission_groups[prefix].append(perm)
            
            for group, perms in permission_groups.items():
                console.print(f"  [bold {COLORS['primary']}]{group}[/bold {COLORS['primary']}]: {len(perms)} permissions")
        
        # Permission management menu
        while True:
            console.print("\n[bold]Permission Actions:[/bold]")
            console.print("  1. Add permission set")
            console.print("  2. Add custom permission")
            console.print("  3. Remove permissions")
            console.print("  4. Reset to defaults")
            console.print("  5. Back to main menu")
            
            choice = Prompt.ask("Choose action", choices=["1", "2", "3", "4", "5"], default="5")
            
            if choice == "1":
                # Add permission set
                console.print(f"Available permission sets: {', '.join(available_permission_sets)}")
                options = [SelectOption(value=pset, label=pset) for pset in available_permission_sets]
                selected_sets = MultiSelectPrompt(
                    "Select permission sets to add",
                    options=options
                ).ask()
                
                if selected_sets:
                    # Generate new settings with selected permission sets
                    new_settings = get_settings_sync(permission_sets=selected_sets)
                    merged_settings = merge_settings_sync(current_settings, new_settings)
                    save_settings_sync(merged_settings, settings_path)
                    success(f"Added permission sets: {', '.join(selected_sets)}")
                    return True
                    
            elif choice == "2":
                # Add custom permission
                custom_perm = Prompt.ask("Enter custom permission (e.g., 'Bash(docker:*)')")
                if custom_perm.strip():
                    current_settings.permissions.allow.append(custom_perm.strip())
                    current_settings.permissions.allow = list(set(current_settings.permissions.allow))  # Dedupe
                    save_settings_sync(current_settings, settings_path)
                    success(f"Added custom permission: {custom_perm}")
                    
            elif choice == "3":
                # Remove permissions
                if not current_permissions:
                    warning("No permissions to remove")
                    continue
                
                options = [SelectOption(value=perm, label=perm) for perm in current_permissions]
                selected_perms = MultiSelectPrompt(
                    "Select permissions to remove",
                    options=options
                ).ask()
                
                if selected_perms:
                    for perm in selected_perms:
                        if perm in current_settings.permissions.allow:
                            current_settings.permissions.allow.remove(perm)
                    save_settings_sync(current_settings, settings_path)
                    success(f"Removed {len(selected_perms)} permissions")
                    
            elif choice == "4":
                # Reset to defaults
                if Confirm.ask("Reset permissions to default set?"):
                    default_settings = get_settings_sync()
                    current_settings.permissions = default_settings.permissions
                    save_settings_sync(current_settings, settings_path)
                    success("Reset permissions to defaults")
                    
            elif choice == "5":
                break
        
        return True
        
    except Exception as e:
        error(f"Failed to manage permissions: {e}")
        return False


def show_settings_menu(settings_path: Path) -> None:
    """Show interactive settings management menu."""
    while True:
        console.print(f"\n[bold {COLORS['header']}]Settings Management[/bold {COLORS['header']}]")
        console.print(f"[dim]Configuration: {settings_path}[/dim]\n")
        
        console.print("[bold]Available Actions:[/bold]")
        console.print("  1. 📋 View current settings")
        console.print("  2. 🎨 Manage themes")
        console.print("  3. 🌍 Manage environment variables")
        console.print("  4. 🔐 Manage permissions")
        console.print("  5. 📁 Show settings file location")
        console.print("  6. ❌ Exit")
        
        choice = Prompt.ask("Choose action", choices=["1", "2", "3", "4", "5", "6"], default="1")
        
        try:
            if choice == "1":
                show_current_settings(settings_path)
                
            elif choice == "2":
                manage_theme(settings_path)
                
            elif choice == "3":
                manage_environment_variables(settings_path)
                
            elif choice == "4":
                manage_permissions(settings_path)
                
            elif choice == "5":
                console.print(f"\n[bold]Settings File Location:[/bold]")
                console.print(f"  {settings_path}")
                if settings_path.exists():
                    console.print(f"  [green]✓ File exists[/green]")
                    console.print(f"  Size: {settings_path.stat().st_size} bytes")
                else:
                    console.print(f"  [yellow]⚠ File does not exist[/yellow]")
                    
            elif choice == "6":
                console.print("[dim]Exiting settings management[/dim]")
                break
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled[/yellow]")
            break


@register_command("settings", description="Manage Claude Code settings and configuration", category="core")
def run_settings_command(
    action: Optional[str] = None,
    test_dir: Optional[str] = None,
    global_config: bool = False,
    interactive: bool = True,
) -> None:
    """Main entry point for the settings command."""
    try:
        # Determine settings path
        settings_path = determine_settings_path(test_dir, global_config)
        
        # Ensure parent directory exists
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        
        if action:
            # Direct action mode
            if action == "show":
                show_current_settings(settings_path)
            elif action == "theme":
                manage_theme(settings_path)
            elif action == "env":
                manage_environment_variables(settings_path)
            elif action == "permissions":
                manage_permissions(settings_path)
            else:
                error(f"Unknown action: {action}")
                info("Available actions: show, theme, env, permissions")
                sys.exit(1)
        else:
            # Interactive mode
            if interactive:
                show_settings_menu(settings_path)
            else:
                show_current_settings(settings_path)
                
    except KeyboardInterrupt:
        console.print("\n[yellow]Settings management cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        error_panel = create_command_error(
            "settings",
            e,
            suggestions=[
                "Check that the configuration directory exists",
                "Run 'claude-setup init' if you haven't set up yet",
                "Use --global to manage global configuration",
            ]
        )
        console.print(error_panel)
        sys.exit(1)