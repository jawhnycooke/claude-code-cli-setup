"""Pytest configuration and fixtures for claude-code-setup tests."""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def test_claude_dir(temp_dir: Path) -> Path:
    """Create a test .claude directory structure."""
    claude_dir = temp_dir / ".claude"
    claude_dir.mkdir()

    # Create subdirectories
    (claude_dir / "commands").mkdir()
    (claude_dir / "hooks").mkdir()

    return claude_dir


@pytest.fixture
def mock_no_interactive() -> Generator[None, None, None]:
    """Mock environment to disable interactive prompts."""
    original_env = os.environ.get("NO_INTERACTIVE")
    os.environ["NO_INTERACTIVE"] = "1"
    try:
        yield
    finally:
        if original_env is None:
            os.environ.pop("NO_INTERACTIVE", None)
        else:
            os.environ["NO_INTERACTIVE"] = original_env


@pytest.fixture
def sample_template() -> dict:
    """Sample template data for testing."""
    return {
        "name": "test-template",
        "description": "A test template",
        "category": "general",
        "content": "# Test Template\n\nThis is a test template.",
    }


@pytest.fixture
def sample_hook() -> dict:
    """Sample hook data for testing."""
    return {
        "name": "test-hook",
        "description": "A test hook",
        "category": "testing",
        "event": "PreToolUse",
        "config": {"type": "command", "command": "echo 'test hook'"},
        "scripts": {"test_script.py": "print('hello from test hook')"},
    }
