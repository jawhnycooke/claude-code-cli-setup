"""Enhanced prompt components for interactive workflows.

This module provides advanced prompt types including multi-select,
confirmation dialogs, validated prompts, and intro/outro flows.
"""

import sys
from typing import List, Optional, Dict, Any, Callable, Union, Tuple
from dataclasses import dataclass
from contextlib import contextmanager

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.align import Align

console = Console()


@dataclass
class SelectOption:
    """Represents an option in a multi-select prompt."""
    value: str
    label: str
    description: Optional[str] = None
    selected: bool = False
    enabled: bool = True


class MultiSelectPrompt:
    """Advanced multi-select prompt with keyboard navigation and visual feedback."""
    
    def __init__(
        self,
        title: str,
        options: List[SelectOption],
        min_selections: int = 0,
        max_selections: Optional[int] = None,
        show_help: bool = True,
    ) -> None:
        """Initialize multi-select prompt.
        
        Args:
            title: Prompt title
            options: List of selectable options
            min_selections: Minimum required selections
            max_selections: Maximum allowed selections
            show_help: Whether to show help text
        """
        self.title = title
        self.options = options
        self.min_selections = min_selections
        self.max_selections = max_selections
        self.show_help = show_help
    
    def ask(self) -> List[str]:
        """Show multi-select prompt and return selected values."""
        console.print(f"\n[bold cyan]{self.title}[/bold cyan]")
        
        if self.show_help:
            help_text = (
                "[dim]Use space to toggle selection, enter to confirm, "
                "or enter comma-separated numbers[/dim]"
            )
            console.print(help_text)
        
        # Show options table
        table = Table(show_header=False, box=None, pad_edge=False)
        table.add_column("Selection", style="cyan", width=12)
        table.add_column("Option", min_width=20)
        table.add_column("Description", style="dim")
        
        for i, option in enumerate(self.options, 1):
            if not option.enabled:
                continue
                
            selection_marker = "✓" if option.selected else " "
            selection_text = f"[{'green' if option.selected else 'white'}]{i:2d}. [{selection_marker}][/{'green' if option.selected else 'white'}]"
            
            label_style = "bold green" if option.selected else "white"
            label_text = f"[{label_style}]{option.label}[/{label_style}]"
            
            description = option.description or ""
            table.add_row(selection_text, label_text, description)
        
        console.print(table)
        console.print()
        
        # Get user input
        while True:
            try:
                user_input = Prompt.ask(
                    "Select options (space-separated numbers or 'all'/'none')",
                    default="",
                    show_default=False
                ).strip()
                
                if not user_input:
                    # Use current selections
                    selected = [opt.value for opt in self.options if opt.selected and opt.enabled]
                else:
                    selected = self._parse_selection(user_input)
                
                # Validate selection count
                if len(selected) < self.min_selections:
                    console.print(f"[red]Please select at least {self.min_selections} option(s)[/red]")
                    continue
                
                if self.max_selections and len(selected) > self.max_selections:
                    console.print(f"[red]Please select at most {self.max_selections} option(s)[/red]")
                    continue
                
                return selected
                
            except ValueError as e:
                console.print(f"[red]Invalid selection: {e}[/red]")
                continue
            except KeyboardInterrupt:
                console.print("\n[yellow]Selection cancelled[/yellow]")
                sys.exit(1)
    
    def _parse_selection(self, user_input: str) -> List[str]:
        """Parse user input and return selected values."""
        user_input = user_input.lower().strip()
        
        if user_input == "all":
            return [opt.value for opt in self.options if opt.enabled]
        elif user_input == "none":
            return []
        
        # Parse comma/space separated numbers
        selections = []
        for part in user_input.replace(",", " ").split():
            try:
                index = int(part) - 1
                if 0 <= index < len(self.options) and self.options[index].enabled:
                    selections.append(self.options[index].value)
                else:
                    raise ValueError(f"Invalid option number: {part}")
            except ValueError:
                raise ValueError(f"'{part}' is not a valid option number")
        
        return selections


class ConfirmationDialog:
    """Enhanced confirmation dialog with detailed information and styling."""
    
    def __init__(
        self,
        title: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        default: bool = True,
        danger: bool = False,
    ) -> None:
        """Initialize confirmation dialog.
        
        Args:
            title: Dialog title
            message: Main confirmation message
            details: Optional details to display
            default: Default response
            danger: Whether this is a dangerous action
        """
        self.title = title
        self.message = message
        self.details = details or {}
        self.default = default
        self.danger = danger
    
    def ask(self) -> bool:
        """Show confirmation dialog and return user response."""
        style = "red" if self.danger else "cyan"
        icon = "⚠️" if self.danger else "❓"
        
        # Create panel with confirmation message
        panel_title = f"{icon} {self.title}"
        panel_content = self.message
        
        if self.details:
            panel_content += "\n\n[bold]Details:[/bold]"
            for key, value in self.details.items():
                panel_content += f"\n• [dim]{key}:[/dim] {value}"
        
        panel = Panel(
            panel_content,
            title=panel_title,
            border_style=style,
            padding=(1, 2),
        )
        
        console.print(panel)
        
        prompt_text = f"[{style}]Continue?[/{style}]"
        return Confirm.ask(prompt_text, default=self.default)


class ValidatedPrompt:
    """Prompt with real-time validation and error feedback."""
    
    def __init__(
        self,
        message: str,
        validator: Callable[[str], Tuple[bool, Optional[str]]],
        default: Optional[str] = None,
        password: bool = False,
        show_choices: bool = True,
    ) -> None:
        """Initialize validated prompt.
        
        Args:
            message: Prompt message
            validator: Function that returns (is_valid, error_message)
            default: Default value
            password: Whether to hide input
            show_choices: Whether to show valid choices in error messages
        """
        self.message = message
        self.validator = validator
        self.default = default
        self.password = password
        self.show_choices = show_choices
    
    def ask(self) -> str:
        """Show validated prompt and return validated input."""
        while True:
            try:
                value = Prompt.ask(
                    self.message,
                    default=self.default,
                    password=self.password,
                    show_default=not self.password,
                )
                
                is_valid, error_message = self.validator(value)
                
                if is_valid:
                    return value
                
                if error_message:
                    console.print(f"[red]✗ {error_message}[/red]")
                else:
                    console.print("[red]✗ Invalid input. Please try again.[/red]")
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Input cancelled[/yellow]")
                sys.exit(1)


@contextmanager
def IntroOutroContext(
    intro_title: str,
    intro_message: Optional[str] = None,
    outro_success: str = "Operation completed successfully!",
    outro_error: str = "Operation failed.",
    show_intro: bool = True,
    show_outro: bool = True,
):
    """Context manager for intro/outro flows around operations.
    
    Args:
        intro_title: Title for intro panel
        intro_message: Optional intro message
        outro_success: Success message for outro
        outro_error: Error message for outro
        show_intro: Whether to show intro
        show_outro: Whether to show outro
    """
    if show_intro:
        # Show intro panel
        intro_content = intro_message or f"Starting {intro_title.lower()}..."
        intro_panel = Panel(
            intro_content,
            title=f"🚀 {intro_title}",
            border_style="cyan",
            padding=(1, 2),
        )
        console.print(intro_panel)
        console.print()
    
    success = False
    error_message = None
    
    try:
        yield
        success = True
    except Exception as e:
        error_message = str(e)
        raise
    finally:
        if show_outro:
            # Show outro panel
            if success:
                outro_panel = Panel(
                    outro_success,
                    title="✅ Success",
                    border_style="green",
                    padding=(1, 2),
                )
            else:
                outro_content = outro_error
                if error_message:
                    outro_content += f"\n\n[dim]Error: {error_message}[/dim]"
                
                outro_panel = Panel(
                    outro_content,
                    title="❌ Error",
                    border_style="red",
                    padding=(1, 2),
                )
            
            console.print()
            console.print(outro_panel)


def create_choice_table(
    choices: List[Tuple[str, str, Optional[str]]],
    title: Optional[str] = None,
    selected_indices: Optional[List[int]] = None,
) -> Table:
    """Create a formatted table for displaying choices.
    
    Args:
        choices: List of (value, label, description) tuples
        title: Optional table title
        selected_indices: Indices of pre-selected choices
        
    Returns:
        Formatted Rich table
    """
    table = Table(
        title=title,
        show_header=False,
        box=None,
        pad_edge=False,
    )
    table.add_column("Choice", style="cyan", width=8)
    table.add_column("Description", min_width=30)
    table.add_column("Details", style="dim")
    
    selected_indices = selected_indices or []
    
    for i, (value, label, description) in enumerate(choices, 1):
        is_selected = (i - 1) in selected_indices
        
        choice_style = "bold green" if is_selected else "cyan"
        choice_text = f"[{choice_style}]{i:2d}.[/{choice_style}]"
        
        if is_selected:
            choice_text += " ✓"
        
        label_style = "bold green" if is_selected else "white"
        label_text = f"[{label_style}]{label}[/{label_style}]"
        
        table.add_row(choice_text, label_text, description or "")
    
    return table


def show_selection_summary(
    title: str,
    selections: Dict[str, Union[str, List[str]]],
    style: str = "cyan",
) -> None:
    """Show a summary of user selections.
    
    Args:
        title: Summary title
        selections: Dictionary of selection categories and values
        style: Panel border style
    """
    summary_table = Table(show_header=False, box=None, pad_edge=False)
    summary_table.add_column("Setting", style="bold", width=15)
    summary_table.add_column("Value", style="white")
    
    for key, value in selections.items():
        if isinstance(value, list):
            value_text = ", ".join(value) if value else "None"
        else:
            value_text = str(value)
        
        summary_table.add_row(key, value_text)
    
    panel = Panel(
        summary_table,
        title=f"📋 {title}",
        border_style=style,
        padding=(1, 2),
    )
    
    console.print(panel)