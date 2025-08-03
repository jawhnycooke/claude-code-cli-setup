"""Tests for settings utilities."""

import json
import tempfile
from pathlib import Path

import pytest

from claude_code_setup.types import ClaudeSettings, PermissionsSettings
from claude_code_setup.utils.settings import (
    get_available_permission_sets,
    get_available_permission_sets_sync,
    get_available_themes,
    get_available_themes_sync,
    get_settings,
    get_settings_directory,
    get_settings_sync,
    load_all_permissions,
    load_all_permissions_sync,
    load_default_settings,
    load_default_settings_sync,
    load_theme,
    load_theme_sync,
    merge_settings,
    merge_settings_sync,
    read_settings,
    read_settings_sync,
    save_settings,
    save_settings_sync,
)


class TestSettingsDirectory:
    """Test settings directory functionality."""

    def test_get_settings_directory(self):
        """Test getting settings directory path."""
        settings_dir = get_settings_directory()
        assert settings_dir is not None
        assert "settings" in str(settings_dir)


class TestPermissionLoading:
    """Test permission loading functionality."""

    @pytest.mark.asyncio
    async def test_load_all_permissions(self):
        """Test loading all permissions from package resources."""
        permissions = await load_all_permissions()
        
        assert isinstance(permissions, list)
        assert len(permissions) > 0
        
        # All permissions should have Bash() prefix
        for perm in permissions:
            assert perm.startswith("Bash(")
            assert perm.endswith(")")

    def test_load_all_permissions_sync(self):
        """Test synchronous permission loading."""
        permissions = load_all_permissions_sync()
        
        assert isinstance(permissions, list)
        assert len(permissions) > 0
        
        # All permissions should have Bash() prefix
        for perm in permissions:
            assert perm.startswith("Bash(")
            assert perm.endswith(")")

    @pytest.mark.asyncio
    async def test_get_available_permission_sets(self):
        """Test getting available permission set names."""
        permission_sets = await get_available_permission_sets()
        
        assert isinstance(permission_sets, list)
        assert len(permission_sets) > 0
        
        # Should be sorted
        assert permission_sets == sorted(permission_sets)
        
        # Check for expected permission sets
        expected_sets = ['git', 'node', 'package-managers', 'python', 'shell']
        for expected_set in expected_sets:
            assert expected_set in permission_sets

    def test_get_available_permission_sets_sync(self):
        """Test synchronous available permission sets."""
        permission_sets = get_available_permission_sets_sync()
        
        assert isinstance(permission_sets, list)
        assert len(permission_sets) > 0
        assert permission_sets == sorted(permission_sets)


class TestThemeLoading:
    """Test theme loading functionality."""

    @pytest.mark.asyncio
    async def test_load_theme_default(self):
        """Test loading default theme."""
        theme = await load_theme("default")
        
        assert theme is not None
        assert isinstance(theme, dict)
        assert "theme" in theme

    @pytest.mark.asyncio
    async def test_load_theme_nonexistent(self):
        """Test loading non-existent theme."""
        theme = await load_theme("nonexistent")
        assert theme is None

    def test_load_theme_sync_default(self):
        """Test synchronous theme loading."""
        theme = load_theme_sync("default")
        
        assert theme is not None
        assert isinstance(theme, dict)
        assert "theme" in theme

    @pytest.mark.asyncio
    async def test_get_available_themes(self):
        """Test getting available theme names."""
        themes = await get_available_themes()
        
        assert isinstance(themes, list)
        assert len(themes) > 0
        
        # Should be sorted
        assert themes == sorted(themes)
        
        # Should include default theme
        assert "default" in themes

    def test_get_available_themes_sync(self):
        """Test synchronous available themes."""
        themes = get_available_themes_sync()
        
        assert isinstance(themes, list)
        assert len(themes) > 0
        assert themes == sorted(themes)
        assert "default" in themes


class TestDefaultSettings:
    """Test default settings loading."""

    @pytest.mark.asyncio
    async def test_load_default_settings(self):
        """Test loading default settings."""
        defaults = await load_default_settings()
        
        assert isinstance(defaults, dict)
        # Should have some default values

    def test_load_default_settings_sync(self):
        """Test synchronous default settings loading."""
        defaults = load_default_settings_sync()
        
        assert isinstance(defaults, dict)


class TestSettingsGeneration:
    """Test settings generation functionality."""

    @pytest.mark.asyncio
    async def test_get_settings_default(self):
        """Test getting settings with default parameters."""
        settings = await get_settings()
        
        assert isinstance(settings, ClaudeSettings)
        assert hasattr(settings, 'permissions')
        assert hasattr(settings, 'theme')
        assert isinstance(settings.permissions, PermissionsSettings)
        assert len(settings.permissions.allow) > 0

    @pytest.mark.asyncio
    async def test_get_settings_custom_permission_sets(self):
        """Test getting settings with custom permission sets."""
        settings = await get_settings(permission_sets=['python', 'git'])
        
        assert isinstance(settings, ClaudeSettings)
        assert len(settings.permissions.allow) > 0
        
        # Should contain python and git permissions
        python_perms = [p for p in settings.permissions.allow if 'python' in p.lower()]
        git_perms = [p for p in settings.permissions.allow if 'git' in p.lower()]
        
        assert len(python_perms) > 0
        assert len(git_perms) > 0

    @pytest.mark.asyncio
    async def test_get_settings_custom_theme(self):
        """Test getting settings with custom theme."""
        settings = await get_settings(theme='default')
        
        assert isinstance(settings, ClaudeSettings)
        assert settings.theme is not None

    def test_get_settings_sync_default(self):
        """Test synchronous settings generation."""
        settings = get_settings_sync()
        
        assert isinstance(settings, ClaudeSettings)
        assert hasattr(settings, 'permissions')
        assert hasattr(settings, 'theme')


class TestSettingsFileOperations:
    """Test settings file read/write operations."""

    @pytest.mark.asyncio
    async def test_read_settings_nonexistent(self):
        """Test reading non-existent settings file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "nonexistent.json"
            settings = await read_settings(settings_path)
            assert settings is None

    @pytest.mark.asyncio
    async def test_save_and_read_settings(self):
        """Test saving and reading settings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "test_settings.json"
            
            # Create test settings
            original_settings = await get_settings(permission_sets=['python'])
            
            # Save settings
            await save_settings(original_settings, settings_path)
            
            # Verify file exists
            assert settings_path.exists()
            
            # Read settings back
            loaded_settings = await read_settings(settings_path)
            
            assert loaded_settings is not None
            assert isinstance(loaded_settings, ClaudeSettings)
            assert loaded_settings.theme == original_settings.theme
            assert len(loaded_settings.permissions.allow) == len(original_settings.permissions.allow)

    def test_save_and_read_settings_sync(self):
        """Test synchronous settings save/read."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "test_settings_sync.json"
            
            # Create test settings
            original_settings = get_settings_sync(permission_sets=['git'])
            
            # Save settings
            save_settings_sync(original_settings, settings_path)
            
            # Verify file exists
            assert settings_path.exists()
            
            # Read settings back
            loaded_settings = read_settings_sync(settings_path)
            
            assert loaded_settings is not None
            assert isinstance(loaded_settings, ClaudeSettings)

    @pytest.mark.asyncio
    async def test_save_settings_creates_directory(self):
        """Test that save_settings creates parent directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "subdir" / "settings.json"
            
            # Create test settings
            settings = await get_settings()
            
            # Save settings (should create directory)
            await save_settings(settings, settings_path)
            
            # Verify file and directory exist
            assert settings_path.exists()
            assert settings_path.parent.exists()


class TestSettingsMerging:
    """Test settings merging functionality."""

    @pytest.mark.asyncio
    async def test_merge_settings_permissions(self):
        """Test merging settings with different permissions."""
        # Create two settings objects with different permissions
        settings1 = await get_settings(permission_sets=['python'])
        settings2 = await get_settings(permission_sets=['git'])
        
        # Merge settings
        merged = await merge_settings(settings1, settings2)
        
        assert isinstance(merged, ClaudeSettings)
        
        # Should have permissions from both
        python_perms = [p for p in merged.permissions.allow if 'python' in p.lower()]
        git_perms = [p for p in merged.permissions.allow if 'git' in p.lower()]
        
        assert len(python_perms) > 0
        assert len(git_perms) > 0
        
        # Should not have duplicates
        assert len(merged.permissions.allow) == len(set(merged.permissions.allow))

    @pytest.mark.asyncio
    async def test_merge_settings_env_vars(self):
        """Test merging settings with environment variables."""
        # Create base settings
        settings1 = await get_settings()
        settings1.env = {"VAR1": "value1", "SHARED": "old_value"}
        
        settings2 = await get_settings()
        settings2.env = {"VAR2": "value2", "SHARED": "new_value"}
        
        # Merge settings
        merged = await merge_settings(settings1, settings2)
        
        assert merged.env is not None
        assert merged.env["VAR1"] == "value1"
        assert merged.env["VAR2"] == "value2"
        assert merged.env["SHARED"] == "new_value"  # New value should override

    def test_merge_settings_sync(self):
        """Test synchronous settings merging."""
        # Create two settings objects with different permission sets
        settings1 = get_settings_sync(permission_sets=['python'])
        settings2 = get_settings_sync(permission_sets=['node'])
        
        # Merge settings
        merged = merge_settings_sync(settings1, settings2)
        
        assert isinstance(merged, ClaudeSettings)
        assert len(merged.permissions.allow) > 0

    @pytest.mark.asyncio
    async def test_merge_settings_ignore_patterns(self):
        """Test merging ignore patterns."""
        settings1 = await get_settings()
        settings1.ignorePatterns = ["*.log", "temp/*"]
        
        settings2 = await get_settings()
        settings2.ignorePatterns = ["*.tmp", "*.log"]  # Duplicate *.log
        
        merged = await merge_settings(settings1, settings2)
        
        assert merged.ignorePatterns is not None
        assert "*.log" in merged.ignorePatterns
        assert "*.tmp" in merged.ignorePatterns
        assert "temp/*" in merged.ignorePatterns
        
        # Should not have duplicates
        assert len(merged.ignorePatterns) == len(set(merged.ignorePatterns))


class TestSettingsValidation:
    """Test settings validation."""

    @pytest.mark.asyncio
    async def test_settings_validation_via_pydantic(self):
        """Test that settings are properly validated by Pydantic."""
        settings = await get_settings()
        
        # Should be valid Pydantic model
        assert isinstance(settings, ClaudeSettings)
        
        # Should be able to convert to dict and back
        settings_dict = settings.model_dump()
        recreated_settings = ClaudeSettings(**settings_dict)
        
        assert recreated_settings.theme == settings.theme
        assert len(recreated_settings.permissions.allow) == len(settings.permissions.allow)

    def test_invalid_settings_file_handling(self):
        """Test handling of invalid settings files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "invalid.json"
            
            # Write invalid JSON
            settings_path.write_text("{ invalid json }")
            
            # Should return None for invalid file
            result = read_settings_sync(settings_path)
            assert result is None