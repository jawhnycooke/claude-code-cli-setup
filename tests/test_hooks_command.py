"""Tests for hooks command implementation."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from claude_code_setup.commands.hooks import (
    run_hooks_list_command,
    run_hooks_add_command,
    run_hooks_remove_command,
    _get_installed_hooks,
    _display_hooks_list,
)
from claude_code_setup.types import Hook, HookEvent, HookConfig, HookRegistry


@pytest.fixture
def mock_hook_registry():
    """Create a mock hook registry for testing."""
    security_hook = Hook(
        name="command-validator",
        description="Validates bash commands for security",
        category="security",
        event=HookEvent.PRE_TOOL_USE,
        matcher="Bash",
        dependencies=["python3"],
        config=HookConfig(
            type="command",
            command="python3 .claude/hooks/security/command-validator/command_validator.py"
        ),
        scripts={"command_validator.py": "#!/usr/bin/env python3\nprint('test')"}
    )
    
    aws_hook = Hook(
        name="deployment-guard",
        description="Guards against dangerous AWS deployments",
        category="aws",
        event=HookEvent.PRE_TOOL_USE,
        matcher="Bash",
        dependencies=["python3", "aws"],
        config=HookConfig(
            type="command",
            command="python3 .claude/hooks/aws/deployment-guard/validate_aws_command.py"
        ),
        scripts={"validate_aws_command.py": "#!/usr/bin/env python3\nprint('aws test')"}
    )
    
    test_hook = Hook(
        name="test-enforcement",
        description="Enforces test execution after code changes",
        category="testing",
        event=HookEvent.POST_TOOL_USE,
        matcher="Edit|MultiEdit|Write",
        dependencies=["bash"],
        config=HookConfig(
            type="command",
            command="bash .claude/hooks/testing/test-enforcement/run_tests_on_change.sh"
        ),
        scripts={"run_tests_on_change.sh": "#!/bin/bash\necho 'running tests'"}
    )
    
    return HookRegistry(
        hooks={
            "command-validator": security_hook,
            "deployment-guard": aws_hook,
            "test-enforcement": test_hook,
        }
    )


@pytest.fixture
def temp_claude_dir():
    """Create a temporary .claude directory structure."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        claude_dir = Path(tmp_dir) / ".claude"
        claude_dir.mkdir()
        (claude_dir / "hooks").mkdir()
        yield claude_dir


class TestHooksListCommand:
    """Test hooks list command functionality."""
    
    @patch('claude_code_setup.commands.hooks.get_all_hooks_sync')
    def test_list_all_hooks(self, mock_get_hooks, mock_hook_registry, temp_claude_dir, capsys):
        """Test listing all available hooks."""
        mock_get_hooks.return_value = mock_hook_registry
        
        run_hooks_list_command(
            test_dir=str(temp_claude_dir.parent),
            interactive=False
        )
        
        # Verify the function was called
        mock_get_hooks.assert_called_once()
    
    @patch('claude_code_setup.commands.hooks.get_all_hooks_sync')
    def test_list_hooks_by_category(self, mock_get_hooks, mock_hook_registry, temp_claude_dir):
        """Test filtering hooks by category."""
        mock_get_hooks.return_value = mock_hook_registry
        
        run_hooks_list_command(
            category="security",
            test_dir=str(temp_claude_dir.parent),
            interactive=False
        )
        
        mock_get_hooks.assert_called_once()
    
    @patch('claude_code_setup.commands.hooks.get_all_hooks_sync')
    def test_list_hooks_by_event(self, mock_get_hooks, mock_hook_registry, temp_claude_dir):
        """Test filtering hooks by event type."""
        mock_get_hooks.return_value = mock_hook_registry
        
        run_hooks_list_command(
            event="PreToolUse",
            test_dir=str(temp_claude_dir.parent),
            interactive=False
        )
        
        mock_get_hooks.assert_called_once()
    
    @patch('claude_code_setup.commands.hooks.get_all_hooks_sync')
    def test_list_installed_hooks_only(self, mock_get_hooks, mock_hook_registry, temp_claude_dir):
        """Test listing only installed hooks."""
        mock_get_hooks.return_value = mock_hook_registry
        
        # Create some installed hooks
        security_dir = temp_claude_dir / "hooks" / "security" / "command-validator"
        security_dir.mkdir(parents=True)
        (security_dir / "metadata.json").write_text(json.dumps({
            "name": "command-validator",
            "description": "Test hook",
            "category": "security"
        }))
        
        run_hooks_list_command(
            installed=True,
            test_dir=str(temp_claude_dir.parent),
            interactive=False
        )
        
        mock_get_hooks.assert_called_once()
    
    @patch('claude_code_setup.commands.hooks.get_all_hooks_sync')
    def test_list_hooks_invalid_category(self, mock_get_hooks, mock_hook_registry, temp_claude_dir, capsys):
        """Test listing hooks with invalid category."""
        mock_get_hooks.return_value = mock_hook_registry
        
        run_hooks_list_command(
            category="invalid",
            test_dir=str(temp_claude_dir.parent),
            interactive=False
        )
        
        mock_get_hooks.assert_called_once()
    
    @patch('claude_code_setup.commands.hooks.get_all_hooks_sync')
    def test_list_hooks_invalid_event(self, mock_get_hooks, mock_hook_registry, temp_claude_dir, capsys):
        """Test listing hooks with invalid event type."""
        mock_get_hooks.return_value = mock_hook_registry
        
        run_hooks_list_command(
            event="InvalidEvent",
            test_dir=str(temp_claude_dir.parent),
            interactive=False
        )
        
        mock_get_hooks.assert_called_once()


class TestHooksAddCommand:
    """Test hooks add command functionality."""
    
    @patch('claude_code_setup.commands.hooks.get_all_hooks_sync')
    @patch('claude_code_setup.commands.hooks.get_hook_sync')
    @patch('claude_code_setup.commands.hooks.HookInstaller')
    def test_add_specific_hooks(self, mock_installer_class, mock_get_hook, mock_get_hooks, 
                              mock_hook_registry, temp_claude_dir):
        """Test adding specific hooks by name."""
        mock_get_hooks.return_value = mock_hook_registry
        mock_get_hook.return_value = mock_hook_registry.hooks["command-validator"]
        
        # Mock installer
        mock_installer = MagicMock()
        mock_installer_class.return_value = mock_installer
        
        # Mock installation report
        mock_report = MagicMock()
        mock_report.successful_installs = 1
        mock_report.failed_installs = 0
        mock_report.skipped_installs = 0
        mock_report.duration = 0.5
        mock_report.results = [
            MagicMock(success=True, hook_name="command-validator", message="Success")
        ]
        mock_installer.install_hooks.return_value = mock_report
        
        run_hooks_add_command(
            hook_names=("command-validator",),
            test_dir=str(temp_claude_dir.parent),
            interactive=False
        )
        
        mock_get_hook.assert_called_with("command-validator")
        mock_installer.install_hooks.assert_called_once_with(["command-validator"])
    
    @patch('claude_code_setup.commands.hooks.get_all_hooks_sync')
    @patch('claude_code_setup.commands.hooks.get_hook_sync')
    def test_add_nonexistent_hook(self, mock_get_hook, mock_get_hooks, 
                                 mock_hook_registry, temp_claude_dir, capsys):
        """Test adding a hook that doesn't exist."""
        mock_get_hooks.return_value = mock_hook_registry
        mock_get_hook.return_value = None
        
        run_hooks_add_command(
            hook_names=("nonexistent-hook",),
            test_dir=str(temp_claude_dir.parent),
            interactive=False
        )
        
        mock_get_hook.assert_called_with("nonexistent-hook")
    
    @patch('claude_code_setup.commands.hooks.get_all_hooks_sync')
    @patch('claude_code_setup.commands.hooks._interactive_hook_selection')
    @patch('claude_code_setup.commands.hooks.HookInstaller')
    def test_add_hooks_interactive(self, mock_installer_class, mock_interactive, 
                                  mock_get_hooks, mock_hook_registry, temp_claude_dir):
        """Test interactive hook selection and installation."""
        mock_get_hooks.return_value = mock_hook_registry
        mock_interactive.return_value = ["command-validator", "deployment-guard"]
        
        # Mock installer
        mock_installer = MagicMock()
        mock_installer_class.return_value = mock_installer
        
        # Mock installation report
        mock_report = MagicMock()
        mock_report.successful_installs = 2
        mock_report.failed_installs = 0
        mock_report.skipped_installs = 0
        mock_report.duration = 1.0
        mock_report.results = [
            MagicMock(success=True, hook_name="command-validator", message="Success"),
            MagicMock(success=True, hook_name="deployment-guard", message="Success")
        ]
        mock_installer.install_hooks.return_value = mock_report
        
        run_hooks_add_command(
            hook_names=(),
            test_dir=str(temp_claude_dir.parent),
            interactive=True
        )
        
        mock_interactive.assert_called_once()
        mock_installer.install_hooks.assert_called_once_with(["command-validator", "deployment-guard"])
    
    @patch('claude_code_setup.commands.hooks.get_all_hooks_sync')
    @patch('claude_code_setup.commands.hooks._interactive_hook_selection')
    def test_add_hooks_interactive_cancelled(self, mock_interactive, mock_get_hooks, 
                                           mock_hook_registry, temp_claude_dir, capsys):
        """Test cancelling interactive hook selection."""
        mock_get_hooks.return_value = mock_hook_registry
        mock_interactive.return_value = []
        
        run_hooks_add_command(
            hook_names=(),
            test_dir=str(temp_claude_dir.parent),
            interactive=True
        )
        
        mock_interactive.assert_called_once()
    
    def test_add_hooks_no_args_non_interactive(self, temp_claude_dir, capsys):
        """Test adding hooks with no arguments in non-interactive mode."""
        run_hooks_add_command(
            hook_names=(),
            test_dir=str(temp_claude_dir.parent),
            interactive=False
        )


class TestHooksRemoveCommand:
    """Test hooks remove command functionality."""
    
    def test_remove_specific_hooks(self, temp_claude_dir):
        """Test removing specific hooks by name."""
        # Create some installed hooks
        security_dir = temp_claude_dir / "hooks" / "security" / "command-validator"
        security_dir.mkdir(parents=True)
        (security_dir / "metadata.json").write_text(json.dumps({
            "name": "command-validator",
            "description": "Test hook",
            "category": "security"
        }))
        
        with patch('claude_code_setup.commands.hooks.HookInstaller') as mock_installer_class:
            mock_installer = MagicMock()
            mock_installer_class.return_value = mock_installer
            mock_installer.uninstall_hook.return_value = MagicMock(
                success=True, 
                hook_name="command-validator",
                message="Success"
            )
            
            run_hooks_remove_command(
                hook_names=("command-validator",),
                test_dir=str(temp_claude_dir),
                interactive=False,
                force=True
            )
            
            mock_installer.uninstall_hook.assert_called_once_with("command-validator")
    
    def test_remove_nonexistent_hook(self, temp_claude_dir, capsys):
        """Test removing a hook that isn't installed."""
        run_hooks_remove_command(
            hook_names=("nonexistent-hook",),
            test_dir=str(temp_claude_dir.parent),
            interactive=False,
            force=True
        )
    
    def test_remove_all_hooks(self, temp_claude_dir):
        """Test removing all installed hooks."""
        # Create some installed hooks
        security_dir = temp_claude_dir / "hooks" / "security" / "command-validator"
        security_dir.mkdir(parents=True)
        (security_dir / "metadata.json").write_text(json.dumps({
            "name": "command-validator",
            "description": "Test hook",
            "category": "security"
        }))
        
        aws_dir = temp_claude_dir / "hooks" / "aws" / "deployment-guard"
        aws_dir.mkdir(parents=True)
        (aws_dir / "metadata.json").write_text(json.dumps({
            "name": "deployment-guard",
            "description": "AWS guard",
            "category": "aws"
        }))
        
        with patch('claude_code_setup.commands.hooks.HookInstaller') as mock_installer_class:
            mock_installer = MagicMock()
            mock_installer_class.return_value = mock_installer
            mock_installer.uninstall_hook.return_value = MagicMock(
                success=True,
                message="Success"
            )
            
            run_hooks_remove_command(
                hook_names=(),
                all_hooks=True,
                test_dir=str(temp_claude_dir),
                interactive=False,
                force=True
            )
            
            # Should call uninstall for both hooks
            assert mock_installer.uninstall_hook.call_count == 2
    
    @patch('claude_code_setup.commands.hooks._interactive_remove_selection')
    def test_remove_hooks_interactive(self, mock_interactive, temp_claude_dir):
        """Test interactive hook removal selection."""
        # Create some installed hooks
        security_dir = temp_claude_dir / "hooks" / "security" / "command-validator"
        security_dir.mkdir(parents=True)
        (security_dir / "metadata.json").write_text(json.dumps({
            "name": "command-validator",
            "description": "Test hook",
            "category": "security"
        }))
        
        mock_interactive.return_value = ["command-validator"]
        
        with patch('claude_code_setup.commands.hooks.HookInstaller') as mock_installer_class:
            with patch('claude_code_setup.commands.hooks.ConfirmationDialog') as mock_confirm:
                mock_installer = MagicMock()
                mock_installer_class.return_value = mock_installer
                mock_installer.uninstall_hook.return_value = MagicMock(
                    success=True,
                    hook_name="command-validator",
                    message="Success"
                )
                
                mock_confirm.return_value.ask.return_value = True
                
                run_hooks_remove_command(
                    hook_names=(),
                    test_dir=str(temp_claude_dir),
                    interactive=True
                )
                
                mock_interactive.assert_called_once()
                mock_installer.uninstall_hook.assert_called_once_with("command-validator")
    
    def test_remove_no_installed_hooks(self, temp_claude_dir, capsys):
        """Test removing hooks when none are installed."""
        run_hooks_remove_command(
            hook_names=("any-hook",),
            test_dir=str(temp_claude_dir.parent),
            interactive=False
        )


class TestHooksUtilities:
    """Test hooks command utility functions."""
    
    def test_get_installed_hooks_empty(self, temp_claude_dir):
        """Test getting installed hooks when none exist."""
        installed = _get_installed_hooks(temp_claude_dir)
        assert installed == {}
    
    def test_get_installed_hooks_with_metadata(self, temp_claude_dir):
        """Test getting installed hooks with metadata."""
        # Create hook with metadata
        security_dir = temp_claude_dir / "hooks" / "security" / "command-validator"
        security_dir.mkdir(parents=True)
        (security_dir / "metadata.json").write_text(json.dumps({
            "name": "command-validator",
            "description": "Validates bash commands",
            "category": "security",
            "event": "PreToolUse",
            "matcher": "Bash"
        }))
        
        installed = _get_installed_hooks(temp_claude_dir)
        
        assert "command-validator" in installed
        assert installed["command-validator"]["category"] == "security"
        assert installed["command-validator"]["description"] == "Validates bash commands"
    
    def test_get_installed_hooks_without_metadata(self, temp_claude_dir):
        """Test getting installed hooks without metadata files."""
        # Create hook without metadata
        security_dir = temp_claude_dir / "hooks" / "security" / "simple-hook"
        security_dir.mkdir(parents=True)
        (security_dir / "script.py").write_text("print('test')")
        
        installed = _get_installed_hooks(temp_claude_dir)
        
        assert "simple-hook" in installed
        assert installed["simple-hook"]["category"] == "security"
        assert "No description" in installed["simple-hook"]["description"]
    
    @patch('claude_code_setup.commands.hooks.console')
    def test_display_hooks_list(self, mock_console, mock_hook_registry, temp_claude_dir):
        """Test displaying hooks list."""
        hooks_list = list(mock_hook_registry.hooks.values())
        
        _display_hooks_list(hooks_list, temp_claude_dir, interactive=False)
        
        # Verify console.print was called multiple times
        assert mock_console.print.call_count > 0


class TestHooksCommandErrors:
    """Test error handling in hooks commands."""
    
    @patch('claude_code_setup.commands.hooks.get_all_hooks_sync')
    def test_list_hooks_exception(self, mock_get_hooks, temp_claude_dir):
        """Test handling exceptions in hooks list command."""
        mock_get_hooks.side_effect = Exception("Registry error")
        
        with pytest.raises(SystemExit):
            run_hooks_list_command(
                test_dir=str(temp_claude_dir.parent),
                interactive=False
            )
    
    @patch('claude_code_setup.commands.hooks.get_all_hooks_sync')
    def test_add_hooks_exception(self, mock_get_hooks, temp_claude_dir):
        """Test handling exceptions in hooks add command."""
        mock_get_hooks.side_effect = Exception("Registry error")
        
        with pytest.raises(SystemExit):
            run_hooks_add_command(
                hook_names=("test-hook",),
                test_dir=str(temp_claude_dir.parent),
                interactive=False
            )
    
    def test_remove_hooks_exception(self, temp_claude_dir):
        """Test handling exceptions in hooks remove command."""
        with patch('claude_code_setup.commands.hooks._get_installed_hooks') as mock_get:
            mock_get.side_effect = Exception("File system error")
            
            with pytest.raises(SystemExit):
                run_hooks_remove_command(
                    hook_names=("test-hook",),
                    test_dir=str(temp_claude_dir.parent),
                    interactive=False
                )