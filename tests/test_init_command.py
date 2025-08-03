"""Tests for init command functionality."""

import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from claude_code_setup.commands.init import (
    run_init_command,
    determine_target_directory,
    parse_permission_sets,
    run_quick_setup,
)
from claude_code_setup.utils import CLAUDE_HOME


class TestInitCommand:
    """Test init command functionality."""

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

    def test_parse_permission_sets(self):
        """Test parsing of comma-separated permission sets."""
        result = parse_permission_sets("python, node,git , shell")
        expected = ["python", "node", "git", "shell"]
        assert result == expected

    def test_parse_permission_sets_empty(self):
        """Test parsing empty permission sets."""
        result = parse_permission_sets("")
        assert result == []

    def test_quick_setup_dry_run(self, capsys):
        """Test quick setup in dry run mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            run_quick_setup(
                force=False,
                dry_run=True,
                test_dir=temp_dir,
                global_config=False,
                permissions="python,git",
                theme="default",
                no_check=False,
            )
            
            # Verify no actual files were created
            claude_dir = Path(temp_dir) / ".claude"
            assert not claude_dir.exists()

    def test_quick_setup_actual(self):
        """Test quick setup actually creating files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            run_quick_setup(
                force=False,
                dry_run=False,
                test_dir=temp_dir,
                global_config=False,
                permissions="python,git",
                theme="default",
                no_check=False,
            )
            
            # Verify files were created
            claude_dir = Path(temp_dir) / ".claude"
            settings_file = claude_dir / "settings.json"
            commands_dir = claude_dir / "commands"
            
            assert claude_dir.exists()
            assert settings_file.exists()
            assert commands_dir.exists()
            
            # Verify category directories
            for category in ['python', 'node', 'project', 'general']:
                category_dir = commands_dir / category
                assert category_dir.exists()

    def test_quick_setup_existing_no_force(self):
        """Test quick setup with existing configuration without force."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create existing setup
            claude_dir = Path(temp_dir) / ".claude"
            settings_file = claude_dir / "settings.json"
            claude_dir.mkdir(parents=True)
            settings_file.write_text('{"test": true}')
            
            # Try to setup again without force
            with pytest.raises(SystemExit):
                run_quick_setup(
                    force=False,
                    dry_run=False,
                    test_dir=temp_dir,
                    global_config=False,
                    permissions="python",
                    theme="default",
                    no_check=False,
                )

    def test_quick_setup_existing_with_force(self):
        """Test quick setup with existing configuration with force."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create existing setup
            claude_dir = Path(temp_dir) / ".claude"
            settings_file = claude_dir / "settings.json"
            claude_dir.mkdir(parents=True)
            settings_file.write_text('{"test": true}')
            
            # Setup again with force
            run_quick_setup(
                force=True,
                dry_run=False,
                test_dir=temp_dir,
                global_config=False,
                permissions="python",
                theme="default",
                no_check=False,
            )
            
            # Verify new setup overwrote old one
            assert settings_file.exists()
            content = settings_file.read_text()
            assert '"test": true' not in content  # Old content should be gone

    def test_quick_setup_existing_with_no_check(self):
        """Test quick setup with existing configuration with no-check flag."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create existing setup
            claude_dir = Path(temp_dir) / ".claude"
            settings_file = claude_dir / "settings.json"
            claude_dir.mkdir(parents=True)
            settings_file.write_text('{"test": true}')
            
            # Setup again with no-check
            run_quick_setup(
                force=False,
                dry_run=False,
                test_dir=temp_dir,
                global_config=False,
                permissions="python",
                theme="default",
                no_check=True,
            )
            
            # Verify new setup was created
            assert settings_file.exists()

    def test_run_init_command_quick_mode(self):
        """Test main init command entry point in quick mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            run_init_command(
                quick=True,
                force=False,
                dry_run=False,
                test_dir=temp_dir,
                global_config=False,
                permissions="python,git",
                theme="default",
                no_check=False,
                interactive=False,
            )
            
            # Verify setup was created
            claude_dir = Path(temp_dir) / ".claude"
            settings_file = claude_dir / "settings.json"
            assert claude_dir.exists()
            assert settings_file.exists()

    def test_run_init_command_non_interactive(self):
        """Test main init command entry point in non-interactive mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            run_init_command(
                quick=False,
                force=False,
                dry_run=False,
                test_dir=temp_dir,
                global_config=False,
                permissions="python",
                theme="default",
                no_check=False,
                interactive=False,  # This should trigger quick setup
            )
            
            # Verify setup was created
            claude_dir = Path(temp_dir) / ".claude"
            assert claude_dir.exists()

    @patch('claude_code_setup.commands.init.console')
    @patch('claude_code_setup.commands.init.error_console')
    def test_run_init_command_keyboard_interrupt(self, mock_error_console, mock_console):
        """Test init command handling keyboard interrupt."""
        with patch('claude_code_setup.commands.init.run_quick_setup') as mock_quick:
            mock_quick.side_effect = KeyboardInterrupt()
            
            with pytest.raises(SystemExit) as exc_info:
                run_init_command(
                    quick=True,
                    force=False,
                    dry_run=False,
                    test_dir=None,
                    global_config=False,
                    permissions="python",
                    theme="default",
                    no_check=False,
                    interactive=False,
                )
            
            assert exc_info.value.code == 1
            # Verify error panel was printed
            mock_console.print.assert_called()

    @patch('claude_code_setup.commands.init.console')
    @patch('claude_code_setup.commands.init.error_console')
    def test_run_init_command_unexpected_error(self, mock_error_console, mock_console):
        """Test init command handling unexpected errors."""
        with patch('claude_code_setup.commands.init.run_quick_setup') as mock_quick:
            mock_quick.side_effect = RuntimeError("Test error")
            
            with pytest.raises(SystemExit) as exc_info:
                run_init_command(
                    quick=True,
                    force=False,
                    dry_run=False,
                    test_dir=None,
                    global_config=False,
                    permissions="python",
                    theme="default",
                    no_check=False,
                    interactive=False,
                )
            
            assert exc_info.value.code == 1
            # Verify error panel was printed to error console
            mock_error_console.print.assert_called()