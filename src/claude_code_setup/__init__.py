"""Claude Code Setup - CLI tool for managing Claude Code templates and configurations.

This package provides a comprehensive CLI tool for setting up and configuring
Claude Code command templates, settings, and security hooks.
"""

__version__ = "0.12.0"
__author__ = "Jawhny Cooke"
__email__ = "jawcooke@amazon.com"
__description__ = "CLI tool to set up and configure Claude Code command templates"

# Re-export main components for easier imports
from .cli import main

__all__ = ["main", "__version__"]
