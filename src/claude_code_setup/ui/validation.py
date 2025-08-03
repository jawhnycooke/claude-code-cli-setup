"""Real-time validation and error display components.

This module provides validation feedback, error display, and real-time
input validation for enhanced user experience.
"""

import re
from typing import List, Optional, Dict, Any, Callable, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns

console = Console()


class ValidationLevel(Enum):
    """Validation message levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class ValidationMessage:
    """Represents a validation message."""
    level: ValidationLevel
    message: str
    field: Optional[str] = None
    code: Optional[str] = None


class ValidationFeedback:
    """Real-time validation feedback display."""
    
    def __init__(
        self,
        title: str = "Validation Results",
        show_success: bool = True,
        console_obj: Optional[Console] = None,
    ) -> None:
        """Initialize validation feedback display.
        
        Args:
            title: Feedback panel title
            show_success: Whether to show success messages
            console_obj: Console instance to use
        """
        self.title = title
        self.show_success = show_success
        self.console = console_obj or console
        self.messages: List[ValidationMessage] = []
    
    def add_message(
        self,
        level: ValidationLevel,
        message: str,
        field: Optional[str] = None,
        code: Optional[str] = None,
    ) -> None:
        """Add a validation message.
        
        Args:
            level: Message level
            message: Message text
            field: Field name (optional)
            code: Error code (optional)
        """
        self.messages.append(ValidationMessage(level, message, field, code))
    
    def clear_messages(self, level: Optional[ValidationLevel] = None) -> None:
        """Clear validation messages.
        
        Args:
            level: Only clear messages of this level (None for all)
        """
        if level is None:
            self.messages.clear()
        else:
            self.messages = [msg for msg in self.messages if msg.level != level]
    
    def has_errors(self) -> bool:
        """Check if there are any error messages."""
        return any(msg.level == ValidationLevel.ERROR for msg in self.messages)
    
    def has_warnings(self) -> bool:
        """Check if there are any warning messages."""
        return any(msg.level == ValidationLevel.WARNING for msg in self.messages)
    
    def display(self) -> None:
        """Display validation feedback panel."""
        if not self.messages:
            if self.show_success:
                success_panel = Panel(
                    "✅ All validations passed",
                    title="✅ Validation Success",
                    border_style="green",
                    padding=(1, 2),
                )
                self.console.print(success_panel)
            return
        
        # Group messages by level
        grouped = {level: [] for level in ValidationLevel}
        for msg in self.messages:
            grouped[msg.level].append(msg)
        
        # Create content
        content_parts = []
        
        # Show errors first
        if grouped[ValidationLevel.ERROR]:
            content_parts.append("[bold red]Errors:[/bold red]")
            for msg in grouped[ValidationLevel.ERROR]:
                field_text = f"[dim]{msg.field}:[/dim] " if msg.field else ""
                content_parts.append(f"  ❌ {field_text}{msg.message}")
        
        # Then warnings
        if grouped[ValidationLevel.WARNING]:
            if content_parts:
                content_parts.append("")
            content_parts.append("[bold yellow]Warnings:[/bold yellow]")
            for msg in grouped[ValidationLevel.WARNING]:
                field_text = f"[dim]{msg.field}:[/dim] " if msg.field else ""
                content_parts.append(f"  ⚠️  {field_text}{msg.message}")
        
        # Then info
        if grouped[ValidationLevel.INFO]:
            if content_parts:
                content_parts.append("")
            content_parts.append("[bold blue]Information:[/bold blue]")
            for msg in grouped[ValidationLevel.INFO]:
                field_text = f"[dim]{msg.field}:[/dim] " if msg.field else ""
                content_parts.append(f"  ℹ️  {field_text}{msg.message}")
        
        # Finally success
        if grouped[ValidationLevel.SUCCESS] and self.show_success:
            if content_parts:
                content_parts.append("")
            content_parts.append("[bold green]Success:[/bold green]")
            for msg in grouped[ValidationLevel.SUCCESS]:
                field_text = f"[dim]{msg.field}:[/dim] " if msg.field else ""
                content_parts.append(f"  ✅ {field_text}{msg.message}")
        
        # Determine panel style based on highest severity
        if self.has_errors():
            border_style = "red"
            title_icon = "❌"
        elif self.has_warnings():
            border_style = "yellow"
            title_icon = "⚠️"
        else:
            border_style = "green"
            title_icon = "✅"
        
        panel = Panel(
            "\n".join(content_parts),
            title=f"{title_icon} {self.title}",
            border_style=border_style,
            padding=(1, 2),
        )
        
        self.console.print(panel)


class RealTimeValidator:
    """Real-time input validator with immediate feedback."""
    
    def __init__(self, console_obj: Optional[Console] = None) -> None:
        """Initialize real-time validator.
        
        Args:
            console_obj: Console instance to use
        """
        self.console = console_obj or console
        self.validators: Dict[str, Callable[[str], List[ValidationMessage]]] = {}
    
    def add_validator(
        self,
        name: str,
        validator: Callable[[str], List[ValidationMessage]],
    ) -> None:
        """Add a validator function.
        
        Args:
            name: Validator name
            validator: Function that returns list of validation messages
        """
        self.validators[name] = validator
    
    def validate(self, value: str) -> ValidationFeedback:
        """Validate input value and return feedback.
        
        Args:
            value: Input value to validate
            
        Returns:
            ValidationFeedback with results
        """
        feedback = ValidationFeedback(console_obj=self.console)
        
        for name, validator in self.validators.items():
            try:
                messages = validator(value)
                feedback.messages.extend(messages)
            except Exception as e:
                feedback.add_message(
                    ValidationLevel.ERROR,
                    f"Validator '{name}' failed: {e}",
                    code="VALIDATOR_ERROR"
                )
        
        return feedback


class ErrorDisplay:
    """Enhanced error display with context and suggestions."""
    
    def __init__(self, console_obj: Optional[Console] = None) -> None:
        """Initialize error display.
        
        Args:
            console_obj: Console instance to use
        """
        self.console = console_obj or console
    
    def show_error(
        self,
        title: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        technical_info: Optional[str] = None,
    ) -> None:
        """Display detailed error information.
        
        Args:
            title: Error title
            message: Main error message
            details: Additional error details
            suggestions: Suggested solutions
            technical_info: Technical details for debugging
        """
        content_parts = [message]
        
        if details:
            content_parts.append("")
            content_parts.append("[bold]Details:[/bold]")
            for key, value in details.items():
                content_parts.append(f"• [dim]{key}:[/dim] {value}")
        
        if suggestions:
            content_parts.append("")
            content_parts.append("[bold]Suggestions:[/bold]")
            for i, suggestion in enumerate(suggestions, 1):
                content_parts.append(f"{i}. {suggestion}")
        
        if technical_info:
            content_parts.append("")
            content_parts.append("[bold dim]Technical Details:[/bold dim]")
            content_parts.append(f"[dim]{technical_info}[/dim]")
        
        error_panel = Panel(
            "\n".join(content_parts),
            title=f"❌ {title}",
            border_style="red",
            padding=(1, 2),
        )
        
        self.console.print(error_panel)
    
    def show_warning(
        self,
        title: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        can_continue: bool = True,
    ) -> None:
        """Display warning information.
        
        Args:
            title: Warning title
            message: Main warning message
            details: Additional warning details
            can_continue: Whether operation can continue
        """
        content_parts = [message]
        
        if details:
            content_parts.append("")
            content_parts.append("[bold]Details:[/bold]")
            for key, value in details.items():
                content_parts.append(f"• [dim]{key}:[/dim] {value}")
        
        if can_continue:
            content_parts.append("")
            content_parts.append("[dim]You can continue, but please review the above.[/dim]")
        
        warning_panel = Panel(
            "\n".join(content_parts),
            title=f"⚠️ {title}",
            border_style="yellow",
            padding=(1, 2),
        )
        
        self.console.print(warning_panel)


# Common validators
def create_required_validator(field_name: str) -> Callable[[str], List[ValidationMessage]]:
    """Create a validator that checks if field is not empty."""
    def validator(value: str) -> List[ValidationMessage]:
        if not value.strip():
            return [ValidationMessage(
                ValidationLevel.ERROR,
                f"{field_name} is required",
                field=field_name,
                code="REQUIRED"
            )]
        return []
    return validator


def create_regex_validator(
    pattern: str,
    field_name: str,
    error_message: Optional[str] = None,
) -> Callable[[str], List[ValidationMessage]]:
    """Create a regex pattern validator."""
    compiled_pattern = re.compile(pattern)
    
    def validator(value: str) -> List[ValidationMessage]:
        if not compiled_pattern.match(value):
            message = error_message or f"{field_name} format is invalid"
            return [ValidationMessage(
                ValidationLevel.ERROR,
                message,
                field=field_name,
                code="INVALID_FORMAT"
            )]
        return []
    return validator


def create_choice_validator(
    choices: List[str],
    field_name: str,
    case_sensitive: bool = False,
) -> Callable[[str], List[ValidationMessage]]:
    """Create a validator that checks value is in allowed choices."""
    def validator(value: str) -> List[ValidationMessage]:
        check_value = value if case_sensitive else value.lower()
        check_choices = choices if case_sensitive else [c.lower() for c in choices]
        
        if check_value not in check_choices:
            return [ValidationMessage(
                ValidationLevel.ERROR,
                f"{field_name} must be one of: {', '.join(choices)}",
                field=field_name,
                code="INVALID_CHOICE"
            )]
        return []
    return validator


def create_length_validator(
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    field_name: str = "Field",
) -> Callable[[str], List[ValidationMessage]]:
    """Create a validator that checks string length."""
    def validator(value: str) -> List[ValidationMessage]:
        messages = []
        length = len(value)
        
        if min_length is not None and length < min_length:
            messages.append(ValidationMessage(
                ValidationLevel.ERROR,
                f"{field_name} must be at least {min_length} characters",
                field=field_name,
                code="TOO_SHORT"
            ))
        
        if max_length is not None and length > max_length:
            messages.append(ValidationMessage(
                ValidationLevel.ERROR,
                f"{field_name} must be at most {max_length} characters",
                field=field_name,
                code="TOO_LONG"
            ))
        
        return messages
    return validator