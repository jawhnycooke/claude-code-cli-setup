"""Tests for the remove command."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from claude_code_setup.cli import cli
from claude_code_setup.commands.remove import (
    find_installed_templates_for_removal,
    remove_template_file,
    remove_templates_batch,
    remove_permission_from_settings,
)
from claude_code_setup.types import ClaudeSettings


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def setup_templates_for_removal(tmp_path):
    """Set up installed templates for removal testing."""
    claude_dir = tmp_path / ".claude"
    commands_dir = claude_dir / "commands"
    
    # Create templates in different categories
    general_dir = commands_dir / "general"
    general_dir.mkdir(parents=True)
    (general_dir / "code-review.md").write_text("# Code Review Template")
    (general_dir / "fix-issue.md").write_text("# Fix Issue Template")
    
    python_dir = commands_dir / "python"
    python_dir.mkdir(parents=True)
    (python_dir / "optimization.md").write_text("# Python Optimization")
    
    # Create settings file
    settings = {
        "theme": "default",
        "allowedTools": ["Bash(npm:*)", "Bash(pip:*)", "Bash(git:*)"],
        "hooks": {},
    }
    (claude_dir / "settings.json").write_text(json.dumps(settings, indent=2))
    
    return claude_dir


class TestRemoveCommand:
    """Test the remove command functionality."""
    
    def test_find_installed_templates_for_removal(self, setup_templates_for_removal):
        """Test finding installed templates."""
        installed = find_installed_templates_for_removal(setup_templates_for_removal)
        
        assert len(installed) == 3
        template_names = [name for name, _, _ in installed]
        assert "code-review" in template_names
        assert "fix-issue" in template_names
        assert "optimization" in template_names
        
        # Check categories
        categories = {cat for _, cat, _ in installed}
        assert "general" in categories
        assert "python" in categories
    
    def test_remove_template_file(self, tmp_path):
        """Test removing a single template file."""
        # Create template file
        template_dir = tmp_path / "commands" / "general"
        template_dir.mkdir(parents=True)
        template_file = template_dir / "test-template.md"
        template_file.write_text("# Test Template")
        
        assert template_file.exists()
        
        # Remove the template
        success = remove_template_file(template_file)
        
        assert success is True
        assert not template_file.exists()
        # Empty directory should be removed
        assert not template_dir.exists()
    
    def test_remove_template_file_dry_run(self, tmp_path):
        """Test dry run mode for template removal."""
        # Create template file
        template_dir = tmp_path / "commands" / "general"
        template_dir.mkdir(parents=True)
        template_file = template_dir / "test-template.md"
        template_file.write_text("# Test Template")
        
        # Remove with dry run
        success = remove_template_file(template_file, dry_run=True)
        
        assert success is True
        assert template_file.exists()  # File should still exist
    
    def test_remove_template_file_not_found(self, tmp_path):
        """Test removing a non-existent template."""
        template_file = tmp_path / "commands" / "general" / "missing.md"
        
        success = remove_template_file(template_file)
        
        assert success is False
    
    def test_remove_templates_batch(self, setup_templates_for_removal):
        """Test batch template removal."""
        installed = find_installed_templates_for_removal(setup_templates_for_removal)
        
        # Remove first two templates
        templates_to_remove = installed[:2]
        successes, errors = remove_templates_batch(templates_to_remove)
        
        assert len(successes) == 2
        assert len(errors) == 0
        
        # Check that files were removed
        for _, _, path in templates_to_remove:
            assert not path.exists()
    
    def test_remove_permission_from_settings(self, setup_templates_for_removal):
        """Test removing a permission from settings."""
        success = remove_permission_from_settings(
            "Bash(npm:*)", setup_templates_for_removal
        )
        
        assert success is True
        
        # Check updated settings
        settings_path = setup_templates_for_removal / "settings.json"
        settings = json.loads(settings_path.read_text())
        assert "Bash(npm:*)" not in settings["allowedTools"]
        assert len(settings["allowedTools"]) == 2  # Two permissions remain
    
    def test_remove_permission_not_found(self, setup_templates_for_removal):
        """Test removing a non-existent permission."""
        success = remove_permission_from_settings(
            "Bash(missing:*)", setup_templates_for_removal
        )
        
        assert success is False
    
    def test_cli_remove_specific_template(self, runner, setup_templates_for_removal):
        """Test removing a specific template via CLI."""
        result = runner.invoke(
            cli,
            [
                "remove",
                "code-review",
                "--test-dir",
                str(setup_templates_for_removal),
                "--force",  # Skip confirmation
            ],
        )
        
        assert result.exit_code == 0
        
        # Check template was removed
        template_file = setup_templates_for_removal / "commands" / "general" / "code-review.md"
        assert not template_file.exists()
    
    def test_cli_remove_all_templates(self, runner, setup_templates_for_removal):
        """Test removing all templates."""
        result = runner.invoke(
            cli,
            [
                "remove",
                "--all",
                "--test-dir",
                str(setup_templates_for_removal),
                "--force",  # Skip confirmation
            ],
        )
        
        assert result.exit_code == 0
        
        # Check all templates were removed
        commands_dir = setup_templates_for_removal / "commands"
        assert not list(commands_dir.glob("**/*.md"))  # No .md files remain
    
    def test_cli_remove_permission(self, runner, setup_templates_for_removal):
        """Test removing a permission via CLI."""
        result = runner.invoke(
            cli,
            [
                "remove",
                "--permission",
                "Bash(pip:*)",
                "--test-dir",
                str(setup_templates_for_removal),
            ],
        )
        
        assert result.exit_code == 0
        
        # Check permission was removed
        settings_path = setup_templates_for_removal / "settings.json"
        settings = json.loads(settings_path.read_text())
        assert "Bash(pip:*)" not in settings["allowedTools"]
    
    def test_cli_remove_dry_run(self, runner, setup_templates_for_removal):
        """Test dry run mode."""
        result = runner.invoke(
            cli,
            [
                "remove",
                "code-review",
                "--test-dir",
                str(setup_templates_for_removal),
                "--dry-run",
            ],
        )
        
        assert result.exit_code == 0
        assert "[DRY RUN]" in result.output
        
        # Check template still exists
        template_file = setup_templates_for_removal / "commands" / "general" / "code-review.md"
        assert template_file.exists()
    
    def test_cli_remove_no_templates(self, runner, tmp_path):
        """Test remove command when no templates are installed."""
        empty_dir = tmp_path / ".claude"
        empty_dir.mkdir()
        
        result = runner.invoke(
            cli, ["remove", "--all", "--test-dir", str(empty_dir)]
        )
        
        assert result.exit_code == 0
        assert "No installed templates found" in result.output
    
    def test_cli_remove_template_not_found(self, runner, setup_templates_for_removal):
        """Test removing a non-existent template."""
        result = runner.invoke(
            cli,
            [
                "remove",
                "non-existent",
                "--test-dir",
                str(setup_templates_for_removal),
            ],
        )
        
        assert result.exit_code == 0
        assert "Templates Not Found" in result.output
        assert "non-existent" in result.output
    
    def test_cli_remove_interactive_cancelled(self, runner, setup_templates_for_removal):
        """Test cancelling interactive removal."""
        with patch("claude_code_setup.commands.remove.show_removal_selection") as mock_show:
            mock_show.return_value = None  # User cancelled
            
            result = runner.invoke(
                cli, ["remove", "--test-dir", str(setup_templates_for_removal)]
            )
            
        assert result.exit_code == 0
        assert "cancelled" in result.output.lower()
    
    def test_cli_remove_confirmation_declined(self, runner, setup_templates_for_removal):
        """Test declining confirmation prompt."""
        with patch("claude_code_setup.ui.prompts.ConfirmationDialog.ask") as mock_ask:
            mock_ask.return_value = False  # User declined
            
            result = runner.invoke(
                cli,
                [
                    "remove",
                    "code-review",
                    "--test-dir",
                    str(setup_templates_for_removal),
                ],
            )
            
        assert result.exit_code == 0
        assert "cancelled" in result.output.lower()
        
        # Check template still exists
        template_file = setup_templates_for_removal / "commands" / "general" / "code-review.md"
        assert template_file.exists()