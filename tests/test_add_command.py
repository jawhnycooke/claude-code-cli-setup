"""Tests for the add command."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from claude_code_setup.cli import cli
from claude_code_setup.commands.add import (
    ResourceType,
    determine_target_directory,
    add_permission,
    run_add_command,
)
from claude_code_setup.types import Template, TemplateCategory, TemplateRegistry


@pytest.fixture
def temp_claude_dir():
    """Create a temporary Claude directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        claude_dir = Path(tmpdir) / ".claude"
        claude_dir.mkdir()
        
        # Create commands directory
        commands_dir = claude_dir / "commands"
        commands_dir.mkdir()
        
        # Create settings.json
        settings = {
            "permissions": {
                "allow": ["Bash(ls:*)", "Bash(cat:*)"]
            }
        }
        settings_file = claude_dir / "settings.json"
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        
        yield claude_dir


@pytest.fixture
def mock_templates():
    """Create mock templates for testing."""
    return {
        "code-review": Template(
            name="code-review",
            description="Code review template",
            category=TemplateCategory.GENERAL,
            content="# Code Review\n\nReview code for quality and best practices."
        ),
        "fix-issue": Template(
            name="fix-issue",
            description="Fix GitHub issues",
            category=TemplateCategory.GENERAL,
            content="# Fix Issue\n\nFix the specified GitHub issue."
        ),
        "python-optimization": Template(
            name="python-optimization",
            description="Optimize Python code",
            category=TemplateCategory.PYTHON,
            content="# Python Optimization\n\nOptimize Python code for performance."
        ),
    }


class TestResourceType:
    """Test ResourceType enum."""
    
    def test_from_string_valid(self):
        """Test converting valid strings to ResourceType."""
        assert ResourceType.from_string("template") == ResourceType.TEMPLATE
        assert ResourceType.from_string("templates") == ResourceType.TEMPLATES
        assert ResourceType.from_string("hook") == ResourceType.HOOK
        assert ResourceType.from_string("permission") == ResourceType.PERMISSION
        
    def test_from_string_case_insensitive(self):
        """Test case-insensitive conversion."""
        assert ResourceType.from_string("TEMPLATE") == ResourceType.TEMPLATE
        assert ResourceType.from_string("Template") == ResourceType.TEMPLATE
        
    def test_from_string_invalid(self):
        """Test invalid string returns None."""
        assert ResourceType.from_string("invalid") is None
        assert ResourceType.from_string("") is None


class TestDetermineTargetDirectory:
    """Test target directory determination."""
    
    def test_test_dir(self, tmp_path):
        """Test using test directory."""
        test_dir = str(tmp_path)
        target = determine_target_directory(test_dir, False)
        assert target == tmp_path / ".claude"
        
    def test_global_dir(self):
        """Test using global directory."""
        from claude_code_setup.utils import CLAUDE_HOME
        target = determine_target_directory(None, True)
        assert target == CLAUDE_HOME
        
    def test_local_dir(self):
        """Test using local directory."""
        target = determine_target_directory(None, False)
        assert target == Path.cwd() / ".claude"


class TestAddPermission:
    """Test permission addition functionality."""
    
    def test_add_new_permission(self, temp_claude_dir):
        """Test adding a new permission."""
        result = add_permission("Bash(docker:*)", temp_claude_dir, False)
        assert result is True
        
        # Verify permission was added
        settings_file = temp_claude_dir / "settings.json"
        with open(settings_file) as f:
            settings = json.load(f)
        
        assert "Bash(docker:*)" in settings["permissions"]["allow"]
        
    def test_add_existing_permission_no_force(self, temp_claude_dir):
        """Test adding existing permission without force."""
        result = add_permission("Bash(ls:*)", temp_claude_dir, False)
        assert result is False
        
    def test_add_existing_permission_with_force(self, temp_claude_dir):
        """Test adding existing permission with force."""
        result = add_permission("Bash(ls:*)", temp_claude_dir, True)
        assert result is True
        
    def test_add_permission_no_settings_file(self, tmp_path):
        """Test adding permission when settings file doesn't exist."""
        result = add_permission("Bash(docker:*)", tmp_path, False)
        assert result is False
        
    def test_add_permission_empty_settings(self, temp_claude_dir):
        """Test adding permission to empty settings."""
        # Create empty settings file
        settings_file = temp_claude_dir / "settings.json"
        with open(settings_file, 'w') as f:
            json.dump({}, f)
        
        result = add_permission("Bash(docker:*)", temp_claude_dir, False)
        assert result is True
        
        # Verify structure was created
        with open(settings_file) as f:
            settings = json.load(f)
        
        assert "permissions" in settings
        assert "allow" in settings["permissions"]
        assert "Bash(docker:*)" in settings["permissions"]["allow"]


class TestAddCommand:
    """Test the add command CLI."""
    
    def test_add_command_help(self):
        """Test add command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["add", "--help"])
        assert result.exit_code == 0
        assert "Add templates, hooks, or settings" in result.output
        
    def test_add_template_direct(self, temp_claude_dir, mock_templates):
        """Test adding a template directly."""
        runner = CliRunner()
        
        with patch('claude_code_setup.commands.add.get_all_templates_sync') as mock_get_templates:
            mock_registry = TemplateRegistry(templates=mock_templates)
            mock_get_templates.return_value = mock_registry
            
            with patch('claude_code_setup.commands.add.install_templates_interactive') as mock_install:
                # Mock successful installation
                from claude_code_setup.utils.template_installer import InstallationReport
                mock_report = InstallationReport(
                    total_requested=1,
                    successful_installs=1,
                    failed_installs=0,
                    skipped_installs=0
                )
                mock_install.return_value = mock_report
                
                result = runner.invoke(cli, [
                    "add", "template", "code-review",
                    "--test-dir", str(temp_claude_dir.parent)
                ])
                
                assert result.exit_code == 0
                mock_install.assert_called_once()
                
    def test_add_permission_direct(self, temp_claude_dir):
        """Test adding a permission directly."""
        runner = CliRunner()
        
        result = runner.invoke(cli, [
            "add", "permission", "Bash(docker:*)",
            "--test-dir", str(temp_claude_dir.parent)
        ])
        
        assert result.exit_code == 0
        assert "Permission added to settings" in result.output
        
        # Verify permission was added
        settings_file = temp_claude_dir / "settings.json"
        with open(settings_file) as f:
            settings = json.load(f)
        assert "Bash(docker:*)" in settings["permissions"]["allow"]
        
    def test_add_invalid_type(self):
        """Test add command with invalid type."""
        runner = CliRunner()
        result = runner.invoke(cli, ["add", "invalid", "value"])
        # Click returns exit code 2 for invalid CLI arguments
        assert result.exit_code == 2
        assert "'invalid' is not one of" in result.output
        
    def test_add_no_config(self, tmp_path):
        """Test add command when configuration doesn't exist."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "add", "template", "code-review",
            "--test-dir", str(tmp_path)
        ])
        assert result.exit_code == 1
        assert "Configuration not found" in result.output
        
    def test_add_hook_not_found(self, temp_claude_dir):
        """Test adding non-existent hook shows error message."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "add", "hook", "test-hook",
            "--test-dir", str(temp_claude_dir.parent)
        ])
        assert result.exit_code == 0
        assert "Hook 'test-hook' not found in registry" in result.output
        
    def test_add_multiple_templates(self, temp_claude_dir, mock_templates):
        """Test adding multiple templates."""
        runner = CliRunner()
        
        with patch('claude_code_setup.commands.add.get_all_templates_sync') as mock_get_templates:
            mock_registry = TemplateRegistry(templates=mock_templates)
            mock_get_templates.return_value = mock_registry
            
            with patch('claude_code_setup.commands.add.install_templates_interactive') as mock_install:
                # Mock successful installation
                from claude_code_setup.utils.template_installer import InstallationReport
                mock_report = InstallationReport(
                    total_requested=2,
                    successful_installs=2,
                    failed_installs=0,
                    skipped_installs=0
                )
                mock_install.return_value = mock_report
                
                result = runner.invoke(cli, [
                    "add", "template", "code-review", "fix-issue",
                    "--test-dir", str(temp_claude_dir.parent)
                ])
                
                assert result.exit_code == 0
                # Should be called with both template names
                call_args = mock_install.call_args[0][0]
                assert "code-review" in call_args
                assert "fix-issue" in call_args


class TestAddCommandInteractive:
    """Test interactive mode of add command."""
    
    @patch('claude_code_setup.commands.add.Prompt.ask')
    @patch('claude_code_setup.commands.add.show_resource_type_selection')
    def test_interactive_mode_cancelled(self, mock_selection, mock_prompt, temp_claude_dir):
        """Test interactive mode when cancelled."""
        runner = CliRunner()
        
        # Simulate user cancelling
        mock_selection.side_effect = KeyboardInterrupt()
        
        result = runner.invoke(cli, [
            "add",
            "--test-dir", str(temp_claude_dir.parent)
        ])
        
        assert result.exit_code == 1
        assert "cancelled by user" in result.output