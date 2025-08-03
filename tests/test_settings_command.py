"""Tests for the settings command."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from claude_code_setup.commands.settings import (
    determine_settings_path,
    show_current_settings,
    manage_theme,
    run_settings_command,
)
from claude_code_setup.utils.settings import get_settings_sync
from claude_code_setup.types import ClaudeSettings, PermissionsSettings


class TestDetermineSettingsPath:
    """Test settings path determination."""

    def test_determine_settings_path_test_dir(self):
        """Test settings path with test directory."""
        test_dir = "/tmp/test"
        result = determine_settings_path(test_dir, False)
        expected = Path("/tmp/test/.claude/settings.json")
        assert result == expected

    def test_determine_settings_path_global(self):
        """Test settings path with global flag."""
        result = determine_settings_path(None, True)
        expected = Path.home() / ".claude" / "settings.json"
        assert result == expected

    def test_determine_settings_path_local(self):
        """Test settings path with local directory."""
        result = determine_settings_path(None, False)
        expected = Path.cwd() / ".claude" / "settings.json"
        assert result == expected


class TestShowCurrentSettings:
    """Test showing current settings."""

    @patch('claude_code_setup.commands.settings.console')
    def test_show_current_settings_no_file(self, mock_console):
        """Test showing settings when file doesn't exist."""
        settings_path = Path("/nonexistent/settings.json")
        show_current_settings(settings_path)
        
        # Should show "not found" message
        mock_console.print.assert_called()
        call_args = str(mock_console.print.call_args_list)
        assert "Settings Not Found" in call_args

    @patch('claude_code_setup.commands.settings.console')
    @patch('claude_code_setup.commands.settings.read_settings_sync')
    def test_show_current_settings_with_file(self, mock_read_settings, mock_console):
        """Test showing settings when file exists."""
        # Create mock settings
        mock_settings = ClaudeSettings(
            theme="dark",
            permissions=PermissionsSettings(allow=["Bash(git:*)", "Bash(python:*)"]),
            autoUpdaterStatus=True,
            preferredNotifChannel="terminal",
            verbose=False,
        )
        mock_read_settings.return_value = mock_settings
        
        settings_path = Path("/tmp/settings.json")
        with patch.object(settings_path, 'exists', return_value=True):
            show_current_settings(settings_path)
        
        # Should show settings table
        mock_console.print.assert_called()
        call_args = str(mock_console.print.call_args_list)
        assert "dark" in call_args  # Theme
        assert "2 allowed" in call_args  # Permissions count


class TestManageTheme:
    """Test theme management."""

    @patch('claude_code_setup.commands.settings.get_available_themes_sync')
    @patch('claude_code_setup.commands.settings.read_settings_sync')
    @patch('claude_code_setup.commands.settings.save_settings_sync')
    @patch('claude_code_setup.commands.settings.Prompt.ask')
    @patch('claude_code_setup.commands.settings.console')
    def test_manage_theme_success(self, mock_console, mock_prompt, mock_save, mock_read, mock_get_themes):
        """Test successful theme change."""
        # Setup mocks
        mock_get_themes.return_value = ["default", "dark"]
        mock_settings = ClaudeSettings(theme="default")
        mock_read.return_value = mock_settings
        mock_prompt.return_value = "dark"
        
        settings_path = Path("/tmp/settings.json")
        result = manage_theme(settings_path)
        
        assert result is True
        mock_save.assert_called_once()
        # Check that theme was updated
        saved_settings = mock_save.call_args[0][0]
        assert saved_settings.theme == "dark"

    @patch('claude_code_setup.commands.settings.get_available_themes_sync')
    @patch('claude_code_setup.commands.settings.read_settings_sync')
    @patch('claude_code_setup.commands.settings.Prompt.ask')
    @patch('claude_code_setup.commands.settings.console')
    def test_manage_theme_no_change(self, mock_console, mock_prompt, mock_read, mock_get_themes):
        """Test theme management when no change is made."""
        # Setup mocks
        mock_get_themes.return_value = ["default", "dark"]
        mock_settings = ClaudeSettings(theme="default")
        mock_read.return_value = mock_settings
        mock_prompt.return_value = "default"  # Same theme
        
        settings_path = Path("/tmp/settings.json")
        result = manage_theme(settings_path)
        
        assert result is False

    @patch('claude_code_setup.commands.settings.get_available_themes_sync')
    @patch('claude_code_setup.commands.settings.console')
    def test_manage_theme_no_themes_available(self, mock_console, mock_get_themes):
        """Test theme management when no themes are available."""
        mock_get_themes.return_value = []
        
        settings_path = Path("/tmp/settings.json")
        result = manage_theme(settings_path)
        
        assert result is False


class TestRunSettingsCommand:
    """Test the main settings command entry point."""

    @patch('claude_code_setup.commands.settings.show_current_settings')
    @patch('claude_code_setup.commands.settings.determine_settings_path')
    def test_run_settings_command_show_action(self, mock_determine_path, mock_show_settings):
        """Test settings command with show action."""
        mock_path = Path("/tmp/settings.json")
        mock_determine_path.return_value = mock_path
        
        with patch.object(mock_path.parent, 'mkdir'):
            run_settings_command(
                action="show",
                test_dir=None,
                global_config=False,
                interactive=False
            )
        
        mock_show_settings.assert_called_once_with(mock_path)

    @patch('claude_code_setup.commands.settings.manage_theme')
    @patch('claude_code_setup.commands.settings.determine_settings_path')
    def test_run_settings_command_theme_action(self, mock_determine_path, mock_manage_theme):
        """Test settings command with theme action."""
        mock_path = Path("/tmp/settings.json")
        mock_determine_path.return_value = mock_path
        
        with patch.object(mock_path.parent, 'mkdir'):
            run_settings_command(
                action="theme",
                test_dir=None,
                global_config=False,
                interactive=False
            )
        
        mock_manage_theme.assert_called_once_with(mock_path)

    @patch('claude_code_setup.commands.settings.show_settings_menu')
    @patch('claude_code_setup.commands.settings.determine_settings_path')
    def test_run_settings_command_interactive(self, mock_determine_path, mock_show_menu):
        """Test settings command in interactive mode."""
        mock_path = Path("/tmp/settings.json")
        mock_determine_path.return_value = mock_path
        
        with patch.object(mock_path.parent, 'mkdir'):
            run_settings_command(
                action=None,
                test_dir=None,
                global_config=False,
                interactive=True
            )
        
        mock_show_menu.assert_called_once_with(mock_path)

    @patch('claude_code_setup.commands.settings.show_current_settings')
    @patch('claude_code_setup.commands.settings.determine_settings_path')
    def test_run_settings_command_non_interactive(self, mock_determine_path, mock_show_settings):
        """Test settings command in non-interactive mode."""
        mock_path = Path("/tmp/settings.json")
        mock_determine_path.return_value = mock_path
        
        with patch.object(mock_path.parent, 'mkdir'):
            run_settings_command(
                action=None,
                test_dir=None,
                global_config=False,
                interactive=False
            )
        
        mock_show_settings.assert_called_once_with(mock_path)

    def test_run_settings_command_invalid_action(self):
        """Test settings command with invalid action."""
        with pytest.raises(SystemExit):
            run_settings_command(
                action="invalid",
                test_dir=None,
                global_config=False,
                interactive=False
            )


class TestSettingsCommandIntegration:
    """Integration tests for settings command functionality."""

    def test_settings_command_functions_exist(self):
        """Test that all required functions exist and are importable."""
        from claude_code_setup.commands.settings import (
            determine_settings_path,
            show_current_settings,
            manage_theme,
            manage_environment_variables,
            manage_permissions,
            show_settings_menu,
            run_settings_command,
        )
        
        # All functions should be callable
        assert callable(determine_settings_path)
        assert callable(show_current_settings)
        assert callable(manage_theme)
        assert callable(manage_environment_variables)
        assert callable(manage_permissions)
        assert callable(show_settings_menu)
        assert callable(run_settings_command)

    @patch('claude_code_setup.commands.settings.get_available_themes_sync')
    def test_available_themes_integration(self, mock_get_themes):
        """Test integration with theme loading."""
        mock_get_themes.return_value = ["default", "dark"]
        
        # This should not raise an exception
        from claude_code_setup.commands.settings import manage_theme
        from claude_code_setup.utils.settings import get_available_themes_sync
        
        themes = get_available_themes_sync()
        assert isinstance(themes, list)

    @patch('claude_code_setup.commands.settings.get_available_permission_sets_sync')
    def test_available_permissions_integration(self, mock_get_perms):
        """Test integration with permission loading."""
        mock_get_perms.return_value = ["python", "node", "git", "shell", "package-managers"]
        
        # This should not raise an exception
        from claude_code_setup.commands.settings import manage_permissions
        from claude_code_setup.utils.settings import get_available_permission_sets_sync
        
        perms = get_available_permission_sets_sync()
        assert isinstance(perms, list)