"""Plugin system for Claude Code Setup.

This module provides a modular plugin architecture that allows extending
Claude Code Setup with specialized expertise through templates, hooks,
agents, and workflows.
"""

from .types import (
    Plugin,
    PluginManifest,
    PluginCapabilities,
    PluginDependency,
    PluginBundle,
    PluginMetadata,
    PluginStatus,
)
from .registry import PluginRegistry
from .loader import PluginLoader

__all__ = [
    "Plugin",
    "PluginManifest",
    "PluginCapabilities",
    "PluginDependency",
    "PluginBundle",
    "PluginMetadata",
    "PluginStatus",
    "PluginRegistry",
    "PluginLoader",
]