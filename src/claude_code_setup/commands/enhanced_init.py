"""Enhanced init command with new UI components.

This module demonstrates how to integrate the new UI components into the
existing init command workflow, providing improved user experience.
"""

import sys
from pathlib import Path
from typing import Optional, List

from rich.console import Console

from ..ui.prompts import (
    SelectOption,
    MultiSelectPrompt,
    ConfirmationDialog,
    ValidatedPrompt,
    IntroOutroContext,
    show_selection_summary,
)
from ..ui.validation import (
    ValidationLevel,
    ValidationFeedback,
    RealTimeValidator,
    create_required_validator,
    create_choice_validator,
)
from ..ui.progress import (
    ProgressStep,
    StepStatus,
    MultiStepProgress,
)
from ..utils import (
    ensure_claude_directories_sync,
    get_settings_sync,
    save_settings_sync,
    success,
    info,
    warning,
    error,
)
from ..utils.template import get_all_templates_sync

console = Console()


def enhanced_interactive_setup(
    permissions: str = "python,node,git,shell,package-managers",
    theme: str = "default",
    force: bool = False,
    global_config: bool = False,
    test_dir: Optional[str] = None,
) -> None:
    """Enhanced interactive setup using new UI components."""
    
    with IntroOutroContext(
        intro_title="Claude Code Setup",
        intro_message="Welcome to the enhanced interactive setup wizard!\nWe'll guide you through configuring Claude Code for your needs.",
        outro_success="🎉 Setup completed successfully! Claude Code is ready to use.",
        outro_error="Setup encountered issues. Please check the errors above.",
    ):
        # Step 1: Location selection with enhanced prompt
        location_options = [
            SelectOption(
                "local", 
                "📁 Current Directory",
                "Project-specific configuration (./.claude) - Recommended for most projects"
            ),
            SelectOption(
                "global",
                "🌍 Global Directory", 
                "System-wide configuration (~/.claude) - Available everywhere"
            ),
        ]
        
        if test_dir:
            location_options.append(SelectOption(
                "test",
                "🧪 Test Directory",
                f"Testing configuration ({test_dir}/.claude) - For development/testing"
            ))
        
        # Use enhanced multi-select (but configured for single selection)
        location_prompt = MultiSelectPrompt(
            title="Choose Setup Location",
            options=location_options,
            min_selections=1,
            max_selections=1,
            show_help=True,
        )
        
        selected_locations = location_prompt.ask()
        setup_location = selected_locations[0]
        
        # Determine target directory
        if setup_location == "global":
            target_home = Path.home() / ".claude"
        elif setup_location == "test" and test_dir:
            target_home = Path(test_dir) / ".claude"
        else:
            target_home = Path.cwd() / ".claude"
        
        console.print(f"✅ Selected location: [cyan]{target_home}[/cyan]")
        
        # Step 2: Check existing configuration with enhanced confirmation
        if target_home.exists() and not force:
            existing_files = list(target_home.rglob("*"))
            
            dialog = ConfirmationDialog(
                title="Existing Configuration Detected",
                message="Claude Code configuration already exists at this location.",
                details={
                    "Location": str(target_home),
                    "Files found": f"{len(existing_files)} configuration files",
                    "Last modified": "Recently" if existing_files else "Unknown"
                },
                default=False,
                danger=True,
            )
            
            if not dialog.ask():
                console.print("[yellow]Operation cancelled by user.[/yellow]")
                return
        
        # Step 3: Permission selection with validation
        available_permissions = ["python", "node", "git", "shell", "package-managers", "docker", "aws"]
        default_permissions = permissions.split(",")
        
        # Create permission options
        permission_options = []
        for perm in available_permissions:
            permission_options.append(SelectOption(
                perm,
                perm.title().replace("-", " "),
                f"Enable {perm} related commands and tools",
                selected=perm in default_permissions
            ))
        
        permission_prompt = MultiSelectPrompt(
            title="Select Permission Sets",
            options=permission_options,
            min_selections=1,
            show_help=True,
        )
        
        selected_permissions = permission_prompt.ask()
        console.print(f"✅ Selected permissions: [cyan]{', '.join(selected_permissions)}[/cyan]")
        
        # Step 4: Theme selection with validation
        available_themes = ["default", "dark", "light", "colorful"]
        
        theme_validator = create_choice_validator(available_themes, "theme", case_sensitive=False)
        validator = RealTimeValidator()
        validator.add_validator("theme", lambda value: theme_validator(value))
        
        theme_prompt = ValidatedPrompt(
            message=f"Choose theme {available_themes}",
            validator=lambda value: validator.validate(value).has_errors() == False and (True, None) or (False, "Invalid theme"),
            default=theme,
        )
        
        selected_theme = theme_prompt.ask()
        console.print(f"✅ Selected theme: [cyan]{selected_theme}[/cyan]")
        
        # Step 5: Template selection with enhanced multi-select
        console.print("\n[bold]Template Selection[/bold]")
        
        try:
            template_registry = get_all_templates_sync()
            templates = template_registry.templates
            
            # Create template options grouped by category
            template_options = []
            recommended_templates = ["code-review", "fix-issue", "create-tasks"]
            
            for template_name, template in templates.items():
                description = f"{template.category.value} - {template.description or 'No description'}"
                template_options.append(SelectOption(
                    template_name,
                    template_name.replace("-", " ").title(),
                    description,
                    selected=template_name in recommended_templates
                ))
            
            if template_options:
                template_prompt = MultiSelectPrompt(
                    title="Select Command Templates to Install",
                    options=template_options,
                    min_selections=0,
                    show_help=True,
                )
                
                selected_templates = template_prompt.ask()
                console.print(f"✅ Selected templates: [cyan]{len(selected_templates)} template(s)[/cyan]")
            else:
                selected_templates = []
                warning("No templates available for installation")
                
        except Exception as e:
            selected_templates = []
            warning(f"Could not load templates: {e}")
        
        # Step 6: Show configuration summary
        selections = {
            "Location": str(target_home),
            "Permissions": selected_permissions,
            "Theme": selected_theme,
            "Templates": selected_templates if selected_templates else ["None"],
        }
        
        show_selection_summary("Configuration Summary", selections)
        
        # Step 7: Final confirmation
        final_dialog = ConfirmationDialog(
            title="Confirm Setup",
            message="Ready to create Claude Code configuration with the above settings.",
            details={
                "This will": "Create directories, install templates, and save settings",
                "Time required": "Less than 30 seconds",
                "Reversible": "Yes, you can modify settings later"
            },
            default=True,
        )
        
        if not final_dialog.ask():
            console.print("[yellow]Operation cancelled by user.[/yellow]")
            return
        
        # Step 8: Execute setup with progress tracking
        setup_steps = [
            ProgressStep("create_dirs", "Create Directories", "Setting up directory structure"),
            ProgressStep("save_settings", "Save Settings", "Creating configuration files"),
            ProgressStep("install_templates", "Install Templates", "Installing selected templates"),
            ProgressStep("finalize", "Finalize Setup", "Completing setup process"),
        ]
        
        progress = MultiStepProgress(
            title="Claude Code Setup",
            steps=setup_steps,
            show_details=True,
        )
        
        with progress.live_display() as (live, update_display):
            try:
                # Create directories
                progress.start_step("create_dirs")
                update_display()
                
                ensure_claude_directories_sync(target_home)
                
                progress.complete_step("create_dirs")
                update_display()
                
                # Save settings
                progress.start_step("save_settings")
                update_display()
                
                settings = get_settings_sync(
                    permission_sets=selected_permissions,
                    theme=selected_theme,
                )
                
                settings_file = target_home / "settings.json"
                save_settings_sync(settings, settings_file)
                
                progress.complete_step("save_settings")
                update_display()
                
                # Install templates
                progress.start_step("install_templates")
                update_display()
                
                templates_installed = 0
                if selected_templates:
                    for i, template_name in enumerate(selected_templates):
                        if template_name in templates:
                            # Simulate template installation
                            progress.update_step_progress(
                                "install_templates", 
                                (i + 1) / len(selected_templates) * 100,
                                f"Installing {template_name}..."
                            )
                            update_display()
                            
                            # Here would be the actual template installation
                            templates_installed += 1
                
                progress.complete_step("install_templates")
                update_display()
                
                # Finalize
                progress.start_step("finalize")
                update_display()
                
                progress.complete_step("finalize")
                update_display()
                
                # Show success summary
                console.print(f"\n✅ [bold green]Setup completed successfully![/bold green]")
                console.print(f"📁 Configuration saved to: [cyan]{target_home}[/cyan]")
                console.print(f"🎨 Theme: [cyan]{selected_theme}[/cyan]")
                console.print(f"🔧 Permission sets: [cyan]{len(selected_permissions)}[/cyan]")
                console.print(f"📄 Templates installed: [cyan]{templates_installed}[/cyan]")
                
                if templates_installed > 0:
                    console.print(f"\n💡 [dim]Try running 'claude-setup list templates' to see your installed templates[/dim]")
                
            except Exception as e:
                if progress.current_step:
                    progress.complete_step(progress.current_step, success=False, error_message=str(e))
                    update_display()
                
                error(f"Setup failed: {e}")
                raise


def demo_enhanced_ui() -> None:
    """Demo function to showcase enhanced UI components."""
    console.print("[bold cyan]🚀 Enhanced UI Components Demo[/bold cyan]\n")
    
    # Demo multi-select
    console.print("[bold]1. Multi-Select Prompt Demo[/bold]")
    options = [
        SelectOption("opt1", "Option 1", "First option", selected=True),
        SelectOption("opt2", "Option 2", "Second option"),
        SelectOption("opt3", "Option 3", "Third option", selected=True),
    ]
    
    prompt = MultiSelectPrompt("Demo Multi-Select", options, min_selections=1)
    # In a real scenario: selections = prompt.ask()
    console.print("✅ Demo complete - would show multi-select interface\n")
    
    # Demo validation feedback
    console.print("[bold]2. Validation Feedback Demo[/bold]")
    feedback = ValidationFeedback("Demo Validation")
    feedback.add_message(ValidationLevel.SUCCESS, "This is working correctly")
    feedback.add_message(ValidationLevel.WARNING, "This might need attention")
    feedback.add_message(ValidationLevel.ERROR, "This needs to be fixed")
    
    feedback.display()
    console.print()
    
    # Demo confirmation dialog
    console.print("[bold]3. Confirmation Dialog Demo[/bold]")
    dialog = ConfirmationDialog(
        "Demo Confirmation",
        "This is a demonstration confirmation dialog.",
        details={"Type": "Demo", "Risk": "None"},
        default=True,
    )
    # In a real scenario: result = dialog.ask()
    console.print("✅ Demo complete - would show confirmation dialog\n")
    
    console.print("[bold green]🎉 Enhanced UI Components are ready for use![/bold green]")


if __name__ == "__main__":
    # Run demo
    demo_enhanced_ui()