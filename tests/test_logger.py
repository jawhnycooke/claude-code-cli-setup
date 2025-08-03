"""Tests for logging utilities."""

import logging
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from rich.console import Console

from claude_code_setup.utils.logger import (
    configure_file_logging,
    debug,
    error,
    get_logger,
    highlight,
    info,
    log_command_execution,
    progress_error,
    progress_start,
    progress_success,
    set_debug_mode,
    success,
    warning,
)


class TestLogger:
    """Test logger functionality."""

    def test_get_logger_singleton(self):
        """Test that get_logger returns the same instance."""
        logger1 = get_logger()
        logger2 = get_logger()
        
        assert logger1 is logger2
        assert logger1.name == "claude-code-setup"

    def test_get_logger_configuration(self):
        """Test logger is properly configured."""
        logger = get_logger()
        
        assert logger.level == logging.INFO
        assert len(logger.handlers) >= 1
        assert not logger.propagate

    def test_set_debug_mode_enable(self):
        """Test enabling debug mode."""
        logger = get_logger()
        set_debug_mode(True)
        
        assert logger.level == logging.DEBUG

    def test_set_debug_mode_disable(self):
        """Test disabling debug mode."""
        logger = get_logger()
        set_debug_mode(False)
        
        assert logger.level == logging.INFO


class TestConsoleOutput:
    """Test console output functions."""

    @patch("claude_code_setup.utils.logger.console")
    def test_success(self, mock_console):
        """Test success message output."""
        success("Test success message")
        mock_console.print.assert_called_once_with("[green]✓ Test success message[/green]")

    @patch("claude_code_setup.utils.logger.console")
    def test_info(self, mock_console):
        """Test info message output."""
        info("Test info message")
        mock_console.print.assert_called_once_with("[blue]ℹ Test info message[/blue]")

    @patch("claude_code_setup.utils.logger.console")
    def test_warning(self, mock_console):
        """Test warning message output."""
        warning("Test warning message")
        mock_console.print.assert_called_once_with("[yellow]⚠ Test warning message[/yellow]")

    @patch("claude_code_setup.ui.styles.error_console")
    def test_error(self, mock_error_console):
        """Test error message output."""
        error("Test error message")
        mock_error_console.print.assert_called_once_with("[red]✗ Test error message[/red]")

    @patch("claude_code_setup.utils.logger.console")
    def test_highlight(self, mock_console):
        """Test highlight message output."""
        highlight("Test highlight message")
        mock_console.print.assert_called_once_with("[cyan]→ Test highlight message[/cyan]")


class TestProgressMessages:
    """Test progress message functions."""

    @patch("claude_code_setup.utils.logger.console")
    def test_progress_start(self, mock_console):
        """Test progress start message."""
        progress_start("Installing packages")
        mock_console.print.assert_called_once_with("[blue]⏳ Installing packages...[/blue]")

    @patch("claude_code_setup.utils.logger.console")
    def test_progress_success(self, mock_console):
        """Test progress success message."""
        progress_success("Packages installed")
        mock_console.print.assert_called_once_with("[green]✅ Packages installed[/green]")

    @patch("claude_code_setup.ui.styles.error_console")
    def test_progress_error(self, mock_error_console):
        """Test progress error message."""
        progress_error("Installation failed")
        mock_error_console.print.assert_called_once_with("[red]❌ Installation failed[/red]")


class TestFileLogging:
    """Test file logging functionality."""

    def test_configure_file_logging_custom_path(self):
        """Test configuring file logging with custom path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            
            configure_file_logging(log_file)
            
            logger = get_logger()
            logger.info("Test log message")
            
            assert log_file.exists()
            content = log_file.read_text()
            assert "Test log message" in content

    def test_configure_file_logging_default_path(self):
        """Test configuring file logging with default path."""
        with patch("claude_code_setup.utils.fs.CLAUDE_HOME") as mock_home:
            with tempfile.TemporaryDirectory() as temp_dir:
                mock_home.__truediv__ = lambda self, other: Path(temp_dir) / other
                
                configure_file_logging()
                
                logger = get_logger()
                logger.info("Test default log message")
                
                # File should be created in the temp directory
                log_files = list(Path(temp_dir).glob("*.log"))
                assert len(log_files) > 0


class TestCommandLogging:
    """Test command execution logging."""

    @patch("claude_code_setup.utils.logger.get_logger")
    def test_log_command_execution_success(self, mock_get_logger):
        """Test logging successful command execution."""
        mock_logger = mock_get_logger.return_value
        
        log_command_execution("npm install", success=True, output="packages installed")
        
        mock_logger.info.assert_called_with("Command executed: npm install")
        mock_logger.debug.assert_called_with("Command output: packages installed")

    @patch("claude_code_setup.utils.logger.get_logger")
    def test_log_command_execution_failure(self, mock_get_logger):
        """Test logging failed command execution."""
        mock_logger = mock_get_logger.return_value
        
        log_command_execution("npm install", success=False, output="network error")
        
        mock_logger.error.assert_any_call("Command failed: npm install")
        mock_logger.error.assert_any_call("Error output: network error")

    @patch("claude_code_setup.utils.logger.get_logger")
    def test_log_command_execution_no_output(self, mock_get_logger):
        """Test logging command execution without output."""
        mock_logger = mock_get_logger.return_value
        
        log_command_execution("ls", success=True)
        
        mock_logger.info.assert_called_once_with("Command executed: ls")
        mock_logger.debug.assert_not_called()


class TestDebugLogging:
    """Test debug logging functionality."""

    @patch("claude_code_setup.utils.logger.get_logger")
    def test_debug_message(self, mock_get_logger):
        """Test debug message logging."""
        mock_logger = mock_get_logger.return_value
        
        debug("Debug information")
        
        mock_logger.debug.assert_called_once_with("[dim]🐛 Debug information[/dim]")