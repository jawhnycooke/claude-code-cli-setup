"""Command loader for claude-code-setup.

This module provides functionality to dynamically load and register
commands from various sources, enabling a modular and extensible
command architecture.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import importlib.util
import sys

import click
from rich.console import Console

from .registry import CommandRegistry

console = Console()


class CommandLoader:
    """Loads and manages CLI commands from various sources."""
    
    def __init__(self, registry: CommandRegistry) -> None:
        """Initialize the command loader.
        
        Args:
            registry: Command registry to register loaded commands with
        """
        self.registry = registry
        self._loaded_modules: List[str] = []
    
    def load_core_commands(self) -> None:
        """Load core commands from the commands package."""
        core_commands = [
            ('claude_code_setup.commands.init', 'init'),
            ('claude_code_setup.commands.list', 'list'),
            ('claude_code_setup.commands.add', 'add'),
            ('claude_code_setup.commands.update', 'update'),
            ('claude_code_setup.commands.remove', 'remove'),
        ]
        
        for module_path, command_name in core_commands:
            try:
                self._load_command_from_module(module_path, command_name)
            except Exception as e:
                console.print(f"[yellow]Warning: Failed to load {command_name}: {e}[/yellow]")
    
    def load_command_from_file(self, file_path: Path, command_name: str) -> None:
        """Load a command from a Python file.
        
        Args:
            file_path: Path to the Python file
            command_name: Name of the command to load from the file
        """
        try:
            spec = importlib.util.spec_from_file_location(f"dynamic_{command_name}", file_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load spec from {file_path}")
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            
            # Look for the command in the module
            if hasattr(module, command_name):
                command = getattr(module, command_name)
                if isinstance(command, (click.Command, click.Group)):
                    self.registry.register_command(
                        name=command_name,
                        command=command,
                        description=command.help,
                        category='external',
                    )
                    console.print(f"[green]✓ Loaded external command: {command_name}[/green]")
                else:
                    console.print(f"[yellow]Warning: {command_name} is not a Click command[/yellow]")
            else:
                console.print(f"[yellow]Warning: Command {command_name} not found in {file_path}[/yellow]")
        
        except Exception as e:
            console.print(f"[red]Error loading command from {file_path}: {e}[/red]")
    
    def load_commands_from_directory(self, directory: Path, pattern: str = "*.py") -> None:
        """Load commands from all Python files in a directory.
        
        Args:
            directory: Directory to scan for command files
            pattern: File pattern to match (default: "*.py")
        """
        if not directory.exists() or not directory.is_dir():
            console.print(f"[yellow]Warning: Directory {directory} does not exist[/yellow]")
            return
        
        for file_path in directory.glob(pattern):
            if file_path.stem.startswith('_'):
                continue  # Skip private files
            
            command_name = file_path.stem.replace('_', '-')
            self.load_command_from_file(file_path, command_name)
    
    def _load_command_from_module(self, module_path: str, command_name: str) -> None:
        """Load a specific command from a module.
        
        Args:
            module_path: Python module path
            command_name: Name of the command to extract
        """
        if module_path in self._loaded_modules:
            return  # Already loaded
        
        try:
            module = importlib.import_module(module_path)
            self._loaded_modules.append(module_path)
            
            # Look for the run_*_command function
            run_function_name = f"run_{command_name}_command"
            if hasattr(module, run_function_name):
                # We have the command implementation, but we need to create the Click command
                # This is handled by the CLI module, so we just mark it as loaded
                console.print(f"[green]✓ Loaded {command_name} command implementation[/green]")
            else:
                console.print(f"[yellow]Warning: No {run_function_name} found in {module_path}[/yellow]")
        
        except ImportError as e:
            console.print(f"[red]Error loading {module_path}: {e}[/red]")
            raise
    
    def get_command_info(self) -> Dict[str, Any]:
        """Get information about all loaded commands.
        
        Returns:
            Dictionary with command information
        """
        return {
            'loaded_modules': len(self._loaded_modules),
            'registered_commands': len(self.registry.list_commands()),
            'registered_groups': len(self.registry.list_groups()),
            'commands': self.registry.list_commands(),
            'groups': self.registry.list_groups(),
        }
    
    def validate_commands(self) -> bool:
        """Validate that all required commands are loaded.
        
        Returns:
            True if all required commands are present
        """
        required_commands = ['init', 'list']
        missing_commands = []
        
        for cmd_name in required_commands:
            # Check if we have the implementation loaded
            module_path = f"claude_code_setup.commands.{cmd_name}"
            if module_path not in self._loaded_modules:
                missing_commands.append(cmd_name)
        
        if missing_commands:
            console.print(f"[red]Missing required commands: {', '.join(missing_commands)}[/red]")
            return False
        
        console.print("[green]✓ All required commands are loaded[/green]")
        return True


def create_command_loader(registry: CommandRegistry) -> CommandLoader:
    """Create a command loader instance.
    
    Args:
        registry: Command registry to use
    
    Returns:
        CommandLoader instance
    """
    return CommandLoader(registry)