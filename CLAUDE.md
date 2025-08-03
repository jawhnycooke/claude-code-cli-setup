# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Code Setup is a sophisticated Python CLI tool that manages command templates and configurations for Claude Code. It provides a streamlined approach to setting up, configuring, and organizing Claude Code commands in projects, similar to shadcn/ui's component installation methodology.

Key features:
- Command template management (add, list, update, remove)
- Settings and permissions management
- Security and automation hooks system
- Extensible plugin architecture
- Interactive setup wizards and direct CLI commands

## Commands

### Setup
```bash
# Install with uv (recommended)
uv venv && source .venv/bin/activate
uv pip install -e .
uv pip install -r requirements-dev.txt

# Traditional setup
python -m venv venv
source venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt
```

### Development
```bash
# Format code
make format
# or: uvx black src/ tests/ && uvx ruff format src/ tests/

# Lint
make lint
# or: uvx ruff check src/ tests/

# Type check
make typecheck
# or: uvx mypy src/ --strict

# Run tests
make test
# or: uvx pytest tests/ -v --cov=src --cov-report=html

# Full CI pipeline
make test-ci  # Runs typecheck + lint + test

# Docker integration tests (preferred for CLI validation)
make test-docker
```

### Building and Distribution
```bash
# Build package
make build
# or: python -m build

# Clean build artifacts
make clean
```

### Testing Specific Components
```bash
# Run a specific test file
pytest tests/test_cli.py -v

# Run tests with specific markers
pytest -m "not slow" -v  # Skip slow tests
pytest -m integration -v  # Only integration tests

# Test with coverage for specific module
pytest tests/commands/test_add.py --cov=src/claude_code_setup/commands/add
```

## Project Structure

The codebase follows a modular architecture with clear separation of concerns:

- `src/claude_code_setup/` - Main package
  - `commands/` - CLI command implementations (init, add, list, update, remove, settings, hooks, plugins)
  - `core/` - Core registry and loader systems
  - `hooks/` - Security and automation hooks (AWS guardrails, security validation, test enforcement)
  - `plugins/` - Plugin system with agents, bundles, workflows
  - `settings/` - Configuration and permission management
  - `templates/` - Command templates organized by category (python, node, project, general)
  - `ui/` - Rich terminal UI components
  - `utils/` - Utility functions and installers

## Architecture Notes

### Plugin System
The project implements a sophisticated plugin architecture that allows extending Claude Code with:
- **Agents**: AI agent plugins for specialized tasks
- **Bundles**: Pre-configured collections of plugins
- **Workflows**: Multi-step automation workflows
- **Hooks**: Event-driven automation and validation

### Command Templates
Templates are organized by category and stored as Markdown files with frontmatter metadata. Each template includes:
- Command definition
- Description
- Category (python/node/project/general)
- Optional bash script sections

### Configuration Management
Dual configuration support:
- Project-level: `.claude/settings.json`
- User-level: `~/.claude/settings.json`

Settings include permissions, environment variables, and theme preferences.

### Hook System
Three main hook categories:
1. **Security Hooks**: Validate commands before execution
2. **Testing Hooks**: Enforce test requirements
3. **AWS Hooks**: Deployment guardrails for AWS resources

## Key Implementation Details

- Uses Click for CLI command structure with Rich for enhanced UI
- Implements template management similar to shadcn/ui
- Supports dry run and test directory options for safe testing
- Type-safe with comprehensive Pydantic models
- Async support for concurrent operations
- Comprehensive error handling with user-friendly messages

## Testing Strategy

- Unit tests for individual components
- Integration tests for CLI commands
- Docker tests for package installation validation
- High code coverage target
- Marked tests for categorization (slow, integration, unit, cli, asyncio)

Always use Docker testing (`make test-docker`) for CLI validation to ensure tests match real-world package installation scenarios.

## Code Style Guidelines

- Black formatting with 88-character line length
- Ruff for comprehensive linting
- MyPy strict mode for type checking
- Google-style docstrings
- Type hints for all public functions
- Comprehensive error messages for user-facing operations