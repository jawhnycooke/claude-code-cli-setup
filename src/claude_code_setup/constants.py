"""Constants used throughout the claude-code-setup application."""

from pathlib import Path

# Version information
APP_NAME = "claude-setup"
APP_DESCRIPTION = "CLI tool to set up and configure Claude Code command templates"

# Directory constants (matching TypeScript implementation)
CLAUDE_HOME = Path.home() / ".claude"
CLAUDE_COMMANDS_DIR = CLAUDE_HOME / "commands"
CLAUDE_HOOKS_DIR = CLAUDE_HOME / "hooks"
CLAUDE_SETTINGS_FILE = CLAUDE_HOME / "settings.json"

# Project URLs
REPO_URL = "https://github.com/jawhnycooke/claude-code-setup"
ISSUES_URL = f"{REPO_URL}/issues"
DOCS_URL = f"{REPO_URL}#readme"

# Template categories
TEMPLATE_CATEGORIES = ["general", "node", "python", "project"]

# Hook categories
HOOK_CATEGORIES = ["security", "testing", "aws"]

# Default ignore patterns (from TypeScript defaults.json)
DEFAULT_IGNORE_PATTERNS = [
    "node_modules",
    ".git",
    "*.log",
    "dist",
    "build",
    "__pycache__",
    "*.pyc",
]

# CLI Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_INTERRUPTED = 130

# Console styling
EMOJI_MAPPING = {
    "setup": "🤖",
    "init": "🚀",
    "list": "📋",
    "add": "📦",
    "update": "🔄",
    "remove": "🗑️",
    "hooks": "🛡️",
    "success": "✅",
    "warning": "⚠️",
    "error": "❌",
    "info": "💡",
    "search": "🔍",
    "target": "🎯",
}
