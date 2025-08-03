"""Logging utilities for claude-code-setup.

This module provides logging functionality with styled console output,
converted from TypeScript logger.ts. Uses Python logging infrastructure
with rich console formatting.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

from ..ui.styles import create_console, COLORS, style_status

# Initialize rich console for styled output
console = create_console()

# Logger instance
_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """Get or create the claude-code-setup logger.
    
    Returns:
        Configured logger instance
    """
    global _logger
    
    if _logger is None:
        _logger = logging.getLogger("claude-code-setup")
        _logger.setLevel(logging.INFO)
        
        # Only add handler if none exists (prevents duplicate handlers)
        if not _logger.handlers:
            # Create rich handler for beautiful console output
            handler = RichHandler(
                console=console,
                show_time=False,
                show_path=False,
                markup=True,
            )
            handler.setLevel(logging.INFO)
            
            # Simple format without timestamp (matches original behavior)
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            
            _logger.addHandler(handler)
            _logger.propagate = False
    
    return _logger


def success(message: str) -> None:
    """Log a success message with green checkmark.
    
    Args:
        message: Success message to display
    """
    console.print(f"[{COLORS['success']}]✓ {message}[/{COLORS['success']}]")


def info(message: str) -> None:
    """Log an info message with blue info icon.
    
    Args:
        message: Info message to display
    """
    console.print(f"[{COLORS['info']}]ℹ {message}[/{COLORS['info']}]")


def warning(message: str) -> None:
    """Log a warning message with yellow warning icon.
    
    Args:
        message: Warning message to display
    """
    console.print(f"[{COLORS['warning']}]⚠ {message}[/{COLORS['warning']}]")


def error(message: str) -> None:
    """Log an error message with red error icon.
    
    Args:
        message: Error message to display
    """
    # Use stderr console for error messages
    from ..ui.styles import error_console
    error_console.print(f"[{COLORS['error']}]✗ {message}[/{COLORS['error']}]")


def highlight(message: str) -> None:
    """Log a highlighted message with cyan arrow.
    
    Args:
        message: Message to highlight
    """
    console.print(f"[{COLORS['primary']}]→ {message}[/{COLORS['primary']}]")


def debug(message: str) -> None:
    """Log a debug message (only shown in debug mode).
    
    Args:
        message: Debug message to display
    """
    logger = get_logger()
    logger.debug(f"[{COLORS['muted']}]🐛 {message}[/{COLORS['muted']}]")


def set_debug_mode(enabled: bool = True) -> None:
    """Enable or disable debug logging.
    
    Args:
        enabled: Whether to enable debug logging
    """
    logger = get_logger()
    if enabled:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        for handler in logger.handlers:
            handler.setLevel(logging.INFO)


def configure_file_logging(log_file: Optional[Path] = None) -> None:
    """Configure file logging in addition to console output.
    
    Args:
        log_file: Optional path to log file. If None, uses ~/.claude/claude-setup.log
    """
    logger = get_logger()
    
    if log_file is None:
        from .fs import CLAUDE_HOME
        log_file = CLAUDE_HOME / "claude-setup.log"
    
    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    
    # More detailed format for file logging
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(file_handler)


def log_command_execution(command: str, success: bool = True, output: str = "") -> None:
    """Log command execution details.
    
    Args:
        command: Command that was executed
        success: Whether command succeeded
        output: Command output (optional)
    """
    logger = get_logger()
    
    if success:
        logger.info(f"Command executed: {command}")
        if output:
            logger.debug(f"Command output: {output}")
    else:
        logger.error(f"Command failed: {command}")
        if output:
            logger.error(f"Error output: {output}")


def progress_start(message: str) -> None:
    """Start a progress operation.
    
    Args:
        message: Progress message
    """
    console.print(f"[{COLORS['info']}]⏳ {message}...[/{COLORS['info']}]")


def progress_success(message: str) -> None:
    """Complete a progress operation successfully.
    
    Args:
        message: Completion message
    """
    console.print(f"[{COLORS['success']}]✅ {message}[/{COLORS['success']}]")


def progress_error(message: str) -> None:
    """Complete a progress operation with error.
    
    Args:
        message: Error message
    """
    # Use stderr console for error messages
    from ..ui.styles import error_console
    error_console.print(f"[{COLORS['error']}]❌ {message}[/{COLORS['error']}]")