"""Command registration system for claude-code-setup.

This module provides a centralized command registration system that allows
for modular command loading and extensibility, similar to the TypeScript
Commander.js structure.
"""

from typing import Dict, List, Callable, Any, Optional
import importlib
from pathlib import Path

import click
from rich.console import Console

console = Console()


class CommandRegistry:
    """Registry for managing CLI commands and their metadata."""
    
    def __init__(self) -> None:
        self._commands: Dict[str, click.Command] = {}
        self._command_groups: Dict[str, click.Group] = {}
        self._command_metadata: Dict[str, Dict[str, Any]] = {}
    
    def register_command(
        self,
        name: str,
        command: click.Command,
        description: Optional[str] = None,
        category: Optional[str] = None,
        aliases: Optional[List[str]] = None,
    ) -> None:
        """Register a command with the registry.
        
        Args:
            name: Command name
            command: Click command object
            description: Command description
            category: Command category (e.g., 'core', 'templates', 'hooks')
            aliases: List of command aliases
        """
        self._commands[name] = command
        self._command_metadata[name] = {
            'description': description or command.help or '',
            'category': category or 'core',
            'aliases': aliases or [],
        }
    
    def register_group(
        self,
        name: str,
        group: click.Group,
        description: Optional[str] = None,
        category: Optional[str] = None,
    ) -> None:
        """Register a command group with the registry.
        
        Args:
            name: Group name
            group: Click group object
            description: Group description
            category: Group category
        """
        self._command_groups[name] = group
        self._command_metadata[name] = {
            'description': description or group.help or '',
            'category': category or 'core',
            'type': 'group',
        }
    
    def get_command(self, name: str) -> Optional[click.Command]:
        """Get a command by name."""
        return self._commands.get(name)
    
    def get_group(self, name: str) -> Optional[click.Group]:
        """Get a command group by name."""
        return self._command_groups.get(name)
    
    def get_all_commands(self) -> Dict[str, click.Command]:
        """Get all registered commands."""
        return self._commands.copy()
    
    def get_all_groups(self) -> Dict[str, click.Group]:
        """Get all registered command groups."""
        return self._command_groups.copy()
    
    def get_commands_by_category(self, category: str) -> Dict[str, click.Command]:
        """Get all commands in a specific category."""
        return {
            name: cmd for name, cmd in self._commands.items()
            if self._command_metadata.get(name, {}).get('category') == category
        }
    
    def get_command_metadata(self, name: str) -> Dict[str, Any]:
        """Get metadata for a command."""
        return self._command_metadata.get(name, {}).copy()
    
    def list_commands(self) -> List[str]:
        """List all registered command names."""
        return list(self._commands.keys())
    
    def list_groups(self) -> List[str]:
        """List all registered group names."""
        return list(self._command_groups.keys())
    
    def attach_to_cli(self, cli: click.Group) -> None:
        """Attach all registered commands and groups to a CLI group.
        
        Args:
            cli: The main CLI group to attach commands to
        """
        # Attach commands
        for name, command in self._commands.items():
            cli.add_command(command, name=name)
        
        # Attach groups
        for name, group in self._command_groups.items():
            cli.add_command(group, name=name)
    
    def load_commands_from_module(self, module_path: str) -> None:
        """Load commands from a Python module.
        
        Args:
            module_path: Python module path (e.g., 'claude_code_setup.commands.init')
        """
        try:
            module = importlib.import_module(module_path)
            
            # Look for commands and groups in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                if isinstance(attr, click.Command) and not isinstance(attr, click.Group):
                    # Register command
                    self.register_command(
                        name=attr_name.replace('_', '-'),
                        command=attr,
                        description=attr.help,
                        category=getattr(module, 'COMMAND_CATEGORY', 'core'),
                    )
                elif isinstance(attr, click.Group):
                    # Register group
                    self.register_group(
                        name=attr_name.replace('_', '-'),
                        group=attr,
                        description=attr.help,
                        category=getattr(module, 'COMMAND_CATEGORY', 'core'),
                    )
            
        except ImportError as e:
            console.print(f"[yellow]Warning: Could not load commands from {module_path}: {e}[/yellow]")
    
    def auto_discover_commands(self, base_package: str) -> None:
        """Auto-discover and load commands from a package.
        
        Args:
            base_package: Base package path (e.g., 'claude_code_setup.commands')
        """
        try:
            # Import the base package
            package = importlib.import_module(base_package)
            package_path = Path(package.__file__).parent
            
            # Find all Python files in the package
            for py_file in package_path.glob('*.py'):
                if py_file.name.startswith('_'):
                    continue  # Skip private modules
                
                module_name = py_file.stem
                full_module_path = f"{base_package}.{module_name}"
                
                self.load_commands_from_module(full_module_path)
        
        except ImportError as e:
            console.print(f"[yellow]Warning: Could not auto-discover commands in {base_package}: {e}[/yellow]")


# Global command registry instance
registry = CommandRegistry()


def register_command(
    name: str,
    description: Optional[str] = None,
    category: Optional[str] = None,
    aliases: Optional[List[str]] = None,
) -> Callable[[click.Command], click.Command]:
    """Decorator to register a command with the global registry.
    
    Args:
        name: Command name
        description: Command description
        category: Command category
        aliases: Command aliases
    
    Returns:
        Decorator function
    """
    def decorator(command: click.Command) -> click.Command:
        registry.register_command(
            name=name,
            command=command,
            description=description,
            category=category,
            aliases=aliases,
        )
        return command
    
    return decorator


def register_group(
    name: str,
    description: Optional[str] = None,
    category: Optional[str] = None,
) -> Callable[[click.Group], click.Group]:
    """Decorator to register a command group with the global registry.
    
    Args:
        name: Group name
        description: Group description
        category: Group category
    
    Returns:
        Decorator function
    """
    def decorator(group: click.Group) -> click.Group:
        registry.register_group(
            name=name,
            group=group,
            description=description,
            category=category,
        )
        return group
    
    return decorator


def get_registry() -> CommandRegistry:
    """Get the global command registry instance."""
    return registry