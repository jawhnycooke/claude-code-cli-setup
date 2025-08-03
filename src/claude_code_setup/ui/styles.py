"""Centralized style configuration for Rich console output.

This module provides consistent styling across all Claude Code Setup commands,
ensuring a cohesive visual experience throughout the application.
"""

from typing import Optional, Dict, Any, List, Callable
from rich.console import Console
from rich.theme import Theme
from rich.style import Style
from rich.panel import Panel
from rich.table import Table
from rich.box import Box, ROUNDED, MINIMAL, HEAVY, DOUBLE
from rich.text import Text
from rich.align import Align
from rich.rule import Rule
from rich.columns import Columns


# Theme color palette
COLORS = {
    # Primary colors
    "primary": "cyan",
    "secondary": "magenta",
    "accent": "yellow",
    
    # Status colors
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "info": "blue",
    
    # UI colors
    "header": "bold cyan",
    "subheader": "cyan",
    "muted": "dim",
    "highlight": "bold yellow",
    
    # Component colors
    "panel_border": "cyan",
    "table_border": "cyan",
    "prompt": "cyan",
    "selection": "bold cyan",
}

# Box styles for different contexts
BOX_STYLES = {
    "default": ROUNDED,
    "minimal": MINIMAL,
    "prominent": HEAVY,
    "special": DOUBLE,
}

# Create custom theme
CLAUDE_THEME = Theme({
    # Headers and titles
    "header": Style(color="cyan", bold=True),
    "subheader": Style(color="cyan"),
    
    # Status styles
    "success": Style(color="green"),
    "warning": Style(color="yellow"),
    "error": Style(color="red", bold=True),
    "info": Style(color="blue"),
    
    # UI elements
    "muted": Style(dim=True),
    "highlight": Style(color="yellow", bold=True),
    "prompt": Style(color="cyan"),
    
    # Component styles
    "panel.border": Style(color="cyan"),
    "table.border": Style(color="cyan"),
})


def create_console(
    force_terminal: Optional[bool] = None,
    force_jupyter: Optional[bool] = None,
    stderr: bool = False,
) -> Console:
    """Create a console instance with consistent styling.
    
    Args:
        force_terminal: Force terminal mode
        force_jupyter: Force Jupyter mode
        stderr: Whether to output to stderr
        
    Returns:
        Configured Console instance
    """
    return Console(
        theme=CLAUDE_THEME,
        force_terminal=force_terminal,
        force_jupyter=force_jupyter,
        stderr=stderr,
    )


def create_panel(
    content: Any,
    *,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    border_style: Optional[str] = None,
    box: Optional[Box] = None,
    expand: bool = True,
    padding: tuple[int, int] = (1, 2),
    style: Optional[str] = None,
) -> Panel:
    """Create a panel with consistent styling.
    
    Args:
        content: Panel content
        title: Panel title
        subtitle: Panel subtitle
        border_style: Border color style
        box: Box style to use
        expand: Whether to expand to full width
        padding: Padding (vertical, horizontal)
        style: Panel style
        
    Returns:
        Styled Panel instance
    """
    panel_kwargs = {
        "title": title,
        "subtitle": subtitle,
        "border_style": border_style or COLORS["panel_border"],
        "box": box or BOX_STYLES["default"],
        "expand": expand,
        "padding": padding,
    }
    
    # Only add style if it's not None
    if style is not None:
        panel_kwargs["style"] = style
    
    return Panel(content, **panel_kwargs)


def create_table(
    *,
    title: Optional[str] = None,
    caption: Optional[str] = None,
    show_header: bool = True,
    show_footer: bool = False,
    show_edge: bool = True,
    show_lines: bool = False,
    box: Optional[Box] = None,
    border_style: Optional[str] = None,
    header_style: Optional[str] = None,
    title_style: Optional[str] = None,
    caption_style: Optional[str] = None,
    expand: bool = False,
    width: Optional[int] = None,
) -> Table:
    """Create a table with consistent styling.
    
    Args:
        title: Table title
        caption: Table caption
        show_header: Whether to show header
        show_footer: Whether to show footer
        show_edge: Whether to show edge
        show_lines: Whether to show lines between rows
        box: Box style to use
        border_style: Border color style
        header_style: Header row style
        title_style: Title style
        caption_style: Caption style
        expand: Whether to expand to full width
        width: Fixed width
        
    Returns:
        Styled Table instance
    """
    return Table(
        title=title,
        caption=caption,
        show_header=show_header,
        show_footer=show_footer,
        show_edge=show_edge,
        show_lines=show_lines,
        box=box or BOX_STYLES["default"],
        border_style=border_style or COLORS["table_border"],
        header_style=header_style or "bold",
        title_style=title_style or COLORS["header"],
        caption_style=caption_style or COLORS["muted"],
        expand=expand,
        width=width,
    )


def style_header(text: str, level: int = 1) -> Text:
    """Style text as a header.
    
    Args:
        text: Header text
        level: Header level (1-3)
        
    Returns:
        Styled Text instance
    """
    styles = {
        1: COLORS["header"],
        2: COLORS["subheader"],
        3: "bold",
    }
    
    style = styles.get(level, "bold")
    return Text(text, style=style)


def style_status(text: str, status: str) -> Text:
    """Style text with status color.
    
    Args:
        text: Text to style
        status: Status type (success, warning, error, info)
        
    Returns:
        Styled Text instance
    """
    status_map = {
        "success": COLORS["success"],
        "warning": COLORS["warning"],
        "error": COLORS["error"],
        "info": COLORS["info"],
    }
    
    style = status_map.get(status, "default")
    return Text(text, style=style)


def create_welcome_banner(
    title: str = "🤖 Claude Code Setup",
    subtitle: str = "Interactive setup wizard to configure Claude Code for your needs",
) -> Panel:
    """Create a welcome banner with consistent styling.
    
    Args:
        title: Banner title
        subtitle: Banner subtitle
        
    Returns:
        Styled welcome banner
    """
    content = Align.center(
        f"[{COLORS['header']}]{title}[/{COLORS['header']}]\n"
        f"[{COLORS['muted']}]{subtitle}[/{COLORS['muted']}]"
    )
    
    return create_panel(
        content,
        box=BOX_STYLES["prominent"],
        border_style=COLORS["primary"],
        padding=(1, 2),
    )


def create_success_banner(
    title: str = "🎉 Success!",
    message: str = "",
    details: Optional[Dict[str, str]] = None,
) -> Panel:
    """Create a success banner with consistent styling.
    
    Args:
        title: Banner title
        message: Success message
        details: Additional details to display
        
    Returns:
        Styled success banner
    """
    content_lines = [f"[{COLORS['success']} bold]{title}[/{COLORS['success']} bold]"]
    
    if message:
        content_lines.append(f"\n{message}")
    
    if details:
        content_lines.append("")
        for key, value in details.items():
            content_lines.append(f"[{COLORS['muted']}]{key}:[/{COLORS['muted']}] {value}")
    
    content = Align.center("\n".join(content_lines))
    
    return create_panel(
        content,
        border_style=COLORS["success"],
        box=BOX_STYLES["prominent"],
        padding=(1, 2),
    )


def create_error_banner(
    title: str = "❌ Error",
    message: str = "",
    details: Optional[Dict[str, str]] = None,
    suggestions: Optional[list[str]] = None,
) -> Panel:
    """Create an error banner with consistent styling.
    
    Args:
        title: Banner title
        message: Error message
        details: Additional error details
        suggestions: Suggestions for fixing the error
        
    Returns:
        Styled error banner
    """
    content_lines = [f"[{COLORS['error']} bold]{title}[/{COLORS['error']} bold]"]
    
    if message:
        content_lines.append(f"\n{message}")
    
    if details:
        content_lines.append("")
        for key, value in details.items():
            content_lines.append(f"[{COLORS['muted']}]{key}:[/{COLORS['muted']}] {value}")
    
    if suggestions:
        content_lines.append(f"\n[{COLORS['warning']}]Suggestions:[/{COLORS['warning']}]")
        for suggestion in suggestions:
            content_lines.append(f"  • {suggestion}")
    
    content = "\n".join(content_lines)
    
    return create_panel(
        content,
        border_style=COLORS["error"],
        box=BOX_STYLES["prominent"],
        padding=(1, 2),
    )


def create_step_indicator(current: int, total: int, label: str = "") -> Text:
    """Create a step indicator for multi-step processes.
    
    Args:
        current: Current step number
        total: Total number of steps
        label: Optional label for the step
        
    Returns:
        Styled step indicator
    """
    indicator_text = f"Step {current} of {total}"
    
    if label:
        full_text = f"{indicator_text} - {label}"
    else:
        full_text = indicator_text
    
    return Text(full_text, style=COLORS['highlight'])


def create_gradient_text(
    text: str,
    colors: Optional[List[str]] = None,
    style: Optional[str] = None,
) -> Text:
    """Create text with gradient effect using Rich colors.
    
    Args:
        text: Text to apply gradient to
        colors: List of color names for gradient (default: cyan->magenta->yellow)
        style: Additional style to apply (e.g., "bold")
        
    Returns:
        Text with gradient-like effect
    """
    if colors is None:
        # Default gradient colors matching TypeScript version
        colors = ["red", "cyan", "blue"]
    
    if not colors:
        return Text(text, style=style)
    
    # Create gradient effect by distributing colors across characters
    gradient_text = Text()
    text_len = len(text)
    color_count = len(colors)
    
    for i, char in enumerate(text):
        # Calculate which color to use based on position
        color_index = int((i / text_len) * (color_count - 1))
        color = colors[color_index]
        
        # Apply color and style
        char_style = f"{color} {style}" if style else color
        gradient_text.append(char, style=char_style)
    
    return gradient_text


def create_ascii_art_banner(
    title: str = "Claude Setup",
    subtitle: Optional[str] = None,
    width: int = 80,
) -> Panel:
    """Create an ASCII art-style banner using box characters.
    
    Args:
        title: Main title text
        subtitle: Optional subtitle
        width: Banner width
        
    Returns:
        Styled banner panel
    """
    # Create ASCII-style text using box drawing characters
    lines = []
    
    # Top border
    lines.append("═" * (width - 4))
    
    # Title with large spacing
    title_text = create_gradient_text(title.upper(), style="bold")
    lines.append("")
    lines.append(Align.center(title_text, width=width - 4))
    lines.append("")
    
    # Subtitle if provided
    if subtitle:
        subtitle_text = Text(subtitle, style=COLORS["muted"])
        lines.append(Align.center(subtitle_text, width=width - 4))
        lines.append("")
    
    # Bottom border
    lines.append("═" * (width - 4))
    
    # Create panel with double box style
    content = "\n".join(str(line) for line in lines)
    
    return Panel(
        content,
        box=BOX_STYLES["special"],
        border_style=COLORS["primary"],
        padding=(1, 2),
        expand=False,
        width=width,
    )


def format_error(
    error: Exception,
    title: Optional[str] = None,
    suggestions: Optional[List[str]] = None,
    show_traceback: bool = False,
) -> Panel:
    """Format an exception into a consistent error display.
    
    Args:
        error: The exception to format
        title: Custom error title (default: "Error")
        suggestions: List of suggestions for fixing the error
        show_traceback: Whether to include traceback information
        
    Returns:
        Formatted error panel
    """
    import traceback
    
    error_title = title or "Error"
    error_message = str(error)
    
    # Build error details
    details = {}
    
    # Add exception type
    details["Type"] = type(error).__name__
    
    # Add traceback if requested
    if show_traceback:
        tb_lines = traceback.format_tb(error.__traceback__)
        if tb_lines:
            # Get the most relevant frame (usually the last one)
            last_frame = tb_lines[-1].strip()
            details["Location"] = last_frame
    
    return create_error_banner(
        title=error_title,
        message=error_message,
        details=details,
        suggestions=suggestions,
    )


def create_command_error(
    command: str,
    error: Exception,
    suggestions: Optional[List[str]] = None,
) -> Panel:
    """Create a standardized command error display.
    
    Args:
        command: The command that failed
        error: The exception that occurred
        suggestions: Suggested fixes
        
    Returns:
        Formatted error panel
    """
    default_suggestions = [
        f"Run 'claude-setup {command} --help' for usage information",
        "Check that all required arguments are provided",
        "Ensure you have the necessary permissions",
    ]
    
    all_suggestions = (suggestions or []) + default_suggestions
    
    return format_error(
        error,
        title=f"Command '{command}' failed",
        suggestions=all_suggestions,
        show_traceback=False,
    )


def create_validation_error(
    field: str,
    value: Any,
    reason: str,
    suggestions: Optional[List[str]] = None,
) -> Panel:
    """Create a validation error display.
    
    Args:
        field: The field that failed validation
        value: The invalid value
        reason: Why the validation failed
        suggestions: How to fix it
        
    Returns:
        Formatted error panel
    """
    error_msg = f"Invalid value for '{field}': {value}"
    
    details = {
        "Field": field,
        "Value": repr(value),
        "Reason": reason,
    }
    
    return create_error_banner(
        title="Validation Error",
        message=error_msg,
        details=details,
        suggestions=suggestions,
    )


def style_command_output(
    output: str,
    status: str = "info",
    title: Optional[str] = None,
) -> Panel:
    """Style command output consistently.
    
    Args:
        output: Command output text
        status: Status type (success, error, warning, info)
        title: Optional panel title
        
    Returns:
        Styled output panel
    """
    status_colors = {
        "success": COLORS["success"],
        "error": COLORS["error"],
        "warning": COLORS["warning"],
        "info": COLORS["info"],
    }
    
    border_color = status_colors.get(status, COLORS["info"])
    
    return create_panel(
        output,
        title=title,
        border_style=border_color,
        box=BOX_STYLES["minimal"],
    )


def create_divider(
    text: Optional[str] = None,
    style: Optional[str] = None,
) -> Rule:
    """Create a styled divider line.
    
    Args:
        text: Optional text to display in divider
        style: Style to apply
        
    Returns:
        Styled Rule
    """
    return Rule(
        title=text,
        style=style or COLORS["muted"],
        align="center",
    )


# Default console instances
console = create_console()
error_console = create_console(stderr=True)


# Export all
__all__ = [
    "COLORS",
    "BOX_STYLES", 
    "CLAUDE_THEME",
    "create_console",
    "create_panel",
    "create_table",
    "style_header",
    "style_status",
    "create_welcome_banner",
    "create_success_banner",
    "create_error_banner",
    "create_step_indicator",
    "create_gradient_text",
    "create_ascii_art_banner",
    "format_error",
    "create_command_error",
    "create_validation_error",
    "style_command_output",
    "create_divider",
    "console",
    "error_console",
]