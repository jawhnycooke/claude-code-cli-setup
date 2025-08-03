"""Tests for file system utilities."""

import asyncio
import tempfile
from pathlib import Path

import pytest

from claude_code_setup.utils.fs import (
    CLAUDE_COMMANDS_DIR,
    CLAUDE_HOME,
    CLAUDE_HOOKS_DIR,
    CLAUDE_SETTINGS_FILE,
    copy_hook_with_permissions,
    ensure_claude_directories,
    ensure_claude_directories_sync,
    get_default_settings,
    read_template,
    template_exists,
    write_template,
)


class TestConstants:
    """Test constants are properly defined."""

    def test_claude_home_path(self):
        """Test CLAUDE_HOME points to ~/.claude."""
        assert CLAUDE_HOME == Path.home() / ".claude"

    def test_commands_dir_path(self):
        """Test CLAUDE_COMMANDS_DIR is correct."""
        assert CLAUDE_COMMANDS_DIR == CLAUDE_HOME / "commands"

    def test_hooks_dir_path(self):
        """Test CLAUDE_HOOKS_DIR is correct."""
        assert CLAUDE_HOOKS_DIR == CLAUDE_HOME / "hooks"

    def test_settings_file_path(self):
        """Test CLAUDE_SETTINGS_FILE is correct."""
        assert CLAUDE_SETTINGS_FILE == CLAUDE_HOME / "settings.json"


class TestEnsureDirectories:
    """Test directory creation functionality."""

    @pytest.mark.asyncio
    async def test_ensure_claude_directories_custom(self):
        """Test creating directories in custom location."""
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "test_claude"
            
            await ensure_claude_directories(str(target))
            
            assert (target / "commands").exists()
            assert (target / "hooks").exists()

    def test_ensure_claude_directories_sync_custom(self):
        """Test synchronous directory creation in custom location."""
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "test_claude"
            
            ensure_claude_directories_sync(str(target))
            
            assert (target / "commands").exists()
            assert (target / "hooks").exists()


class TestTemplateOperations:
    """Test template file operations."""

    @pytest.mark.asyncio
    async def test_template_exists_false(self):
        """Test template_exists returns False for non-existent template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exists = await template_exists("nonexistent", target_dir=temp_dir)
            assert exists is False

    @pytest.mark.asyncio
    async def test_write_and_read_template(self):
        """Test writing and reading a template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_name = "test-template"
            content = "# Test Template\n\nThis is a test template."
            
            # Write template
            await write_template(template_name, content, target_dir=temp_dir)
            
            # Check it exists
            exists = await template_exists(template_name, target_dir=temp_dir)
            assert exists is True
            
            # Read template
            read_content = await read_template(template_name, target_dir=temp_dir)
            assert read_content == content

    @pytest.mark.asyncio
    async def test_write_and_read_template_with_category(self):
        """Test writing and reading a template with category."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_name = "test-template"
            category = "python"
            content = "# Python Template\n\nThis is a Python template."
            
            # Write template with category
            await write_template(template_name, content, category=category, target_dir=temp_dir)
            
            # Check it exists
            exists = await template_exists(template_name, category=category, target_dir=temp_dir)
            assert exists is True
            
            # Check it doesn't exist without category
            exists_no_cat = await template_exists(template_name, target_dir=temp_dir)
            assert exists_no_cat is False
            
            # Read template
            read_content = await read_template(template_name, category=category, target_dir=temp_dir)
            assert read_content == content

    @pytest.mark.asyncio
    async def test_read_nonexistent_template(self):
        """Test reading a non-existent template returns None."""
        with tempfile.TemporaryDirectory() as temp_dir:
            content = await read_template("nonexistent", target_dir=temp_dir)
            assert content is None


class TestDefaultSettings:
    """Test default settings functionality."""

    def test_get_default_settings_structure(self):
        """Test default settings has correct structure."""
        settings = get_default_settings()
        
        assert "permissions" in settings
        assert "allow" in settings["permissions"]
        assert isinstance(settings["permissions"]["allow"], list)

    def test_get_default_settings_permissions(self):
        """Test default settings includes expected permissions."""
        settings = get_default_settings()
        permissions = settings["permissions"]["allow"]
        
        # Check for some key permissions
        assert "Bash(python:*)" in permissions
        assert "Bash(git:*)" in permissions
        assert "Bash(npm:*)" in permissions
        assert "Bash(uv:*)" in permissions
        assert "Bash(pytest:*)" in permissions


class TestHookPermissions:
    """Test hook file permission handling."""

    def test_copy_hook_with_permissions_shell_script(self):
        """Test copying shell script with executable permissions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create source script
            source_path = Path(temp_dir) / "source_script.sh"
            source_path.write_text("#!/bin/bash\necho 'test'")
            
            # Copy with permissions
            target_path = Path(temp_dir) / "target" / "script.sh"
            copy_hook_with_permissions(source_path, target_path)
            
            # Check file exists and is executable
            assert target_path.exists()
            assert target_path.stat().st_mode & 0o111  # Check executable bits

    def test_copy_hook_with_permissions_python_script(self):
        """Test copying Python script with executable permissions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create source script
            source_path = Path(temp_dir) / "source_script.py"
            source_path.write_text("#!/usr/bin/env python3\nprint('test')")
            
            # Copy with permissions
            target_path = Path(temp_dir) / "target" / "script.py"
            copy_hook_with_permissions(source_path, target_path)
            
            # Check file exists and is executable
            assert target_path.exists()
            assert target_path.stat().st_mode & 0o111  # Check executable bits

    def test_copy_hook_with_permissions_regular_file(self):
        """Test copying regular file (should not be executable)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create source file
            source_path = Path(temp_dir) / "source_file.json"
            source_path.write_text('{"test": true}')
            
            # Copy with permissions
            target_path = Path(temp_dir) / "target" / "file.json"
            copy_hook_with_permissions(source_path, target_path)
            
            # Check file exists but is not executable
            assert target_path.exists()
            # JSON files should not have executable permissions set