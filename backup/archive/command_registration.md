# Command Registration System

The command registration system provides a modular architecture for managing CLI commands in claude-code-setup, similar to how the TypeScript version uses Commander.js with separate command modules.

## Overview

The system consists of three main components:

1. **CommandRegistry**: Centralized registry for managing commands and their metadata
2. **CommandLoader**: Dynamic loader for discovering and loading commands from modules
3. **ExtensionManager**: Manager for loading external commands and plugins

## Architecture

```
CLI Entry Point (cli.py)
    ↓
CommandRegistry ← CommandLoader → Command Modules
    ↓                                (init.py, list.py, etc.)
ExtensionManager ← User Extensions
    ↓                 (.claude/extensions/)
Registered Commands
```

## Core Components

### CommandRegistry

The `CommandRegistry` class manages all registered commands and groups:

```python
from claude_code_setup.core.registry import CommandRegistry

registry = CommandRegistry()

# Register a command
registry.register_command(
    name="my-command",
    command=my_click_command,
    description="My custom command",
    category="custom"
)

# Get commands by category
core_commands = registry.get_commands_by_category("core")
```

### CommandLoader

The `CommandLoader` class dynamically loads commands from Python modules:

```python
from claude_code_setup.core.loader import CommandLoader

loader = CommandLoader(registry)

# Load core commands
loader.load_core_commands()

# Load command from file
loader.load_command_from_file(Path("my_command.py"), "my-command")

# Validate required commands
if loader.validate_commands():
    print("All required commands loaded!")
```

### ExtensionManager

The `ExtensionManager` class supports loading external commands:

```python
from claude_code_setup.core.extensions import ExtensionManager

ext_manager = ExtensionManager(registry, loader)

# Load extensions from user directories
ext_count = ext_manager.discover_user_extensions()

# Load specific extension file
ext_manager.load_extension_from_file(Path("my_extension.py"))
```

## Creating Commands

### Method 1: Direct Registration

```python
import click
from claude_code_setup.core.registry import get_registry

@click.command()
@click.argument('name')
def hello(name: str) -> None:
    \"\"\"Say hello to someone.\"\"\"
    click.echo(f"Hello, {name}!")

# Register the command
registry = get_registry()
registry.register_command(
    name="hello",
    command=hello,
    description="Greet someone",
    category="examples"
)
```

### Method 2: Decorator Registration

```python
import click
from claude_code_setup.core.registry import register_command

@register_command(
    name="goodbye",
    description="Say goodbye",
    category="examples"
)
@click.command()
@click.argument('name')
def goodbye(name: str) -> None:
    \"\"\"Say goodbye to someone.\"\"\"
    click.echo(f"Goodbye, {name}!")
```

### Method 3: Module-based Commands

Create a Python module with command functions:

```python
# src/claude_code_setup/commands/my_command.py

import click
from rich.console import Console

console = Console()

def run_my_command_command(arg1: str, flag: bool) -> None:
    \"\"\"Implementation of my-command.\"\"\"
    console.print(f"Running my command with {arg1}, flag={flag}")

# The CLI framework will automatically create a Click command
# that calls run_my_command_command with the appropriate arguments
```

## Extension System

### Creating Extensions

Extensions are Python files that define Click commands or groups:

```python
# ~/.claude/extensions/my_extension.py

import click
from rich.console import Console

console = Console()

@click.command()
@click.argument('message')
def custom_command(message: str) -> None:
    \"\"\"My custom extension command.\"\"\"
    console.print(f"[green]Extension says: {message}[/green]")

@click.group()
def tools() -> None:
    \"\"\"Custom tools group.\"\"\"
    pass

@tools.command()
def analyze() -> None:
    \"\"\"Analyze something.\"\"\"
    console.print("[blue]Analyzing...[/blue]")
```

### Extension Discovery

Extensions are automatically discovered from:

1. `~/.claude/extensions/` - Global user extensions
2. `.claude/extensions/` - Project-specific extensions

### Extension Loading

Extensions are loaded at CLI startup:

```bash
$ claude-setup --help
✓ Loaded init command implementation
✓ Loaded list command implementation
✓ All required commands are loaded
✓ Loaded 2 user extensions
✓ Command registration system initialized
```

## Integration with CLI

The command registration system is integrated into the main CLI:

```python
# cli.py
from .core.registry import get_registry
from .core.loader import create_command_loader
from .core.extensions import create_extension_manager

# Initialize system
registry = get_registry()
loader = create_command_loader(registry)
extension_manager = create_extension_manager(registry, loader)

def load_commands() -> None:
    \"\"\"Load all commands and extensions.\"\"\"
    # Load core commands
    loader.load_core_commands()
    
    # Load user extensions
    ext_count = extension_manager.discover_user_extensions()
    
    # Validate
    loader.validate_commands()
```

## Command Categories

Commands are organized by category:

- **core**: Built-in commands (init, list, add, update, remove)
- **hooks**: Hook management commands
- **extension**: User-defined extension commands
- **external**: Dynamically loaded commands

## Metadata System

Each command can have associated metadata:

```python
registry.register_command(
    name="my-command",
    command=my_command,
    description="Description shown in help",
    category="custom",
    aliases=["mc", "mycmd"]  # Alternative names
)

# Retrieve metadata
metadata = registry.get_command_metadata("my-command")
print(metadata["description"])  # "Description shown in help"
print(metadata["category"])     # "custom"
print(metadata["aliases"])      # ["mc", "mycmd"]
```

## TypeScript Compatibility

This system mirrors the TypeScript Commander.js structure:

| TypeScript | Python |
|------------|--------|
| `commander.js` program | `CommandRegistry` |
| Dynamic imports | `CommandLoader` |
| Command modules | Command modules |
| Plugin system | `ExtensionManager` |

## Testing

The command registration system includes comprehensive tests:

```bash
# Run registration system tests
uv run pytest tests/test_command_registration.py -v

# Test CLI integration
uv run claude-setup --help
```

## Best Practices

1. **Use categories** to organize related commands
2. **Provide descriptions** for all commands
3. **Follow naming conventions** (kebab-case for command names)
4. **Include comprehensive help text** in command docstrings
5. **Handle errors gracefully** in command implementations
6. **Use Rich console** for consistent output formatting

## Future Enhancements

The modular design allows for future enhancements:

- Plugin marketplace integration
- Command versioning and compatibility
- Automatic command updates
- Command performance monitoring
- Custom command templates
- Integration with external CLI tools

## Examples

See the `examples/` directory for complete examples of:

- Custom command implementations
- Extension development
- Plugin architecture
- Command testing patterns