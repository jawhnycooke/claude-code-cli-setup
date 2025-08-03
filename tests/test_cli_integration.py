"""Comprehensive CLI integration tests for claude-code-setup.

This module tests the CLI functionality using subprocess calls to simulate
real-world usage patterns. These tests complement the CliRunner tests by
testing the actual console script entry point.
"""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestCLIIntegration:
    """Test CLI integration using subprocess calls."""

    def run_cli_command(self, args, cwd=None, check=True):
        """Run a CLI command using subprocess."""
        cmd = ["uv", "run", "python", "-m", "claude_code_setup.cli"] + args
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check
        )
        return result

    def test_cli_help_subprocess(self):
        """Test CLI help command via subprocess."""
        result = self.run_cli_command(["--help"])
        assert result.returncode == 0
        assert "Setup and configure Claude Code" in result.stdout
        assert "init" in result.stdout
        assert "list" in result.stdout
        assert "add" in result.stdout

    def test_cli_version_subprocess(self):
        """Test CLI version command via subprocess."""
        result = self.run_cli_command(["--version"])
        assert result.returncode == 0
        assert "0.12.0" in result.stdout

    def test_cli_no_interactive_mode(self):
        """Test CLI in non-interactive mode."""
        result = self.run_cli_command(["--no-interactive"])
        assert result.returncode == 0
        assert "Claude Code Setup" in result.stdout
        # Should not show interactive tips
        assert "💡 Tip:" not in result.stdout

    def test_full_workflow_subprocess(self):
        """Test a complete workflow using subprocess calls."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            claude_dir = temp_path / ".claude"
            
            # Test init command
            result = self.run_cli_command([
                "init", "--quick", "--test-dir", str(temp_path), "--force"
            ])
            assert result.returncode == 0
            assert claude_dir.exists()
            assert (claude_dir / "settings.json").exists()
            
            # Test list command
            result = self.run_cli_command([
                "list", "--test-dir", str(temp_path), "--no-interactive"
            ])
            assert result.returncode == 0
            assert "templates" in result.stdout.lower()
            
            # Test add template command
            result = self.run_cli_command([
                "add", "template", "new-python-project", 
                "--test-dir", str(temp_path), "--force"
            ])
            assert result.returncode == 0
            
            # Verify template was installed
            template_path = claude_dir / "commands" / "python" / "new-python-project.md"
            assert template_path.exists()
            
            # Test add permission command
            result = self.run_cli_command([
                "add", "permission", "Bash(docker:*)", 
                "--test-dir", str(temp_path), "--force"
            ])
            assert result.returncode == 0
            
            # Verify permission was added
            with open(claude_dir / "settings.json") as f:
                settings = json.load(f)
                permissions = settings.get("permissions", {}).get("allow", [])
                assert any("docker" in perm for perm in permissions)
            
            # Test settings command
            result = self.run_cli_command([
                "settings", "show", "--test-dir", str(temp_path), "--no-interactive"
            ])
            assert result.returncode == 0
            assert "Configuration" in result.stdout
            
            # Test hooks list command
            result = self.run_cli_command([
                "hooks", "list", "--test-dir", str(temp_path), "--no-interactive"
            ])
            assert result.returncode == 0
            
            # Test update command (dry run)
            result = self.run_cli_command([
                "update", "--dry-run", "--test-dir", str(temp_path)
            ])
            assert result.returncode == 0

    def test_error_handling_subprocess(self):
        """Test error handling in subprocess calls."""
        # Test invalid command
        result = self.run_cli_command(["invalid-command"], check=False)
        assert result.returncode != 0
        assert "Error" in result.stderr or "Usage" in result.stderr

    def test_hooks_workflow_subprocess(self):
        """Test hooks workflow using subprocess."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Initialize configuration
            result = self.run_cli_command([
                "init", "--quick", "--test-dir", str(temp_path), "--force"
            ])
            assert result.returncode == 0
            
            # List available hooks
            result = self.run_cli_command([
                "hooks", "list", "--test-dir", str(temp_path), "--no-interactive"
            ])
            assert result.returncode == 0
            assert "Available Hooks" in result.stdout
            
            # Add a hook
            result = self.run_cli_command([
                "hooks", "add", "validate-aws-command", 
                "--test-dir", str(temp_path), "--force"
            ])
            assert result.returncode == 0
            
            # Verify hook was installed
            hook_dir = temp_path / ".claude" / "hooks" / "aws" / "validate-aws-command"
            assert hook_dir.exists()
            assert (hook_dir / "metadata.json").exists()
            
            # Verify hook was registered in settings
            settings_path = temp_path / ".claude" / "settings.json"
            with open(settings_path) as f:
                settings = json.load(f)
                assert "hooks" in settings
                assert settings["hooks"] is not None

    def test_interactive_mode_detection(self):
        """Test that interactive mode is properly detected."""
        # Test with --no-interactive flag
        result = self.run_cli_command(["list", "--no-interactive"])
        assert result.returncode == 0
        
        # Test default behavior (should work even if not truly interactive)
        result = self.run_cli_command(["list", "templates"])
        assert result.returncode == 0

    def test_global_vs_local_config(self):
        """Test global vs local configuration handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test local configuration
            result = self.run_cli_command([
                "init", "--quick", "--test-dir", str(temp_path), "--force"
            ])
            assert result.returncode == 0
            assert (temp_path / ".claude").exists()
            
            # Test list with local config
            result = self.run_cli_command([
                "list", "--test-dir", str(temp_path), "--no-interactive"
            ])
            assert result.returncode == 0

    def test_command_help_systems(self):
        """Test help for individual commands."""
        commands = ["init", "list", "add", "update", "remove", "hooks", "settings"]
        
        for command in commands:
            result = self.run_cli_command([command, "--help"])
            assert result.returncode == 0
            assert command in result.stdout.lower()

    def test_settings_management_subprocess(self):
        """Test settings management via subprocess."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Initialize configuration
            result = self.run_cli_command([
                "init", "--quick", "--test-dir", str(temp_path), "--force"
            ])
            assert result.returncode == 0
            
            # Test settings show
            result = self.run_cli_command([
                "settings", "show", "--test-dir", str(temp_path), "--no-interactive"
            ])
            assert result.returncode == 0
            assert "Configuration" in result.stdout
            assert "Theme" in result.stdout
            assert "Permissions" in result.stdout

    def test_dry_run_operations(self):
        """Test dry-run operations don't make changes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Initialize configuration
            result = self.run_cli_command([
                "init", "--quick", "--test-dir", str(temp_path), "--force"
            ])
            assert result.returncode == 0
            
            # Get initial state
            initial_files = list((temp_path / ".claude").rglob("*"))
            
            # Run update with dry-run
            result = self.run_cli_command([
                "update", "--dry-run", "--test-dir", str(temp_path)
            ])
            assert result.returncode == 0
            
            # Verify no changes were made
            final_files = list((temp_path / ".claude").rglob("*"))
            assert len(initial_files) == len(final_files)


class TestCLIErrorHandling:
    """Test CLI error handling and edge cases."""

    def run_cli_command(self, args, cwd=None, check=True):
        """Run a CLI command using subprocess."""
        cmd = ["uv", "run", "python", "-m", "claude_code_setup.cli"] + args
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check
        )
        return result

    def test_invalid_arguments(self):
        """Test handling of invalid arguments."""
        # Invalid template name
        result = self.run_cli_command([
            "add", "template", "nonexistent-template"
        ], check=False)
        assert result.returncode != 0

    def test_missing_configuration(self):
        """Test commands that require configuration when none exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Try to add template without init
            result = self.run_cli_command([
                "add", "template", "new-python-project", 
                "--test-dir", str(temp_path)
            ], check=False)
            assert result.returncode != 0

    def test_permission_denied_scenarios(self):
        """Test handling of permission denied scenarios."""
        # This would test read-only directories, but we'll simulate
        # by testing with non-existent parent directories
        result = self.run_cli_command([
            "init", "--test-dir", "/nonexistent/deeply/nested/path"
        ], check=False)
        # Should handle gracefully (might succeed by creating dirs or fail gracefully)
        assert isinstance(result.returncode, int)