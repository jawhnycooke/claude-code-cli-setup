"""Version utilities for claude-code-setup."""

import importlib.metadata

from rich.console import Console
from rich.panel import Panel

from . import __version__
from .constants import APP_NAME, REPO_URL

console = Console()


def get_version() -> str:
    """Get the current version of claude-code-setup."""
    try:
        # Try to get version from installed package metadata
        return importlib.metadata.version("claude-code-setup")
    except importlib.metadata.PackageNotFoundError:
        # Fallback to hardcoded version
        return __version__


def show_version_info(verbose: bool = False) -> None:
    """Show version information with optional verbose details."""
    version = get_version()

    if not verbose:
        console.print(f"{APP_NAME}, version {version}")
        return

    # Verbose version info
    version_info = [
        f"[bold]{APP_NAME}[/bold] version [cyan]{version}[/cyan]",
        "",
        f"Repository: [link]{REPO_URL}[/link]",
        "Python package: [dim]claude-code-setup[/dim]",
    ]

    # Try to get additional package info
    try:
        metadata = importlib.metadata.metadata("claude-code-setup")
        if metadata.get("Author"):
            version_info.append(f"Author: [dim]{metadata['Author']}[/dim]")
        if metadata.get("License"):
            version_info.append(f"License: [dim]{metadata['License']}[/dim]")
    except importlib.metadata.PackageNotFoundError:
        version_info.append("[dim]Development installation[/dim]")

    panel = Panel(
        "\n".join(version_info), title="🤖 Claude Code Setup", border_style="cyan"
    )

    console.print(panel)
