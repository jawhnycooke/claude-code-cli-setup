"""Init command implementation for claude-code-setup.

This module implements the init command, converted from TypeScript init.ts.
Handles interactive setup, directory creation, settings configuration, and template installation.
"""

import sys
from pathlib import Path
from typing import Optional

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Confirm, Prompt

# Enhanced UI components
from ..ui.prompts import (
    ConfirmationDialog,
    ValidatedPrompt,
    show_selection_summary,
)
from ..ui.validation import (
    create_choice_validator,
    create_required_validator,
)
from ..ui.progress import (
    ProgressStep,
    MultiStepProgress,
)

from ..utils import (
    ensure_claude_directories,
    ensure_claude_directories_sync,
    get_settings,
    get_settings_sync,
    read_settings_sync,
    merge_settings_sync,
    save_settings_sync,
    success,
    info,
    warning,
    error,
    highlight,
    CLAUDE_HOME,
    CLAUDE_SETTINGS_FILE,
)
from ..utils.template import (
    get_all_templates_sync,
    get_template_categories_sync,
)

# Import styled console and components from centralized styles
from ..ui.styles import (
    console,
    error_console,
    create_console,
    create_panel,
    create_table,
    create_welcome_banner,
    create_success_banner,
    create_error_banner,
    create_step_indicator,
    create_ascii_art_banner,
    format_error,
    create_command_error,
    create_validation_error,
    COLORS,
    BOX_STYLES,
)


def show_welcome_banner() -> None:
    """Show the welcome banner for interactive setup."""
    # Create ASCII art style banner with gradient matching TypeScript version
    banner = create_ascii_art_banner(
        title="Claude Setup",
        subtitle="🤖 Configure templates, settings, and permissions for Claude Code ✨",
    )
    console.print(banner)
    console.print()


def show_success_summary(target_home: Path, templates_installed: int = 0) -> None:
    """Show success summary after setup completion."""
    console.print()
    details = {
        "Settings saved to": str(target_home / 'settings.json'),
        "Commands directory": str(target_home / 'commands'),
    }
    if templates_installed > 0:
        details["Templates installed"] = str(templates_installed)
    
    message = (
        f"\n[{COLORS['highlight']}]🚀 Next steps:[/{COLORS['highlight']}]\n"
        "• Run [bold]claude-setup list[/bold] to see what's available\n"
        "• Run [bold]claude-setup add[/bold] to install more templates\n"
        "• Start using Claude Code with your new setup!"
    )
    
    success_panel = create_success_banner(
        title="🎉 Setup Complete!",
        message=message,
        details=details,
    )
    console.print(success_panel)


def determine_target_directory(
    test_dir: Optional[str], global_config: bool
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


def parse_permission_sets(permissions: str) -> list[str]:
    """Parse comma-separated permission sets."""
    return [p.strip() for p in permissions.split(",") if p.strip()]


def run_quick_setup(
    force: bool,
    dry_run: bool,
    test_dir: Optional[str],
    global_config: bool,
    permissions: str,
    theme: str,
    no_check: bool,
) -> None:
    """Run quick setup with defaults (non-interactive)."""
    console.print(f"⚡ [{COLORS['header']}]Quick Setup with Defaults[/{COLORS['header']}]")
    
    # Determine target directory
    target_home = determine_target_directory(test_dir, global_config)
    target_settings_file = target_home / "settings.json"
    
    # Parse permission sets
    permission_sets = parse_permission_sets(permissions)
    
    # Create multi-step progress for quick setup
    steps = [
        ProgressStep("check", "Check existing configuration", "Verify if setup already exists"),
        ProgressStep("dirs", "Create directories", "Create .claude directory structure"),
        ProgressStep("settings", "Generate settings", "Create settings.json with permissions"),
        ProgressStep("save", "Save configuration", "Write settings to disk"),
        ProgressStep("templates", "Install default templates", "Install recommended templates"),
    ]
    
    multi_progress = MultiStepProgress(
        title="⚡ Quick Setup with Defaults",
        steps=steps,
        console_obj=console,
    )
    
    try:
        with multi_progress.live_display() as (live, update):
            # Check for existing settings first
            multi_progress.start_step("check")
            update()
            
            if target_settings_file.exists() and not no_check and not force:
                multi_progress.complete_step("check", success=False, error_message="Configuration already exists")
                
                warning("Claude Code is already configured")
                info(f"Settings file exists at: {target_settings_file}")
                info(f"Commands directory exists at: {target_home / 'commands'}")
                info("Use --force to overwrite existing configuration or --no-check to skip this check")
                sys.exit(1)
            
            multi_progress.complete_step("check", success=True)
            update()
            
            if dry_run:
                # Skip remaining steps in dry run
                multi_progress.skip_step("dirs", "Dry run mode")
                multi_progress.skip_step("settings", "Dry run mode")
                multi_progress.skip_step("save", "Dry run mode")
                multi_progress.skip_step("templates", "Dry run mode")
                update()
                
                info("Dry run mode - would perform the following actions:")
                info(f"• Create directory: {target_home}")
                info(f"• Create directory: {target_home / 'commands'}")
                info(f"• Create settings file with: {', '.join(permission_sets)} permissions")
                info(f"• Use theme: {theme}")
                info("• Install default templates: code-review, fix-issue, create-tasks")
                success("Dry run complete")
                return
            
            # Create directories
            multi_progress.start_step("dirs")
            update()
            
            ensure_claude_directories_sync(str(target_home))
            
            # Create category directories
            categories = ['python', 'node', 'project', 'general']
            for category in categories:
                category_dir = target_home / "commands" / category
                category_dir.mkdir(parents=True, exist_ok=True)
            
            multi_progress.complete_step("dirs", success=True)
            update()
            
            # Generate and save settings
            multi_progress.start_step("settings")
            update()
            
            settings = get_settings_sync(
                permission_sets=permission_sets,
                theme=theme,
            )
            
            multi_progress.complete_step("settings", success=True)
            update()
            
            # Save configuration
            multi_progress.start_step("save")
            update()
            
            save_settings_sync(settings, target_settings_file)
            
            multi_progress.complete_step("save", success=True)
            update()
            
            # Install default templates
            multi_progress.start_step("templates")
            update()
            
            # Use the new template installer
            from ..utils.template_installer import TemplateInstaller
            installer = TemplateInstaller(
                target_dir=target_home,
                dry_run=False,
                force=force,
                backup=True
            )
            
            # Default templates to install in quick setup
            default_templates = ["code-review", "fix-issue", "create-tasks"]
            templates_installed = 0
            
            for template_name in default_templates:
                result = installer.install_template(template_name)
                if result.success:
                    templates_installed += 1
                else:
                    warning(f"Failed to install {template_name}: {result.message}")
                    
            multi_progress.complete_step("templates", success=True)
            update()
            
        # Show final report
        console.print(multi_progress.create_installation_report("configuration steps"))
        show_success_summary(target_home, templates_installed)
    
    except Exception as e:
        error_panel = create_command_error(
            "init",
            e,
            suggestions=[
                "Try running with '--force' to overwrite existing configuration",
                "Check that you have write permissions to the target directory",
            ]
        )
        error_console.print(error_panel)
        sys.exit(1)


def run_interactive_setup(
    force: bool,
    dry_run: bool,
    test_dir: Optional[str],
    global_config: bool,
    permissions: str,
    theme: str,
    no_check: bool,  
) -> None:
    """Run interactive setup with step-by-step guidance."""
    show_welcome_banner()
    
    console.print("🚀 Welcome to Claude Code Setup!")
    console.print("This interactive setup will help you configure Claude Code for your needs.\n")
    
    # Step 1: Choose setup location
    console.print(create_step_indicator(1, 4, "Choose Setup Location"))
    location_choices = [
        ("local", "📁 Current Directory (./.claude) - Recommended for projects"),
        ("global", "🌍 Global Directory (~/.claude) - Available everywhere"),
    ]
    
    if test_dir:
        location_choices.append(("test", f"🧪 Test Directory ({test_dir}/.claude)"))
    
    # Show choices
    table = create_table(
        show_header=False,
        box=BOX_STYLES["minimal"],
        show_edge=False,
    )
    table.add_column("Choice", style=COLORS["primary"])
    table.add_column("Description")
    
    for i, (value, description) in enumerate(location_choices, 1):
        table.add_row(f"[bold]{i}[/bold]", description)
    
    console.print(table)
    console.print()
    
    while True:
        choice = Prompt.ask("Choose setup location", choices=[str(i) for i in range(1, len(location_choices) + 1)], default="1")
        try:
            choice_idx = int(choice) - 1
            setup_location = location_choices[choice_idx][0]
            break
        except (ValueError, IndexError):
            error_panel = create_validation_error(
                "location",
                choice,
                "Invalid location selection",
                suggestions=["Please enter a number from the list above"],
            )
            console.print(error_panel)
    
    # Determine target directory
    if setup_location == "test" and test_dir:
        target_home = Path(test_dir) / ".claude"
    elif setup_location == "global":
        target_home = CLAUDE_HOME
    else:
        target_home = Path.cwd() / ".claude"
    
    target_settings_file = target_home / "settings.json"
    target_commands_dir = target_home / "commands"
    
    console.print(f"\n[{COLORS['muted']}]Selected location: {target_home}[/{COLORS['muted']}]\n")
    
    # Step 2: Check for existing setup
    if target_settings_file.exists() and not no_check and not force:
        console.print(f"[{COLORS['warning']} bold]⚠️  Existing Configuration Found[/{COLORS['warning']} bold]")
        console.print(f"Claude Code is already set up at: {target_home}")
        console.print("What would you like to do?")
        
        action_choices = [
            ("update", "🔄 Update existing settings with new defaults"),
            ("overwrite", "♻️  Start fresh (overwrite everything)"),
            ("keep", "✋ Keep existing setup (exit)"),
        ]
        
        table = create_table(
            show_header=False,
            box=BOX_STYLES["minimal"],
        )
        table.add_column("Choice", style=COLORS["primary"])
        table.add_column("Description")
        
        for i, (value, description) in enumerate(action_choices, 1):
            table.add_row(f"[bold]{i}[/bold]", description)
        
        console.print(table)
        console.print()
        
        while True:
            action_choice = Prompt.ask("Choose action", choices=["1", "2", "3"], default="1")
            try:
                action_idx = int(action_choice) - 1
                action = action_choices[action_idx][0]
                break
            except (ValueError, IndexError):
                console.print(f"[{COLORS['error']}]Invalid choice. Please try again.[/{COLORS['error']}]")
        
        if action == "keep":
            info("Keeping existing setup")
            console.print(f"\n[{COLORS['success']}]✓ Your existing Claude Code setup has been preserved.[/{COLORS['success']}]")
            console.print("Run [bold]claude-setup list[/bold] to see your current configuration.")
            return
        
        if action == "update":
            update_existing_settings(target_settings_file)
            return
        
        # Continue with overwrite if selected
        console.print(f"\n[{COLORS['warning']}]Proceeding with fresh setup...[/{COLORS['warning']}]\n")
    
    # Step 3: Configure settings
    console.print(create_step_indicator(2, 4, "Configure Settings"))
    
    # Permission sets configuration
    default_permissions = parse_permission_sets(permissions)
    console.print(f"Default permission sets: [{COLORS['primary']}]{', '.join(default_permissions)}[/{COLORS['primary']}]")
    
    use_defaults = Confirm.ask("Use default permission sets?", default=True)
    
    if not use_defaults:
        from ..utils.settings import get_available_permission_sets_sync
        available_sets = get_available_permission_sets_sync()
        console.print(f"Available permission sets: {', '.join(available_sets)}")
        
        custom_permissions = Prompt.ask(
            "Enter comma-separated permission sets",
            default=permissions,
        )
        permission_sets = parse_permission_sets(custom_permissions)
    else:
        permission_sets = default_permissions
    
    # Theme configuration
    from ..utils.settings import get_available_themes_sync
    available_themes = get_available_themes_sync()
    console.print(f"Available themes: [{COLORS['primary']}]{', '.join(available_themes)}[/{COLORS['primary']}]")
    
    # Use enhanced validated prompt for theme selection
    theme_validator = create_choice_validator(available_themes, "theme", case_sensitive=False)
    
    def validate_theme(value: str) -> tuple[bool, Optional[str]]:
        messages = theme_validator(value)
        if messages:
            return False, messages[0].message
        return True, None
    
    theme_prompt = ValidatedPrompt(
        "Choose theme",
        validate_theme,
        default=theme,
    )
    
    selected_theme = theme_prompt.ask()
    
    # Step 4: Template installation
    console.print(f"\n{create_step_indicator(3, 4, 'Template Installation')}")
    install_templates = Confirm.ask("Would you like to install some popular command templates now?", default=True)
    
    selected_templates: list[str] = []
    if install_templates:
        try:
            template_registry = get_all_templates_sync()
            templates = template_registry.templates
            template_choices = [
                ("code-review", True),
                ("fix-issue", True), 
                ("create-tasks", True),
                ("update-tasks", False),
                ("generate-docs", False),
                ("optimization", False),
            ]
            
            console.print("Popular templates (recommended selections marked):")
            
            table = create_table(
                show_header=False,
                box=BOX_STYLES["minimal"],
            )
            table.add_column("Template", style=COLORS["primary"])
            table.add_column("Recommended", justify="center")
            table.add_column("Description")
            
            for template_name, recommended in template_choices:
                if template_name in templates:
                    template = templates[template_name]
                    table.add_row(
                        template_name,
                        "✓" if recommended else " ",
                        template.description[:50] + "..." if len(template.description) > 50 else template.description
                    )
            
            console.print(table)
            console.print()
            
            # Simple template selection (for now, install recommended ones)
            install_recommended = Confirm.ask("Install recommended templates?", default=True)
            
            if install_recommended:
                selected_templates = [name for name, recommended in template_choices if recommended and name in templates]
            
        except Exception as e:
            warning(f"Could not load templates: {e}")
    
    # Step 5: Confirm and create
    console.print(f"\n{create_step_indicator(4, 4, 'Confirmation')}")
    
    # Show summary
    summary_table = create_table(
        show_header=False,
        box=BOX_STYLES["minimal"],
    )
    summary_table.add_column("Setting", style=COLORS["primary"], width=20)
    summary_table.add_column("Value")
    
    summary_table.add_row("Location", str(target_home))
    summary_table.add_row("Permission sets", ", ".join(permission_sets))
    summary_table.add_row("Theme", selected_theme)
    summary_table.add_row("Templates", f"{len(selected_templates)} selected" if selected_templates else "None")
    
    console.print(summary_table)
    
    # Enhanced selection summary using new UI component
    selections = {
        "Location": str(target_home),
        "Permission sets": permission_sets,
        "Theme": selected_theme,
        "Templates": selected_templates if selected_templates else ["None"],
    }
    
    show_selection_summary("Configuration Summary", selections)
    console.print()
    
    if dry_run:
        console.print(f"[{COLORS['warning']}]🔍 Dry run mode - no changes will be made[/{COLORS['warning']}]")
        
        info("Would perform the following actions:")
        info(f"• Create directory: {target_home}")
        info(f"• Create settings with theme: {selected_theme}")
        info(f"• Add {len(permission_sets)} permission sets")
        if selected_templates:
            info(f"• Install {len(selected_templates)} templates")
        
        success("Dry run complete")
        return
    
    # Use enhanced confirmation dialog
    confirmation = ConfirmationDialog(
        title="Confirm Setup",
        message="Ready to create Claude Code configuration with the above settings.",
        details={
            "Location": str(target_home),
            "Templates": f"{len(selected_templates)} templates" if selected_templates else "No templates",
            "This will": "Create directories, install templates, and save configuration"
        },
        default=True,
    )
    
    proceed = confirmation.ask()
    if not proceed:
        console.print(f"[{COLORS['warning']}]Setup cancelled.[/{COLORS['warning']}]")
        return
    
    # Create the setup
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:
        
        setup_task = progress.add_task("Creating Claude Code setup...", total=100)
        
        try:
            # Create directories
            progress.update(setup_task, advance=20, description="Creating directories...")
            ensure_claude_directories_sync(str(target_home))
            
            # Create category directories
            categories = ['python', 'node', 'project', 'general']
            for category in categories:
                category_dir = target_home / "commands" / category
                category_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate and save settings
            progress.update(setup_task, advance=30, description="Generating settings...")
            settings = get_settings_sync(
                permission_sets=permission_sets,
                theme=selected_theme,
            )
            
            save_settings_sync(settings, target_settings_file)
            
            # Install selected templates
            templates_installed = 0
            if selected_templates:
                progress.update(setup_task, advance=30, description="Installing templates...")
                
                # Use the new template installer
                from ..utils.template_installer import TemplateInstaller
                installer = TemplateInstaller(
                    target_dir=target_home,
                    dry_run=False,
                    force=force,
                    backup=True
                )
                
                for template_name in selected_templates:
                    result = installer.install_template(template_name)
                    if result.success:
                        templates_installed += 1
                        progress.update(
                            setup_task,
                            description=f"Installed {template_name}"
                        )
                    else:
                        warning(f"Failed to install {template_name}: {result.message}")
            
            progress.update(setup_task, advance=20, description="Setup complete!", completed=100)
            
        except Exception as e:
            progress.stop()
            error_panel = create_command_error(
                "init",
                e,
                suggestions=[
                    "Try running in quick mode with '--quick'",
                    "Check that the target directory is accessible",
                ]
            )
            error_console.print(error_panel)
            sys.exit(1)
    
    show_success_summary(target_home, templates_installed)


def update_existing_settings(settings_path: Path) -> None:
    """Update existing settings with new defaults."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        update_task = progress.add_task("Updating existing settings...", total=None)
        
        try:
            current_settings = read_settings_sync(settings_path)
            if not current_settings:
                progress.stop()
                warning_panel = create_error_banner(
                    title="⚠️  Warning",
                    message="Could not read existing settings, using defaults",
                )
                console.print(warning_panel)
                current_settings = {}
            
            default_settings = get_settings_sync()
            merged_settings = merge_settings_sync(current_settings, default_settings)
            
            save_settings_sync(merged_settings, settings_path)
            
            progress.update(update_task, description="Settings updated successfully!")
            progress.stop()
            
            success_panel = create_success_banner(
                title="Settings Updated",
                message=(
                    "• Your settings have been updated with the latest defaults\n"
                    "• Your custom configurations have been preserved\n"
                    "• Run [bold]claude-setup list[/bold] to see your updated settings"
                ),
            )
            console.print(success_panel)
            
        except Exception as e:
            progress.stop()
            error_panel = create_command_error(
                "init",
                e,
                suggestions=[
                    "Check that the settings file is not corrupted",
                    "Try deleting the settings file and running init again",
                ]
            )
            error_console.print(error_panel)
            sys.exit(1)


def run_init_command(
    quick: bool,
    force: bool,
    dry_run: bool,
    test_dir: Optional[str],
    global_config: bool,
    permissions: str,
    theme: str,
    no_check: bool,
    interactive: bool,
) -> None:
    """Main entry point for the init command."""
    try:
        if quick or not interactive:
            run_quick_setup(
                force=force,
                dry_run=dry_run,
                test_dir=test_dir,
                global_config=global_config,
                permissions=permissions,
                theme=theme,
                no_check=no_check,
            )
        else:
            run_interactive_setup(
                force=force,
                dry_run=dry_run,
                test_dir=test_dir,
                global_config=global_config,
                permissions=permissions,
                theme=theme,
                no_check=no_check,
            )
            
    except KeyboardInterrupt:
        console.print("\n")
        interrupted_panel = create_error_banner(
            title="⌨️  Setup Cancelled",
            message="Setup was interrupted by user",
            suggestions=["Run 'claude-setup init' again to restart the setup process"],
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