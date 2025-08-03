"""Tests for UI styling utilities."""

import pytest
from rich.text import Text
from rich.panel import Panel
from rich.rule import Rule

from claude_code_setup.ui.styles import (
    create_gradient_text,
    create_ascii_art_banner,
    format_error,
    create_command_error,
    create_validation_error,
    style_command_output,
    create_divider,
    create_welcome_banner,
    create_success_banner,
    create_error_banner,
    create_step_indicator,
    style_header,
    style_status,
    COLORS,
)


class TestGradientText:
    """Test gradient text creation."""
    
    def test_gradient_text_default_colors(self) -> None:
        """Test gradient text with default colors."""
        result = create_gradient_text("Hello World")
        assert isinstance(result, Text)
        assert str(result) == "Hello World"
        # Check that colors are applied
        assert len(result._spans) > 0
    
    def test_gradient_text_custom_colors(self) -> None:
        """Test gradient text with custom colors."""
        result = create_gradient_text("Test", colors=["red", "blue"])
        assert isinstance(result, Text)
        assert str(result) == "Test"
    
    def test_gradient_text_with_style(self) -> None:
        """Test gradient text with additional style."""
        result = create_gradient_text("Bold", style="bold")
        assert isinstance(result, Text)
        assert "bold" in str(result._spans[0].style)
    
    def test_gradient_text_empty_colors(self) -> None:
        """Test gradient text with empty colors list."""
        result = create_gradient_text("Plain", colors=[])
        assert isinstance(result, Text)
        assert str(result) == "Plain"


class TestASCIIArtBanner:
    """Test ASCII art banner creation."""
    
    def test_ascii_banner_default(self) -> None:
        """Test ASCII banner with default values."""
        result = create_ascii_art_banner()
        assert isinstance(result, Panel)
        assert "CLAUDE SETUP" in str(result.renderable)
    
    def test_ascii_banner_custom_title(self) -> None:
        """Test ASCII banner with custom title."""
        result = create_ascii_art_banner(title="Custom Title")
        assert isinstance(result, Panel)
        assert "CUSTOM TITLE" in str(result.renderable)
    
    def test_ascii_banner_with_subtitle(self) -> None:
        """Test ASCII banner with subtitle."""
        result = create_ascii_art_banner(subtitle="Test subtitle")
        assert isinstance(result, Panel)
        assert "Test subtitle" in str(result.renderable)


class TestErrorFormatting:
    """Test error formatting utilities."""
    
    def test_format_error_basic(self) -> None:
        """Test basic error formatting."""
        error = ValueError("Test error message")
        result = format_error(error)
        assert isinstance(result, Panel)
        # Panel content is a string representation
        content = str(result.renderable)
        assert "Test error message" in content
        assert "ValueError" in content
    
    def test_format_error_with_suggestions(self) -> None:
        """Test error formatting with suggestions."""
        error = RuntimeError("Something went wrong")
        result = format_error(
            error,
            title="Custom Error",
            suggestions=["Try this", "Or that"],
        )
        assert isinstance(result, Panel)
        content = str(result.renderable)
        assert "Custom Error" in content
        assert "Try this" in content
        assert "Or that" in content
    
    def test_format_error_with_traceback(self) -> None:
        """Test error formatting with traceback."""
        try:
            raise Exception("Test exception")
        except Exception as e:
            result = format_error(e, show_traceback=True)
            assert isinstance(result, Panel)
            content = str(result.renderable)
            assert "Location" in content
    
    def test_command_error(self) -> None:
        """Test command error formatting."""
        error = Exception("Command failed")
        result = create_command_error("test-cmd", error)
        assert isinstance(result, Panel)
        content = str(result.renderable)
        assert "test-cmd" in content
        assert "Command failed" in content
        assert "claude-setup test-cmd --help" in content
    
    def test_command_error_with_suggestions(self) -> None:
        """Test command error with custom suggestions."""
        error = Exception("Failed")
        result = create_command_error(
            "init",
            error,
            suggestions=["Check permissions"],
        )
        content = str(result.renderable)
        assert "Check permissions" in content
        assert "claude-setup init --help" in content
    
    def test_validation_error(self) -> None:
        """Test validation error formatting."""
        result = create_validation_error(
            "email",
            "not-an-email",
            "Invalid email format",
            suggestions=["Use format: user@example.com"],
        )
        assert isinstance(result, Panel)
        content = str(result.renderable)
        assert "email" in content
        assert "not-an-email" in content
        assert "Invalid email format" in content
        assert "user@example.com" in content


class TestCommandOutput:
    """Test command output styling."""
    
    def test_style_command_output_info(self) -> None:
        """Test styling command output as info."""
        result = style_command_output("Info message", status="info")
        assert isinstance(result, Panel)
        assert result.border_style == COLORS["info"]
    
    def test_style_command_output_success(self) -> None:
        """Test styling command output as success."""
        result = style_command_output("Success!", status="success")
        assert isinstance(result, Panel)
        assert result.border_style == COLORS["success"]
    
    def test_style_command_output_with_title(self) -> None:
        """Test styling command output with title."""
        result = style_command_output(
            "Output text",
            status="warning",
            title="Warning Output",
        )
        assert isinstance(result, Panel)
        assert result.title == "Warning Output"
        assert result.border_style == COLORS["warning"]


class TestDivider:
    """Test divider creation."""
    
    def test_create_divider_simple(self) -> None:
        """Test simple divider creation."""
        result = create_divider()
        assert isinstance(result, Rule)
        assert result.style == COLORS["muted"]
    
    def test_create_divider_with_text(self) -> None:
        """Test divider with text."""
        result = create_divider(text="Section Break")
        assert isinstance(result, Rule)
        assert result.title == "Section Break"
    
    def test_create_divider_custom_style(self) -> None:
        """Test divider with custom style."""
        result = create_divider(style="bold red")
        assert isinstance(result, Rule)
        assert result.style == "bold red"


class TestExistingUtilities:
    """Test existing styling utilities."""
    
    def test_style_header(self) -> None:
        """Test header styling."""
        result = style_header("Header Text", level=1)
        assert isinstance(result, Text)
        assert str(result) == "Header Text"
        assert result.style == COLORS["header"]
        
        result2 = style_header("Subheader", level=2)
        assert result2.style == COLORS["subheader"]
    
    def test_style_status(self) -> None:
        """Test status styling."""
        result = style_status("Success", "success")
        assert isinstance(result, Text)
        assert result.style == COLORS["success"]
        
        result2 = style_status("Error", "error")
        assert result2.style == COLORS["error"]
    
    def test_create_step_indicator(self) -> None:
        """Test step indicator creation."""
        result = create_step_indicator(2, 5, "Processing")
        assert isinstance(result, Text)
        assert "Step 2 of 5" in str(result)
        assert "Processing" in str(result)
    
    def test_create_welcome_banner(self) -> None:
        """Test welcome banner creation."""
        result = create_welcome_banner()
        assert isinstance(result, Panel)
        assert "Claude Code Setup" in str(result.renderable)
    
    def test_create_success_banner(self) -> None:
        """Test success banner creation."""
        result = create_success_banner(
            message="Operation completed",
            details={"Files": "10", "Time": "2s"},
        )
        assert isinstance(result, Panel)
        content = str(result.renderable)
        assert "Success" in content
        assert "Operation completed" in content
        assert "Files" in content
        assert "10" in content
    
    def test_create_error_banner(self) -> None:
        """Test error banner creation."""
        result = create_error_banner(
            message="Operation failed",
            details={"Code": "404"},
            suggestions=["Check the URL"],
        )
        assert isinstance(result, Panel)
        content = str(result.renderable)
        assert "Error" in content
        assert "Operation failed" in content
        assert "404" in content
        assert "Check the URL" in content