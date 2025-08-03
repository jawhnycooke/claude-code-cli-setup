"""Tests for list command functionality."""

import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from claude_code_setup.commands.list import (
    run_list_command,
    determine_target_directory,
    show_templates,
    show_hooks,
    show_settings,
)
from claude_code_setup.utils import CLAUDE_HOME


class TestListCommand:
    """Test list command functionality."""

    def test_determine_target_directory_test_dir(self):
        """Test target directory determination with test dir."""
        target = determine_target_directory("/tmp/test", False)
        expected = Path("/tmp/test") / ".claude"
        assert target == expected

    def test_determine_target_directory_global(self):
        """Test target directory determination with global config."""
        target = determine_target_directory(None, True)
        assert target == CLAUDE_HOME

    def test_determine_target_directory_local(self):
        """Test target directory determination with local config."""
        target = determine_target_directory(None, False)
        expected = Path.cwd() / ".claude"
        assert target == expected

    @patch('claude_code_setup.commands.list.warning')
    def test_show_templates_no_templates(self, mock_warning):
        """Test showing templates when none are available."""
        with patch('claude_code_setup.commands.list.get_all_templates_sync') as mock_get_templates:
            from claude_code_setup.types import TemplateRegistry
            mock_get_templates.return_value = TemplateRegistry(templates={})
            
            show_templates()
            
            # Should show warning about no templates
            mock_warning.assert_called_once_with("No templates found. Please ensure template files exist.")

    @patch('claude_code_setup.commands.list.console')
    def test_show_templates_with_templates(self, mock_console):
        """Test showing templates when templates are available."""
        with patch('claude_code_setup.commands.list.get_all_templates_sync') as mock_get_templates:
            from claude_code_setup.types import Template, TemplateRegistry, TemplateCategory
            
            template = Template(
                name="test-template",
                description="Test template description",
                category=TemplateCategory.PYTHON,
                content="# Test Template",
            )
            
            mock_get_templates.return_value = TemplateRegistry(
                templates={"test-template": template}
            )
            
            show_templates()
            
            # Should show templates table
            mock_console.print.assert_called()

    @patch('claude_code_setup.commands.list.console')
    def test_show_templates_with_category_filter(self, mock_console):
        """Test showing templates with category filter."""
        with patch('claude_code_setup.commands.list.get_all_templates_sync') as mock_get_templates:
            from claude_code_setup.types import Template, TemplateRegistry, TemplateCategory
            
            python_template = Template(
                name="python-template",
                description="Python template",
                category=TemplateCategory.PYTHON,
                content="# Python Template",
            )
            
            node_template = Template(
                name="node-template", 
                description="Node template",
                category=TemplateCategory.NODE,
                content="# Node Template",
            )
            
            mock_get_templates.return_value = TemplateRegistry(
                templates={
                    "python-template": python_template,
                    "node-template": node_template,
                }
            )
            
            show_templates(category_filter="python")
            
            # Should show only python templates
            mock_console.print.assert_called()

    @patch('claude_code_setup.commands.list.warning')
    def test_show_templates_invalid_category(self, mock_warning):
        """Test showing templates with invalid category filter."""
        with patch('claude_code_setup.commands.list.get_all_templates_sync') as mock_get_templates:
            from claude_code_setup.types import TemplateRegistry
            mock_get_templates.return_value = TemplateRegistry(templates={})
            
            show_templates(category_filter="invalid")
            
            # Should show warning about invalid category
            mock_warning.assert_called_once()

    @patch('claude_code_setup.commands.list.console')  
    def test_show_templates_with_installed_filter(self, mock_console):
        """Test showing only installed templates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir) / ".claude"
            commands_dir = target_dir / "commands" / "python"
            commands_dir.mkdir(parents=True)
            
            # Create an installed template file
            template_file = commands_dir / "test-template.md"
            template_file.write_text("# Test Template")
            
            with patch('claude_code_setup.commands.list.get_all_templates_sync') as mock_get_templates:
                from claude_code_setup.types import Template, TemplateRegistry, TemplateCategory
                
                template = Template(
                    name="test-template",
                    description="Test template",
                    category=TemplateCategory.PYTHON,
                    content="# Test Template",
                )
                
                mock_get_templates.return_value = TemplateRegistry(
                    templates={"test-template": template}
                )
                
                show_templates(installed_only=True, target_dir=target_dir)
                
                # Should show templates table with installed status
                mock_console.print.assert_called()

    @patch('claude_code_setup.commands.list.console')
    def test_show_hooks(self, mock_console):
        """Test showing hooks."""
        show_hooks()
        
        # Should show hooks table
        mock_console.print.assert_called()

    @patch('claude_code_setup.commands.list.console')
    def test_show_settings(self, mock_console):
        """Test showing settings."""
        with patch('claude_code_setup.commands.list.get_available_themes_sync') as mock_themes, \
             patch('claude_code_setup.commands.list.get_available_permission_sets_sync') as mock_perms:
            
            mock_themes.return_value = ["default", "dark"]
            mock_perms.return_value = ["python", "node", "git", "shell", "package-managers"]
            
            show_settings()
            
            # Should show settings table
            mock_console.print.assert_called()

    @patch('claude_code_setup.commands.list.console')
    def test_show_settings_with_target_dir(self, mock_console):
        """Test showing settings with target directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir) / ".claude"
            settings_file = target_dir / "settings.json"
            target_dir.mkdir(parents=True)
            settings_file.write_text('{"theme": "default"}')
            
            with patch('claude_code_setup.commands.list.get_available_themes_sync') as mock_themes, \
                 patch('claude_code_setup.commands.list.get_available_permission_sets_sync') as mock_perms:
                
                mock_themes.return_value = ["default", "dark"]
                mock_perms.return_value = ["python", "node"]
                
                show_settings(target_dir=target_dir)
                
                # Should show settings table and current status
                mock_console.print.assert_called()

    def test_run_list_command_templates(self):
        """Test running list command for templates."""
        with patch('claude_code_setup.commands.list.show_templates') as mock_show:
            run_list_command(resource_type="templates", interactive=False)
            mock_show.assert_called_once()

    def test_run_list_command_hooks(self):
        """Test running list command for hooks."""
        with patch('claude_code_setup.commands.list.show_hooks') as mock_show:
            run_list_command(resource_type="hooks", interactive=False)
            mock_show.assert_called_once()

    def test_run_list_command_settings(self):
        """Test running list command for settings."""
        with patch('claude_code_setup.commands.list.show_settings') as mock_show:
            run_list_command(resource_type="settings", interactive=False)
            mock_show.assert_called_once()

    def test_run_list_command_all(self):
        """Test running list command for all resources."""
        with patch('claude_code_setup.commands.list.show_all_resources') as mock_show:
            run_list_command(interactive=False)
            mock_show.assert_called_once()

    def test_run_list_command_with_test_dir(self):
        """Test running list command with test directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('claude_code_setup.commands.list.show_templates') as mock_show:
                run_list_command(
                    resource_type="templates",
                    test_dir=temp_dir,
                    interactive=False
                )
                
                # Should call show_templates with target_dir
                mock_show.assert_called_once()
                args, kwargs = mock_show.call_args
                # The target_dir should be passed in the call

    def test_run_list_command_with_global_config(self):
        """Test running list command with global config."""
        with patch('claude_code_setup.commands.list.show_templates') as mock_show:
            run_list_command(
                resource_type="templates",
                global_config=True,
                interactive=False
            )
            
            # Should call show_templates with CLAUDE_HOME as target_dir
            mock_show.assert_called_once()

    def test_run_list_command_with_category_filter(self):
        """Test running list command with category filter."""
        with patch('claude_code_setup.commands.list.show_templates') as mock_show:
            run_list_command(
                resource_type="templates",
                category="python",
                interactive=False
            )
            
            # Should call show_templates with category filter
            mock_show.assert_called_once()
            args, kwargs = mock_show.call_args
            # Category should be passed as first argument

    def test_run_list_command_with_installed_filter(self):
        """Test running list command with installed filter."""
        with patch('claude_code_setup.commands.list.show_templates') as mock_show:
            run_list_command(
                resource_type="templates",
                installed=True,
                interactive=False
            )
            
            # Should call show_templates with installed filter
            mock_show.assert_called_once()

    @patch('claude_code_setup.commands.list.console')
    def test_run_list_command_keyboard_interrupt(self, mock_console):
        """Test list command handling keyboard interrupt."""
        with patch('claude_code_setup.commands.list.show_templates') as mock_show:
            mock_show.side_effect = KeyboardInterrupt()
            
            with pytest.raises(SystemExit) as exc_info:
                run_list_command(resource_type="templates", interactive=False)
            
            assert exc_info.value.code == 1

    @patch('claude_code_setup.commands.list.console')
    def test_run_list_command_unexpected_error(self, mock_console):
        """Test list command handling unexpected errors."""
        with patch('claude_code_setup.commands.list.show_templates') as mock_show:
            mock_show.side_effect = RuntimeError("Test error")
            
            with pytest.raises(SystemExit) as exc_info:
                run_list_command(resource_type="templates", interactive=False)
            
            assert exc_info.value.code == 1

    def test_run_list_command_interactive_mode(self):
        """Test running list command in interactive mode."""
        with patch('claude_code_setup.commands.list.show_templates') as mock_show:
            run_list_command(resource_type="templates", interactive=True)
            
            # Should call show_templates and show interactive tip
            mock_show.assert_called_once()
            # Interactive tip should be shown (tested through console output)

    def test_run_list_command_settings_no_interactive_tip(self):
        """Test that settings command doesn't show interactive tip."""
        with patch('claude_code_setup.commands.list.show_settings') as mock_show, \
             patch('claude_code_setup.commands.list.console') as mock_console:
            
            run_list_command(resource_type="settings", interactive=True)
            
            # Should call show_settings but not show interactive tip for settings
            mock_show.assert_called_once()
            # The interactive tip should not be shown for settings