"""Tests for the command registration system."""

import pytest
from unittest.mock import Mock, patch

from claude_code_setup.core.registry import CommandRegistry, get_registry
from claude_code_setup.core.loader import CommandLoader, create_command_loader
import click


class TestCommandRegistry:
    """Test the CommandRegistry class."""
    
    def test_registry_initialization(self):
        """Test that registry initializes correctly."""
        registry = CommandRegistry()
        assert len(registry.list_commands()) == 0
        assert len(registry.list_groups()) == 0
    
    def test_register_command(self):
        """Test command registration."""
        registry = CommandRegistry()
        
        @click.command()
        def test_command():
            """Test command."""
            pass
        
        registry.register_command(
            name="test",
            command=test_command,
            description="Test command",
            category="test"
        )
        
        assert "test" in registry.list_commands()
        assert registry.get_command("test") == test_command
        metadata = registry.get_command_metadata("test")
        assert metadata["description"] == "Test command"
        assert metadata["category"] == "test"
    
    def test_register_group(self):
        """Test group registration."""
        registry = CommandRegistry()
        
        @click.group()
        def test_group():
            """Test group."""
            pass
        
        registry.register_group(
            name="testgroup",
            group=test_group,
            description="Test group"
        )
        
        assert "testgroup" in registry.list_groups()
        assert registry.get_group("testgroup") == test_group
    
    def test_get_commands_by_category(self):
        """Test filtering commands by category."""
        registry = CommandRegistry()
        
        @click.command()
        def cmd1():
            pass
        
        @click.command()
        def cmd2():
            pass
        
        registry.register_command("cmd1", cmd1, category="core")
        registry.register_command("cmd2", cmd2, category="external")
        
        core_commands = registry.get_commands_by_category("core")
        assert "cmd1" in core_commands
        assert "cmd2" not in core_commands
    
    def test_attach_to_cli(self):
        """Test attaching commands to CLI."""
        registry = CommandRegistry()
        
        @click.command()
        def test_cmd():
            pass
        
        @click.group()
        def test_group():
            pass
        
        registry.register_command("test", test_cmd)
        registry.register_group("group", test_group)
        
        cli_mock = Mock()
        registry.attach_to_cli(cli_mock)
        
        # Should have called add_command twice
        assert cli_mock.add_command.call_count == 2


class TestCommandLoader:
    """Test the CommandLoader class."""
    
    def test_loader_initialization(self):
        """Test that loader initializes correctly."""
        registry = CommandRegistry()
        loader = CommandLoader(registry)
        
        assert loader.registry == registry
        assert len(loader._loaded_modules) == 0
    
    def test_create_command_loader(self):
        """Test the factory function."""
        registry = CommandRegistry()
        loader = create_command_loader(registry)
        
        assert isinstance(loader, CommandLoader)
        assert loader.registry == registry
    
    @patch('claude_code_setup.core.loader.importlib.import_module')
    def test_load_core_commands(self, mock_import):
        """Test loading core commands."""
        registry = CommandRegistry()
        loader = CommandLoader(registry)
        
        # Mock the module imports
        mock_init_module = Mock()
        mock_init_module.run_init_command = Mock()
        mock_list_module = Mock()
        mock_list_module.run_list_command = Mock()
        
        def side_effect(module_path):
            if module_path == 'claude_code_setup.commands.init':
                return mock_init_module
            elif module_path == 'claude_code_setup.commands.list':
                return mock_list_module
            raise ImportError(f"No module named '{module_path}'")
        
        mock_import.side_effect = side_effect
        
        loader.load_core_commands()
        
        # Should have tried to import all core modules
        expected_calls = [
            ('claude_code_setup.commands.init',),
            ('claude_code_setup.commands.list',),
            ('claude_code_setup.commands.add',),
            ('claude_code_setup.commands.update',),
            ('claude_code_setup.commands.remove',),
        ]
        actual_calls = [call[0] for call in mock_import.call_args_list]
        assert actual_calls == expected_calls
    
    def test_validate_commands_success(self):
        """Test command validation when all required commands are loaded."""
        registry = CommandRegistry()
        loader = CommandLoader(registry)
        
        # Manually add the required modules to simulate successful loading
        loader._loaded_modules = [
            'claude_code_setup.commands.init',
            'claude_code_setup.commands.list',
            'claude_code_setup.commands.add',
            'claude_code_setup.commands.update',
            'claude_code_setup.commands.remove',
        ]
        
        assert loader.validate_commands() is True
    
    def test_validate_commands_failure(self):
        """Test command validation when required commands are missing."""
        registry = CommandRegistry()
        loader = CommandLoader(registry)
        
        # Don't load any modules
        assert loader.validate_commands() is False
    
    def test_get_command_info(self):
        """Test getting command information."""
        registry = CommandRegistry()
        loader = CommandLoader(registry)
        
        # Add some test data
        loader._loaded_modules = ['test.module']
        
        @click.command()
        def test_cmd():
            pass
        
        registry.register_command("test", test_cmd)
        
        info = loader.get_command_info()
        
        assert info['loaded_modules'] == 1
        assert info['registered_commands'] == 1
        assert info['registered_groups'] == 0
        assert 'test' in info['commands']


class TestGlobalRegistry:
    """Test the global registry functionality."""
    
    def test_get_registry(self):
        """Test getting the global registry instance."""
        registry1 = get_registry()
        registry2 = get_registry()
        
        # Should return the same instance
        assert registry1 is registry2
    
    def test_register_command_decorator(self):
        """Test the register_command decorator."""
        from claude_code_setup.core.registry import register_command
        
        @register_command(
            name="decorated_cmd",
            description="Decorated command",
            category="test"
        )
        @click.command()
        def decorated_command():
            """A decorated command."""
            pass
        
        # Check that it was registered
        registry = get_registry()
        assert "decorated_cmd" in registry.list_commands()
        
        # Clean up for other tests
        if "decorated_cmd" in registry._commands:
            del registry._commands["decorated_cmd"]
        if "decorated_cmd" in registry._command_metadata:
            del registry._command_metadata["decorated_cmd"]
    
    def test_register_group_decorator(self):
        """Test the register_group decorator."""
        from claude_code_setup.core.registry import register_group
        
        @register_group(
            name="decorated_group",
            description="Decorated group"
        )
        @click.group()
        def decorated_group():
            """A decorated group."""
            pass
        
        # Check that it was registered
        registry = get_registry()
        assert "decorated_group" in registry.list_groups()
        
        # Clean up for other tests
        if "decorated_group" in registry._command_groups:
            del registry._command_groups["decorated_group"]
        if "decorated_group" in registry._command_metadata:
            del registry._command_metadata["decorated_group"]


class TestIntegration:
    """Integration tests for the command registration system."""
    
    @patch('claude_code_setup.core.loader.console')
    def test_registry_and_loader_integration(self, mock_console):
        """Test that registry and loader work together."""
        registry = CommandRegistry()
        loader = CommandLoader(registry)
        
        # Test loading with error handling
        with patch('claude_code_setup.core.loader.importlib.import_module') as mock_import:
            mock_import.side_effect = ImportError("Module not found")
            
            loader.load_core_commands()
            
            # Should have printed warning messages
            assert mock_console.print.called
            
            # Validation should fail
            assert loader.validate_commands() is False
    
    def test_command_info_structure(self):
        """Test the structure of command info returned by loader."""
        registry = CommandRegistry()
        loader = CommandLoader(registry)
        
        info = loader.get_command_info()
        
        # Check structure
        required_keys = ['loaded_modules', 'registered_commands', 'registered_groups', 'commands', 'groups']
        for key in required_keys:
            assert key in info
        
        # Check types
        assert isinstance(info['loaded_modules'], int)
        assert isinstance(info['registered_commands'], int)
        assert isinstance(info['registered_groups'], int)
        assert isinstance(info['commands'], list)
        assert isinstance(info['groups'], list)