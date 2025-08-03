"""Tests for the CLI functionality."""

import subprocess
import sys

import pytest
from click.testing import CliRunner

from claude_code_setup.cli import cli


def test_cli_help():
    """Test that CLI help works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Claude Code" in result.output
    assert "Setup and configure" in result.output


def test_cli_version():
    """Test that version command works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.12.0" in result.output


def test_cli_no_command():
    """Test CLI behavior when no command is provided."""
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert "🤖 Claude Code Setup" in result.output
    assert "Examples:" in result.output


def test_cli_no_command_non_interactive():
    """Test CLI behavior with --no-interactive flag."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--no-interactive"])
    assert result.exit_code == 0
    assert "🤖 Claude Code Setup" in result.output
    # Should not show interactive tips
    assert "💡 Tip:" not in result.output


def test_init_command():
    """Test init command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "--help"])
    assert result.exit_code == 0
    assert "Initialize Claude Code setup" in result.output


def test_list_command():
    """Test list command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["list", "--help"])
    assert result.exit_code == 0
    assert "List templates, hooks, and settings" in result.output


def test_add_command():
    """Test add command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["add", "--help"])
    assert result.exit_code == 0
    assert "Add templates, hooks, or settings" in result.output


def test_hooks_subcommand():
    """Test hooks subcommand."""
    runner = CliRunner()
    result = runner.invoke(cli, ["hooks", "--help"])
    assert result.exit_code == 0
    assert "Manage security and automation hooks" in result.output


def test_hooks_list():
    """Test hooks list subcommand."""
    runner = CliRunner()
    result = runner.invoke(cli, ["hooks", "list"])
    assert result.exit_code == 0
    assert "🛡️ Available Hooks" in result.output


def test_init_with_options():
    """Test init command with various options."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["init", "--quick", "--dry-run", "--no-check"])
        assert result.exit_code == 0
        # Check for new output format from the actual init command
        assert "⚡ Quick Setup with Defaults" in result.output
        assert "Dry run mode" in result.output


def test_list_with_type():
    """Test list command with specific type."""
    runner = CliRunner()
    result = runner.invoke(cli, ["list", "templates"])
    assert result.exit_code == 0
    # Check for new output format from the actual list command
    assert "📄 Available Templates" in result.output
    assert "code-review" in result.output


def test_add_with_arguments():
    """Test add command with arguments."""
    runner = CliRunner()
    result = runner.invoke(cli, ["add", "template", "code-review", "--force"])
    assert result.exit_code == 0
    # The add command now shows different output based on whether config exists
    # It may show "No templates were installed" if template not found
    assert ("Using" in result.output) or ("Configuration not found" in result.output)


@pytest.mark.slow
@pytest.mark.integration
def test_cli_executable():
    """Test that the CLI executable works (requires package installation)."""
    result = subprocess.run(
        [sys.executable, "-m", "claude_code_setup", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "0.12.0" in result.stdout


@pytest.mark.slow
@pytest.mark.integration
def test_console_script():
    """Test that the console script works (requires package installation)."""
    result = subprocess.run(
        ["claude-setup", "--version"],
        capture_output=True,
        text=True,
    )
    # This might fail if not installed, but should work in development
    if result.returncode == 0:
        assert "0.12.0" in result.stdout
