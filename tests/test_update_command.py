"""Tests for the update command."""

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from claude_code_setup.cli import cli
from claude_code_setup.commands.update import (
    compare_template_content,
    find_installed_templates,
    get_updatable_templates,
    update_settings,
    update_templates_batch,
)
from claude_code_setup.utils.template import Template


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_templates():
    """Create mock templates for testing."""
    return [
        Template(
            name="test-template-1",
            content="# Test Template 1\nUpdated content v2",
            category="general",
            description="Test template 1",
        ),
        Template(
            name="test-template-2",
            content="# Test Template 2\nOriginal content",
            category="python",
            description="Test template 2",
        ),
        Template(
            name="test-template-3",
            content="# Test Template 3\nNew content",
            category="node",
            description="Test template 3",
        ),
    ]


@pytest.fixture
def setup_installed_templates(tmp_path, mock_templates):
    """Set up installed templates with different states."""
    commands_dir = tmp_path / ".claude" / "commands"
    
    # Install template 1 with old content (needs update)
    general_dir = commands_dir / "general"
    general_dir.mkdir(parents=True)
    (general_dir / "test-template-1.md").write_text("# Test Template 1\nOld content v1")
    
    # Install template 2 with same content (no update needed)
    python_dir = commands_dir / "python"
    python_dir.mkdir(parents=True)
    (python_dir / "test-template-2.md").write_text("# Test Template 2\nOriginal content")
    
    return tmp_path / ".claude"


class TestUpdateCommand:
    """Test the update command functionality."""
    
    def _create_mock_registry(self, templates):
        """Helper to create a mock template registry."""
        from claude_code_setup.utils.template import TemplateRegistry
        return TemplateRegistry(
            templates={t.name: t for t in templates},
            last_updated=time.time(),
        )
    
    def test_compare_template_content_needs_update(self, tmp_path, mock_templates):
        """Test comparing template content when update is needed."""
        # Set up old template
        commands_dir = tmp_path / ".claude" / "commands" / "general"
        commands_dir.mkdir(parents=True)
        (commands_dir / "test-template-1.md").write_text("Old content")
        
        with patch("claude_code_setup.commands.update.get_template_sync") as mock_get:
            mock_get.return_value = mock_templates[0]
            
            needs_update, current, latest = compare_template_content(
                "test-template-1", "general", tmp_path / ".claude"
            )
            
        assert needs_update is True
        assert current == "Old content"
        assert latest == "# Test Template 1\nUpdated content v2"
    
    def test_compare_template_content_no_update(self, tmp_path, mock_templates):
        """Test comparing template content when no update is needed."""
        # Set up template with same content
        commands_dir = tmp_path / ".claude" / "commands" / "python"
        commands_dir.mkdir(parents=True)
        (commands_dir / "test-template-2.md").write_text(mock_templates[1].content)
        
        with patch("claude_code_setup.commands.update.get_template_sync") as mock_get:
            mock_get.return_value = mock_templates[1]
            
            needs_update, current, latest = compare_template_content(
                "test-template-2", "python", tmp_path / ".claude"
            )
            
        assert needs_update is False
        assert current == latest
    
    def test_find_installed_templates(self, setup_installed_templates, mock_templates):
        """Test finding all installed templates."""
        from claude_code_setup.utils.template import TemplateRegistry
        
        with patch("claude_code_setup.commands.update.get_all_templates_sync") as mock_get_all:
            mock_get_all.return_value = self._create_mock_registry(mock_templates)
            
            installed = find_installed_templates(setup_installed_templates)
            
        assert "general" in installed
        assert "test-template-1" in installed["general"]
        assert "python" in installed
        assert "test-template-2" in installed["python"]
        assert "node" not in installed  # Not installed
    
    def test_get_updatable_templates(self, setup_installed_templates, mock_templates):
        """Test getting list of updatable templates."""
        from claude_code_setup.utils.template import TemplateRegistry
        
        with patch("claude_code_setup.commands.update.get_all_templates_sync") as mock_get_all:
            with patch("claude_code_setup.commands.update.get_template_sync") as mock_get:
                mock_get_all.return_value = self._create_mock_registry(mock_templates)
                mock_get.side_effect = lambda name: next(
                    (t for t in mock_templates if t.name == name), None
                )
                
                updatable = get_updatable_templates(setup_installed_templates)
                
        # Should find template 1 needs update, template 2 doesn't
        assert len(updatable) == 1
        assert updatable[0] == ("test-template-1", "general", True)
    
    def test_get_updatable_templates_with_force(
        self, setup_installed_templates, mock_templates
    ):
        """Test getting updatable templates with force flag."""
        with patch("claude_code_setup.commands.update.get_all_templates_sync") as mock_get_all:
            with patch("claude_code_setup.commands.update.get_template_sync") as mock_get:
                mock_get_all.return_value = self._create_mock_registry(mock_templates)
                mock_get.side_effect = lambda name: next(
                    (t for t in mock_templates if t.name == name), None
                )
                
                updatable = get_updatable_templates(
                    setup_installed_templates, force=True
                )
                
        # Should include both installed templates with force
        assert len(updatable) == 2
        names = [t[0] for t in updatable]
        assert "test-template-1" in names
        assert "test-template-2" in names
    
    def test_update_templates_batch(self, tmp_path, mock_templates):
        """Test batch updating templates."""
        target_dir = tmp_path / ".claude"
        templates_to_update = [
            ("test-template-1", "general"),
            ("test-template-2", "python"),
        ]
        
        with patch("claude_code_setup.commands.update.get_template_sync") as mock_get:
            mock_get.side_effect = lambda name: next(
                (t for t in mock_templates if t.name == name), None
            )
            
            with patch("claude_code_setup.commands.update.TemplateInstaller") as MockInstaller:
                mock_installer = MockInstaller.return_value
                mock_installer.install_template.return_value = MagicMock(
                    success=True, template_name="test"
                )
                
                results, errors = update_templates_batch(
                    templates_to_update, target_dir
                )
                
        assert len(results) == 2
        assert len(errors) == 0
        assert mock_installer.install_template.call_count == 2
    
    def test_update_settings(self, tmp_path):
        """Test updating settings file."""
        target_dir = tmp_path / ".claude"
        target_dir.mkdir(parents=True)
        
        # Create current settings
        current = {
            "theme": "user-theme",
            "allowedTools": ["tool1"],
            "hooks": {"UserPromptSubmit": ["hook1"]},
        }
        (target_dir / "settings.json").write_text(json.dumps(current))
        
        # Mock default settings with new additions
        default = {
            "theme": "default-theme",
            "allowedTools": ["tool1", "tool2"],
            "hooks": {"UserPromptSubmit": [], "PreToolUse": []},
            "newFeature": True,
        }
        
        with patch("claude_code_setup.commands.update.get_default_settings") as mock_default:
            mock_default.return_value = default
            
            success = update_settings(target_dir)
            
        assert success is True
        
        # Check merged settings
        updated = json.loads((target_dir / "settings.json").read_text())
        assert updated["theme"] == "user-theme"  # User value preserved
        assert "tool2" in updated["allowedTools"]  # New tool added
        assert updated["hooks"]["UserPromptSubmit"] == ["hook1"]  # User hooks preserved
        assert "PreToolUse" in updated["hooks"]  # New hook type added
        assert updated["newFeature"] is True  # New feature added
    
    def test_cli_update_all(self, runner, setup_installed_templates, mock_templates):
        """Test update command with --all flag."""
        with patch("claude_code_setup.commands.update.get_all_templates_sync") as mock_get_all:
            with patch("claude_code_setup.commands.update.get_template_sync") as mock_get:
                mock_get_all.return_value = self._create_mock_registry(mock_templates)
                mock_get.side_effect = lambda name: next(
                    (t for t in mock_templates if t.name == name), None
                )
                
                with patch("claude_code_setup.commands.update.TemplateInstaller") as MockInstaller:
                    mock_installer = MockInstaller.return_value
                    mock_installer.install_template.return_value = MagicMock(
                        success=True,
                        template_name="test",
                        already_installed=False,
                        action="updated",
                    )
                    
                    result = runner.invoke(
                        cli,
                        ["update", "--all", "--test-dir", str(setup_installed_templates)],
                    )
                    
        assert result.exit_code == 0
        assert mock_installer.install_template.called
    
    def test_cli_update_specific(self, runner, setup_installed_templates, mock_templates):
        """Test update command with specific template."""
        with patch("claude_code_setup.commands.update.get_all_templates_sync") as mock_get_all:
            with patch("claude_code_setup.commands.update.get_template_sync") as mock_get:
                mock_get_all.return_value = self._create_mock_registry(mock_templates)
                mock_get.side_effect = lambda name: next(
                    (t for t in mock_templates if t.name == name), None
                )
                
                with patch("claude_code_setup.commands.update.TemplateInstaller") as MockInstaller:
                    mock_installer = MockInstaller.return_value
                    mock_installer.install_template.return_value = MagicMock(
                        success=True,
                        template_name="test-template-1",
                        already_installed=False,
                        action="updated",
                    )
                    
                    result = runner.invoke(
                        cli,
                        [
                            "update",
                            "test-template-1",
                            "--test-dir",
                            str(setup_installed_templates),
                        ],
                    )
                    
        assert result.exit_code == 0
        assert mock_installer.install_template.call_count == 1
    
    def test_cli_update_settings(self, runner, tmp_path):
        """Test update command for settings."""
        target_dir = tmp_path / ".claude"
        target_dir.mkdir(parents=True)
        
        # Create settings file
        (target_dir / "settings.json").write_text('{"theme": "user-theme"}')
        
        with patch("claude_code_setup.commands.update.get_default_settings") as mock_default:
            mock_default.return_value = {"theme": "default", "newOption": True}
            
            result = runner.invoke(
                cli, ["update", "--settings", "--test-dir", str(target_dir)]
            )
            
        assert result.exit_code == 0
        
        # Check settings were updated
        updated = json.loads((target_dir / "settings.json").read_text())
        assert updated["theme"] == "user-theme"  # Preserved
        assert updated["newOption"] is True  # Added
    
    def test_cli_update_dry_run(self, runner, setup_installed_templates, mock_templates):
        """Test update command with dry run."""
        with patch("claude_code_setup.commands.update.get_all_templates_sync") as mock_get_all:
            with patch("claude_code_setup.commands.update.get_template_sync") as mock_get:
                mock_get_all.return_value = self._create_mock_registry(mock_templates)
                mock_get.side_effect = lambda name: next(
                    (t for t in mock_templates if t.name == name), None
                )
                
                result = runner.invoke(
                    cli,
                    [
                        "update",
                        "--all",
                        "--dry-run",
                        "--test-dir",
                        str(setup_installed_templates),
                    ],
                )
                
        assert result.exit_code == 0
        # Should not actually update files
        content = (setup_installed_templates / "commands" / "general" / "test-template-1.md").read_text()
        assert "Old content v1" in content  # Original content preserved
    
    def test_cli_update_no_templates(self, runner, tmp_path):
        """Test update command when no templates are installed."""
        result = runner.invoke(
            cli, ["update", "--all", "--test-dir", str(tmp_path / ".claude")]
        )
        
        assert result.exit_code == 0
        assert "No installed templates found" in result.output
    
    def test_cli_update_interactive_cancelled(self, runner, setup_installed_templates):
        """Test update command interactive mode cancelled."""
        with patch("claude_code_setup.commands.update.get_all_templates_sync") as mock_get_all:
            mock_get_all.return_value = []
            
            with patch("claude_code_setup.commands.update.show_update_selection") as mock_show:
                mock_show.return_value = None  # User cancelled
                
                result = runner.invoke(
                    cli, ["update", "--test-dir", str(setup_installed_templates)]
                )
                
        assert result.exit_code == 0
        assert "cancelled" in result.output.lower()