"""Tests for basic package functionality."""

import claude_code_setup
from claude_code_setup import cli, types


def test_package_version():
    """Test that package version is accessible."""
    assert claude_code_setup.__version__ == "0.12.0"


def test_package_metadata():
    """Test that package metadata is correct."""
    assert claude_code_setup.__author__
    assert claude_code_setup.__description__


def test_cli_import():
    """Test that CLI module can be imported."""
    assert hasattr(cli, "main")
    assert callable(cli.main)


def test_types_import():
    """Test that types module can be imported."""
    assert hasattr(types, "Template")
    assert hasattr(types, "Hook")
    assert hasattr(types, "ClaudeSettings")


def test_template_model():
    """Test that Template model works correctly."""
    template = types.Template(
        name="test", description="A test template", category="general", content="# Test"
    )
    assert template.name == "test"
    assert template.category == types.TemplateCategory.GENERAL


def test_hook_model():
    """Test that Hook model works correctly."""
    hook = types.Hook(
        name="test-hook",
        description="A test hook",
        category="testing",
        event=types.HookEvent.PRE_TOOL_USE,
        config=types.HookConfig(command="echo test"),
        scripts={"test.py": "print('test')"},
    )
    assert hook.name == "test-hook"
    assert hook.event == types.HookEvent.PRE_TOOL_USE


def test_settings_model():
    """Test that ClaudeSettings model works correctly."""
    settings = types.ClaudeSettings(
        theme="dark",
        permissions=types.PermissionsSettings(allow=["test"]),
        env={"TEST": "value"},
    )
    assert settings.theme == "dark"
    assert "test" in settings.permissions.allow
    assert settings.env["TEST"] == "value"
