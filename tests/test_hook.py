"""Tests for hook loading and management utilities."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from claude_code_setup.utils.hook import (
    get_all_hooks_sync,
    get_hook_sync,
    get_hooks_by_category,
    get_hooks_by_event,
    get_hook_categories,
    validate_hook_metadata,
    clear_hook_cache,
    set_cache_ttl,
    get_cache_info,
)
from claude_code_setup.types import Hook, HookRegistry, HookEvent
from claude_code_setup.exceptions import HookLoadError


class TestHookLoading:
    """Test hook loading functionality."""
    
    def test_get_all_hooks_sync(self):
        """Test getting all hooks synchronously."""
        registry = get_all_hooks_sync()
        
        assert isinstance(registry, HookRegistry)
        assert isinstance(registry.hooks, dict)
        
        # Should have at least the hooks we know exist
        hook_names = set(registry.hooks.keys())
        expected_hooks = {
            "command-validator",
            "deployment-guard", 
            "file-change-limiter",
            "sensitive-file-protector",
            "test-enforcement"
        }
        
        assert expected_hooks.issubset(hook_names)
        
    def test_get_hook_sync_existing(self):
        """Test getting a specific hook that exists."""
        hook = get_hook_sync("command-validator")
        
        assert hook is not None
        assert isinstance(hook, Hook)
        assert hook.name == "command-validator"
        assert hook.category == "security"
        assert hook.event == HookEvent.PRE_TOOL_USE
        assert "command_validator.py" in hook.scripts
        
    def test_get_hook_sync_nonexistent(self):
        """Test getting a hook that doesn't exist."""
        hook = get_hook_sync("nonexistent-hook")
        assert hook is None
        
    def test_get_hooks_by_category(self):
        """Test filtering hooks by category."""
        security_hooks = get_hooks_by_category("security")
        
        assert len(security_hooks) >= 3  # At least command-validator, file-change-limiter, sensitive-file-protector
        for hook in security_hooks:
            assert hook.category == "security"
            
        # Test case insensitive
        security_hooks_upper = get_hooks_by_category("SECURITY")
        assert len(security_hooks_upper) == len(security_hooks)
        
    def test_get_hooks_by_event(self):
        """Test filtering hooks by event type."""
        pre_tool_hooks = get_hooks_by_event(HookEvent.PRE_TOOL_USE)
        
        assert len(pre_tool_hooks) >= 2  # At least command-validator and deployment-guard
        for hook in pre_tool_hooks:
            assert hook.event == HookEvent.PRE_TOOL_USE
            
        # Test with string event
        post_tool_hooks = get_hooks_by_event("PostToolUse")
        assert len(post_tool_hooks) >= 1  # At least test-enforcement
        
    def test_get_hook_categories(self):
        """Test getting available hook categories."""
        categories = get_hook_categories()
        
        assert isinstance(categories, dict)
        assert "security" in categories
        assert "testing" in categories
        assert "aws" in categories
        
        # Check descriptions
        assert isinstance(categories["security"], str)
        assert len(categories["security"]) > 0


class TestHookValidation:
    """Test hook metadata validation."""
    
    def test_validate_hook_metadata_valid(self):
        """Test validating valid hook metadata."""
        metadata = {
            "name": "test-hook",
            "description": "A test hook",
            "category": "testing",
            "event": "PreToolUse",
            "matcher": "Bash",
            "dependencies": ["python3"],
            "config": {
                "type": "command",
                "command": "python3 test.py"
            }
        }
        
        is_valid, errors = validate_hook_metadata(metadata)
        assert is_valid
        assert len(errors) == 0
        
    def test_validate_hook_metadata_invalid(self):
        """Test validating invalid hook metadata."""
        metadata = {
            "name": "",  # Invalid: empty name
            "description": "A test hook",
            "category": "testing",
            "event": "InvalidEvent",  # Invalid: not a valid event
            "config": {}  # Invalid: missing required command
        }
        
        is_valid, errors = validate_hook_metadata(metadata)
        assert not is_valid
        assert len(errors) > 0
        
        # Check that errors mention the specific issues
        error_text = " ".join(errors)
        assert "name" in error_text or "event" in error_text


class TestHookCaching:
    """Test hook registry caching functionality."""
    
    def test_cache_functionality(self):
        """Test that caching works correctly."""
        # Clear cache first
        clear_hook_cache()
        
        # First call should load from package
        registry1 = get_all_hooks_sync()
        cache_info1 = get_cache_info()
        
        assert cache_info1["cached"]
        assert cache_info1["hook_count"] > 0
        
        # Second call should use cache
        registry2 = get_all_hooks_sync()
        cache_info2 = get_cache_info()
        
        # Should be the same object (cached)
        assert registry1 is registry2
        assert cache_info2["cache_age"] >= cache_info1["cache_age"]
        
    def test_force_reload(self):
        """Test force reloading hooks."""
        # Load hooks normally
        registry1 = get_all_hooks_sync()
        
        # Force reload
        registry2 = get_all_hooks_sync(force_reload=True)
        
        # Should be different objects
        assert registry1 is not registry2
        # But should have same content
        assert len(registry1.hooks) == len(registry2.hooks)
        
    def test_cache_ttl(self):
        """Test cache TTL functionality."""
        # Set very short TTL
        set_cache_ttl(0.1)  # 100ms
        
        clear_hook_cache()
        
        # Load hooks
        registry1 = get_all_hooks_sync()
        
        # Wait for TTL to expire
        import time
        time.sleep(0.2)
        
        # Should reload automatically
        registry2 = get_all_hooks_sync()
        
        # Reset TTL to default
        set_cache_ttl(300.0)
        
    def test_clear_cache(self):
        """Test clearing the cache."""
        # Load hooks
        get_all_hooks_sync()
        
        # Verify cache exists
        cache_info = get_cache_info()
        assert cache_info["cached"]
        
        # Clear cache
        clear_hook_cache()
        
        # Verify cache is cleared
        cache_info = get_cache_info()
        assert not cache_info["cached"]
        assert cache_info["hook_count"] == 0


class TestSpecificHooks:
    """Test specific hook implementations."""
    
    def test_command_validator_hook(self):
        """Test the command validator hook specifically."""
        hook = get_hook_sync("command-validator")
        
        assert hook is not None
        assert hook.name == "command-validator"
        assert hook.description.lower().find("validates") != -1
        assert hook.category == "security"
        assert hook.event == HookEvent.PRE_TOOL_USE
        assert hook.matcher == "Bash"
        assert "python3" in hook.dependencies
        assert hook.config.type == "command"
        assert "command_validator.py" in hook.config.command
        assert "command_validator.py" in hook.scripts
        
        # Check that the script content is loaded
        script_content = hook.scripts["command_validator.py"]
        assert len(script_content) > 0
        assert "def" in script_content  # Should be Python code
        
    def test_deployment_guard_hook(self):
        """Test the AWS deployment guard hook."""
        hook = get_hook_sync("deployment-guard")
        
        assert hook is not None
        assert hook.name == "deployment-guard"
        assert hook.category == "aws"
        assert hook.event == HookEvent.PRE_TOOL_USE
        assert "validate_aws_command.py" in hook.scripts
        
    def test_test_enforcement_hook(self):
        """Test the test enforcement hook."""
        hook = get_hook_sync("test-enforcement")
        
        assert hook is not None
        assert hook.name == "test-enforcement"
        assert hook.category == "testing"
        assert hook.event == HookEvent.POST_TOOL_USE
        assert hook.matcher == "Edit|MultiEdit|Write"
        assert "run_tests_on_change.sh" in hook.scripts
        
        # Check script content
        script_content = hook.scripts["run_tests_on_change.sh"]
        assert len(script_content) > 0
        assert "#!/" in script_content  # Should be shell script


class TestErrorHandling:
    """Test error handling in hook operations."""
    
    @patch('claude_code_setup.utils.hook.importlib.resources')
    def test_hook_load_error(self, mock_resources):
        """Test handling of hook loading errors."""
        # Mock resources to raise an exception
        mock_resources.files.side_effect = Exception("Package not found")
        
        clear_hook_cache()
        
        with pytest.raises(HookLoadError):
            get_all_hooks_sync()
            
    def test_empty_hook_registry(self):
        """Test behavior with empty hook registry."""
        with patch('claude_code_setup.utils.hook._discover_hooks_from_package') as mock_discover:
            mock_discover.return_value = {}
            
            clear_hook_cache()
            registry = get_all_hooks_sync()
            
            assert len(registry.hooks) == 0
            assert get_hooks_by_category("security") == []
            assert get_hooks_by_event(HookEvent.PRE_TOOL_USE) == []