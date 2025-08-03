"""File system utilities for claude-code-setup.

This module provides file system operations for managing Claude Code directories,
templates, and configuration files. Converted from TypeScript fs.ts.
"""

import json
import shutil
from pathlib import Path
from typing import Any, Optional

# Claude Code home directory paths
CLAUDE_HOME = Path.home() / ".claude"
CLAUDE_COMMANDS_DIR = CLAUDE_HOME / "commands"
CLAUDE_SETTINGS_FILE = CLAUDE_HOME / "settings.json"
CLAUDE_HOOKS_DIR = CLAUDE_HOME / "hooks"


async def ensure_claude_directories(target_dir: Optional[str] = None) -> None:
    """Ensure Claude Code directory structure exists.

    Args:
        target_dir: Optional custom directory to create structure in.
                   If None, uses default home directory structure.
    """
    if target_dir:
        # If custom directory is specified, ensure the commands and hooks directories within it
        target_path = Path(target_dir)
        commands_dir = target_path / "commands"
        hooks_dir = target_path / "hooks"

        commands_dir.mkdir(parents=True, exist_ok=True)
        hooks_dir.mkdir(parents=True, exist_ok=True)
    else:
        # Default Claude directories in home
        CLAUDE_HOME.mkdir(parents=True, exist_ok=True)
        CLAUDE_COMMANDS_DIR.mkdir(parents=True, exist_ok=True)
        CLAUDE_HOOKS_DIR.mkdir(parents=True, exist_ok=True)


async def template_exists(
    template_name: str, category: Optional[str] = None, target_dir: Optional[str] = None
) -> bool:
    """Check if a template exists in Claude Code directory.

    Args:
        template_name: Name of the template to check
        category: Optional category subdirectory
        target_dir: Optional custom directory to check in

    Returns:
        True if template exists, False otherwise
    """
    if target_dir:
        # If custom directory, use the commands directory within it
        commands_dir = Path(target_dir) / "commands"
    else:
        # Default Claude commands directory
        commands_dir = CLAUDE_COMMANDS_DIR

    if category:
        template_path = commands_dir / category / f"{template_name}.md"
    else:
        template_path = commands_dir / f"{template_name}.md"

    return template_path.exists()


async def write_template(
    template_name: str,
    content: str,
    category: Optional[str] = None,
    target_dir: Optional[str] = None,
) -> None:
    """Write a template to Claude Code directory.

    Args:
        template_name: Name of the template file (without .md extension)
        content: Template content to write
        category: Optional category subdirectory
        target_dir: Optional custom directory to write to
    """
    if target_dir:
        # If custom directory, use the commands directory within it
        commands_dir = Path(target_dir) / "commands"
    else:
        # Default Claude commands directory
        commands_dir = CLAUDE_COMMANDS_DIR

    if category:
        target_dir_path = commands_dir / category
    else:
        target_dir_path = commands_dir

    # Ensure target directory exists
    target_dir_path.mkdir(parents=True, exist_ok=True)

    # Write template file
    target_path = target_dir_path / f"{template_name}.md"
    target_path.write_text(content, encoding="utf-8")


async def read_template(
    template_name: str, category: Optional[str] = None, target_dir: Optional[str] = None
) -> Optional[str]:
    """Read a template from Claude Code directory.

    Args:
        template_name: Name of the template to read
        category: Optional category subdirectory
        target_dir: Optional custom directory to read from

    Returns:
        Template content as string, or None if not found
    """
    if target_dir:
        # If custom directory, use the commands directory within it
        commands_dir = Path(target_dir) / "commands"
    else:
        # Default Claude commands directory
        commands_dir = CLAUDE_COMMANDS_DIR

    if category:
        template_path = commands_dir / category / f"{template_name}.md"
    else:
        template_path = commands_dir / f"{template_name}.md"

    if template_path.exists():
        return template_path.read_text(encoding="utf-8")

    return None


def template_exists_sync(
    template_name: str, category: Optional[str] = None, target_dir: Optional[str] = None
) -> bool:
    """Synchronous version of template_exists."""
    if target_dir:
        commands_dir = Path(target_dir) / "commands"
    else:
        commands_dir = CLAUDE_COMMANDS_DIR

    if category:
        template_path = commands_dir / category / f"{template_name}.md"
    else:
        template_path = commands_dir / f"{template_name}.md"

    return template_path.exists()


def write_template_sync(
    template_name: str,
    content: str,
    category: Optional[str] = None,
    target_dir: Optional[str] = None,
) -> None:
    """Synchronous version of write_template."""
    if target_dir:
        commands_dir = Path(target_dir) / "commands"
    else:
        commands_dir = CLAUDE_COMMANDS_DIR

    if category:
        target_dir_path = commands_dir / category
    else:
        target_dir_path = commands_dir

    # Ensure target directory exists
    target_dir_path.mkdir(parents=True, exist_ok=True)

    # Write template file
    target_path = target_dir_path / f"{template_name}.md"
    target_path.write_text(content, encoding="utf-8")


def read_template_sync(
    template_name: str, category: Optional[str] = None, target_dir: Optional[str] = None
) -> Optional[str]:
    """Synchronous version of read_template."""
    if target_dir:
        commands_dir = Path(target_dir) / "commands"
    else:
        commands_dir = CLAUDE_COMMANDS_DIR

    if category:
        template_path = commands_dir / category / f"{template_name}.md"
    else:
        template_path = commands_dir / f"{template_name}.md"

    if template_path.exists():
        return template_path.read_text(encoding="utf-8")

    return None


def get_default_settings() -> dict[str, Any]:
    """Get the default settings.json content.

    Returns:
        Dictionary containing default Claude Code settings
    """
    return {
        "permissions": {
            "allow": [
                "Bash(uv:*)",
                "Bash(uvx:*)",
                "Bash(python:*)",
                "Bash(pip:*)",
                "Bash(venv:*)",
                "Bash(conda:*)",
                "Bash(poetry:*)",
                "Bash(pdm:*)",
                "Bash(pyenv:*)",
                "Bash(black:*)",
                "Bash(isort:*)",
                "Bash(mypy:*)",
                "Bash(ruff:*)",
                "Bash(flake8:*)",
                "Bash(pylint:*)",
                "Bash(bandit:*)",
                "Bash(pycodestyle:*)",
                "Bash(pydocstyle:*)",
                "Bash(pytest:*)",
                "Bash(coverage:*)",
                "Bash(tox:*)",
                "Bash(hypothesis:*)",
                "Bash(pdb:*)",
                "Bash(ipdb:*)",
                "Bash(npm:*)",
                "Bash(npx:*)",
                "Bash(node:*)",
                "Bash(yarn:*)",
                "Bash(pnpm:*)",
                "Bash(bun:*)",
                "Bash(git:*)",
                "Bash(gh:*)",
                "Bash(pre-commit:*)",
                "Bash(ls:*)",
                "Bash(find:*)",
                "Bash(grep:*)",
                "Bash(cat:*)",
                "Bash(touch:*)",
                "Bash(mkdir:*)",
                "Bash(rm:*)",
                "Bash(cd:*)",
                "Bash(pwd:*)",
                "Bash(echo:*)",
                "Bash(sed:*)",
                "Bash(awk:*)",
                "Bash(jq:*)",
            ]
        }
    }


def ensure_claude_directories_sync(target_dir: Optional[str] = None) -> None:
    """Synchronous version of ensure_claude_directories for non-async contexts.

    Args:
        target_dir: Optional custom directory to create structure in.
                   If None, uses default home directory structure.
    """
    if target_dir:
        # If custom directory is specified, ensure the commands and hooks directories within it
        target_path = Path(target_dir)
        commands_dir = target_path / "commands"
        hooks_dir = target_path / "hooks"

        commands_dir.mkdir(parents=True, exist_ok=True)
        hooks_dir.mkdir(parents=True, exist_ok=True)
    else:
        # Default Claude directories in home
        CLAUDE_HOME.mkdir(parents=True, exist_ok=True)
        CLAUDE_COMMANDS_DIR.mkdir(parents=True, exist_ok=True)
        CLAUDE_HOOKS_DIR.mkdir(parents=True, exist_ok=True)


def ensure_directory(directory: Path) -> None:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Path to the directory
    """
    directory.mkdir(parents=True, exist_ok=True)


def read_json_file(file_path: Path) -> dict[str, Any]:
    """Read and parse a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON data as a dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json_file(file_path: Path, data: dict[str, Any], indent: int = 2) -> None:
    """Write data to a JSON file.
    
    Args:
        file_path: Path to write the JSON file
        data: Data to serialize to JSON
        indent: JSON indentation level (default: 2)
    """
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def copy_hook_with_permissions(source_path: Path, target_path: Path) -> None:
    """Copy a hook file with proper executable permissions.

    Args:
        source_path: Source file path
        target_path: Target file path
    """
    # Ensure target directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Copy the file
    shutil.copy2(source_path, target_path)

    # Set executable permissions for shell scripts
    if target_path.suffix in {".sh", ".py"}:
        # Make executable for owner, group, and others (755)
        target_path.chmod(0o755)
