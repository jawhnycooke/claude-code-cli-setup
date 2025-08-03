"""Extension system for claude-code-setup CLI.

This module demonstrates how the command registration system can be extended
to support dynamic loading of external commands and plugins.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
import importlib.util
import sys

import click
from rich.console import Console

from .registry import CommandRegistry
from .loader import CommandLoader

console = Console()


class ExtensionManager:
    """Manages external command extensions and plugins."""
    
    def __init__(self, registry: CommandRegistry, loader: CommandLoader) -> None:
        """Initialize the extension manager.
        
        Args:
            registry: Command registry to register extensions with
            loader: Command loader for loading extension modules
        """
        self.registry = registry
        self.loader = loader
        self._loaded_extensions: List[str] = []
    
    def load_extension_from_file(self, file_path: Path) -> bool:
        """Load an extension from a Python file.
        
        Args:
            file_path: Path to the extension Python file
            
        Returns:
            True if extension was loaded successfully
        """
        try:
            if not file_path.exists() or not file_path.suffix == '.py':
                console.print(f"[yellow]Warning: {file_path} is not a valid Python file[/yellow]")
                return False
            
            # Load the module
            spec = importlib.util.spec_from_file_location(f"extension_{file_path.stem}", file_path)
            if spec is None or spec.loader is None:
                console.print(f"[red]Error: Could not load spec from {file_path}[/red]")
                return False
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            
            # Look for commands and groups in the module
            loaded_count = 0
            for attr_name in dir(module):
                if attr_name.startswith('_'):
                    continue
                
                attr = getattr(module, attr_name)
                
                if isinstance(attr, click.Command) and not isinstance(attr, click.Group):
                    # Register command
                    command_name = getattr(attr, 'name', attr_name.replace('_', '-'))
                    self.registry.register_command(
                        name=command_name,
                        command=attr,
                        description=attr.help or f"External command from {file_path.name}",
                        category='extension',
                    )
                    loaded_count += 1
                    console.print(f"[green]✓ Loaded extension command: {command_name}[/green]")
                    
                elif isinstance(attr, click.Group):
                    # Register group
                    group_name = getattr(attr, 'name', attr_name.replace('_', '-'))
                    self.registry.register_group(
                        name=group_name,
                        group=attr,
                        description=attr.help or f"External group from {file_path.name}",
                        category='extension',
                    )
                    loaded_count += 1
                    console.print(f"[green]✓ Loaded extension group: {group_name}[/green]")
            
            if loaded_count > 0:
                self._loaded_extensions.append(str(file_path))
                console.print(f"[green]✓ Extension loaded: {file_path.name} ({loaded_count} commands)[/green]")
                return True
            else:
                console.print(f"[yellow]Warning: No commands found in {file_path}[/yellow]")
                return False
                
        except Exception as e:
            console.print(f"[red]Error loading extension from {file_path}: {e}[/red]")
            return False
    
    def load_extensions_from_directory(self, directory: Path, pattern: str = "*.py") -> int:
        """Load all extensions from a directory.
        
        Args:
            directory: Directory to scan for extension files
            pattern: File pattern to match (default: "*.py")
            
        Returns:
            Number of extensions successfully loaded
        """
        if not directory.exists() or not directory.is_dir():
            console.print(f"[yellow]Warning: Extension directory {directory} does not exist[/yellow]")
            return 0
        
        loaded_count = 0
        for file_path in directory.glob(pattern):
            if file_path.stem.startswith('_'):
                continue  # Skip private files
            
            if self.load_extension_from_file(file_path):
                loaded_count += 1
        
        if loaded_count > 0:
            console.print(f"[green]✓ Loaded {loaded_count} extensions from {directory}[/green]")
        
        return loaded_count
    
    def discover_user_extensions(self) -> int:
        """Discover and load user extensions from standard locations.
        
        Returns:
            Number of extensions loaded
        """
        total_loaded = 0
        
        # Look for extensions in ~/.claude/extensions/
        user_claude_dir = Path.home() / '.claude' / 'extensions'
        if user_claude_dir.exists():
            total_loaded += self.load_extensions_from_directory(user_claude_dir)
        
        # Look for extensions in current project .claude/extensions/
        project_claude_dir = Path.cwd() / '.claude' / 'extensions'
        if project_claude_dir.exists():
            total_loaded += self.load_extensions_from_directory(project_claude_dir)
        
        return total_loaded
    
    def get_extension_info(self) -> Dict[str, Any]:
        """Get information about loaded extensions.
        
        Returns:
            Dictionary with extension information
        """
        extension_commands = self.registry.get_commands_by_category('extension')
        extension_groups = {
            name: group for name, group in self.registry.get_all_groups().items()
            if self.registry.get_command_metadata(name).get('category') == 'extension'
        }
        
        return {
            'loaded_extensions': len(self._loaded_extensions),
            'extension_commands': len(extension_commands),
            'extension_groups': len(extension_groups),
            'extension_files': self._loaded_extensions,
            'commands': list(extension_commands.keys()),
            'groups': list(extension_groups.keys()),
        }
    
    def list_extensions(self) -> None:
        """Display information about loaded extensions."""
        info = self.get_extension_info()
        
        if info['loaded_extensions'] == 0:
            console.print("[dim]No extensions loaded[/dim]")
            return
        
        console.print(f"[bold cyan]Loaded Extensions ({info['loaded_extensions']})[/bold cyan]")
        
        if info['commands']:
            console.print("\n[bold]Extension Commands:[/bold]")
            for cmd_name in info['commands']:
                metadata = self.registry.get_command_metadata(cmd_name)
                console.print(f"  • {cmd_name} - {metadata.get('description', 'No description')}")
        
        if info['groups']:
            console.print("\n[bold]Extension Groups:[/bold]")
            for group_name in info['groups']:
                metadata = self.registry.get_command_metadata(group_name)
                console.print(f"  • {group_name} - {metadata.get('description', 'No description')}")
        
        console.print(f"\n[dim]Loaded from: {', '.join(Path(f).name for f in info['extension_files'])}[/dim]")


def create_extension_manager(registry: CommandRegistry, loader: CommandLoader) -> ExtensionManager:
    """Create an extension manager instance.
    
    Args:
        registry: Command registry to use
        loader: Command loader to use
    
    Returns:
        ExtensionManager instance
    """
    return ExtensionManager(registry, loader)


# Example extension command for demonstration
@click.command()
@click.argument('message', default='Hello from extension!')
def example_extension_command(message: str) -> None:
    """Example extension command to demonstrate the system."""
    console.print(f"[green]🔌 Extension says: {message}[/green]")


# This would be automatically discovered if this module was in an extensions directory
if __name__ == '__main__':
    # Demo usage
    from .registry import get_registry
    from .loader import create_command_loader
    
    registry = get_registry()
    loader = create_command_loader(registry)
    ext_manager = create_extension_manager(registry, loader)
    
    # Register the example command
    registry.register_command(
        name='example-ext',
        command=example_extension_command,
        description='Example extension command',
        category='extension'
    )
    
    ext_manager.list_extensions()