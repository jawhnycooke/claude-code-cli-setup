"""Tests for hook installation and validation utilities."""

import json
import stat
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from claude_code_setup.utils.hook_installer import (
    HookInstaller,
    HookInstallationResult,
    HookInstallationReport,
    create_hook_installer,
    install_hook_simple,
)
from claude_code_setup.types import Hook, HookEvent, HookConfig


@pytest.fixture
def mock_hook():
    """Create a mock hook for testing."""
    return Hook(
        name="test-hook",
        description="A test hook for validation",
        category="testing",
        event=HookEvent.PRE_TOOL_USE,
        matcher="Bash",
        dependencies=["python3", "bash"],
        config=HookConfig(
            type="command",
            command="python3 .claude/hooks/test-hook/test_script.py"
        ),
        scripts={
            "test_script.py": "#!/usr/bin/env python3\nprint('Hello from test hook')\n",
            "test_script.sh": "#!/bin/bash\necho 'Hello from shell script'\n"
        }
    )


@pytest.fixture
def temp_claude_dir(tmp_path):
    """Create a temporary .claude directory structure."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    (claude_dir / "hooks").mkdir()
    return claude_dir


class TestHookInstaller:
    """Test hook installer functionality."""
    
    def test_init_default(self):
        """Test installer initialization with defaults."""
        installer = HookInstaller()
        
        assert installer.target_dir == Path.home() / ".claude"
        assert not installer.dry_run
        assert not installer.force
        assert installer.backup
        assert installer.validate_dependencies
        assert installer.hooks_dir == installer.target_dir / "hooks"
        
    def test_init_custom(self, temp_claude_dir):
        """Test installer initialization with custom settings."""
        installer = HookInstaller(
            target_dir=temp_claude_dir,
            dry_run=True,
            force=True,
            backup=False,
            validate_dependencies=False,
        )
        
        assert installer.target_dir == temp_claude_dir
        assert installer.dry_run
        assert installer.force
        assert not installer.backup
        assert not installer.validate_dependencies
        
    def test_install_hook_success(self, temp_claude_dir, mock_hook):
        """Test successful hook installation."""
        installer = HookInstaller(target_dir=temp_claude_dir)
        
        with patch('claude_code_setup.utils.hook_installer.get_hook_sync') as mock_get:
            mock_get.return_value = mock_hook
            
            result = installer.install_hook("test-hook")
            
            assert result.success
            assert result.hook_name == "test-hook"
            assert "successfully" in result.message.lower()
            assert result.installed_path == temp_claude_dir / "hooks" / "testing" / "test-hook"
            assert "test_script.py" in result.scripts_installed
            assert "test_script.sh" in result.scripts_installed
            
            # Check that files were created
            hook_dir = temp_claude_dir / "hooks" / "testing" / "test-hook"
            assert hook_dir.exists()
            assert (hook_dir / "test_script.py").exists()
            assert (hook_dir / "test_script.sh").exists()
            assert (hook_dir / "metadata.json").exists()
            
            # Check script content
            script_content = (hook_dir / "test_script.py").read_text()
            assert "Hello from test hook" in script_content
            
            # Check metadata
            metadata_content = json.loads((hook_dir / "metadata.json").read_text())
            assert metadata_content["name"] == "test-hook"
            assert metadata_content["category"] == "testing"
            
    def test_install_hook_dry_run(self, temp_claude_dir, mock_hook):
        """Test hook installation in dry run mode."""
        installer = HookInstaller(target_dir=temp_claude_dir, dry_run=True)
        
        with patch('claude_code_setup.utils.hook_installer.get_hook_sync') as mock_get:
            mock_get.return_value = mock_hook
            
            result = installer.install_hook("test-hook")
            
            assert result.success
            assert "test_script.py" in result.scripts_installed
            
            # Check that no files were actually created
            hook_dir = temp_claude_dir / "hooks" / "testing" / "test-hook"
            assert not hook_dir.exists()
            
    def test_install_hook_not_found(self, temp_claude_dir):
        """Test installing a hook that doesn't exist."""
        installer = HookInstaller(target_dir=temp_claude_dir)
        
        with patch('claude_code_setup.utils.hook_installer.get_hook_sync') as mock_get:
            mock_get.return_value = None
            
            result = installer.install_hook("nonexistent-hook")
            
            assert not result.success
            assert "not found" in result.message.lower()
            
    def test_install_hook_already_exists(self, temp_claude_dir, mock_hook):
        """Test installing a hook that already exists."""
        installer = HookInstaller(target_dir=temp_claude_dir)
        
        # Create existing hook directory
        hook_dir = temp_claude_dir / "hooks" / "testing" / "test-hook"
        hook_dir.mkdir(parents=True)
        (hook_dir / "existing_file.txt").write_text("existing content")
        
        with patch('claude_code_setup.utils.hook_installer.get_hook_sync') as mock_get:
            mock_get.return_value = mock_hook
            
            result = installer.install_hook("test-hook")
            
            assert not result.success
            assert "already exists" in result.message.lower()
            
    def test_install_hook_force_overwrite(self, temp_claude_dir, mock_hook):
        """Test force overwriting existing hook."""
        installer = HookInstaller(target_dir=temp_claude_dir, force=True)
        
        # Create existing hook directory
        hook_dir = temp_claude_dir / "hooks" / "testing" / "test-hook"
        hook_dir.mkdir(parents=True)
        (hook_dir / "existing_file.txt").write_text("existing content")
        
        with patch('claude_code_setup.utils.hook_installer.get_hook_sync') as mock_get:
            mock_get.return_value = mock_hook
            
            result = installer.install_hook("test-hook")
            
            assert result.success
            # Old file should be gone, new files should exist
            assert not (hook_dir / "existing_file.txt").exists()
            assert (hook_dir / "test_script.py").exists()
            
    def test_install_hooks_batch(self, temp_claude_dir, mock_hook):
        """Test batch hook installation."""
        installer = HookInstaller(target_dir=temp_claude_dir)
        
        with patch('claude_code_setup.utils.hook_installer.get_hook_sync') as mock_get:
            mock_get.return_value = mock_hook
            
            report = installer.install_hooks(["hook1", "hook2", "hook3"])
            
            assert report.total_requested == 3
            assert report.successful_installs == 3
            assert report.failed_installs == 0
            assert len(report.results) == 3
            assert report.success_rate == 100.0
            assert report.duration >= 0
            
    def test_validate_hook_dependencies_success(self, temp_claude_dir, mock_hook):
        """Test successful dependency validation."""
        installer = HookInstaller(target_dir=temp_claude_dir)
        
        with patch.object(installer.dependency_validator, '_check_tool_available') as mock_check:
            mock_check.return_value = True
            
            is_valid, missing = installer._validate_hook_dependencies(mock_hook)
            
            assert is_valid
            assert len(missing) == 0
            
    def test_validate_hook_dependencies_missing(self, temp_claude_dir, mock_hook):
        """Test dependency validation with missing dependencies."""
        installer = HookInstaller(target_dir=temp_claude_dir)
        
        with patch.object(installer.dependency_validator, '_check_tool_available') as mock_check:
            # python3 available, bash missing
            mock_check.side_effect = lambda dep: dep == "python3"
            
            is_valid, missing = installer._validate_hook_dependencies(mock_hook)
            
            assert not is_valid
            assert "bash" in missing
            assert "python3" not in missing
            
    def test_make_executable(self, temp_claude_dir):
        """Test making script files executable."""
        installer = HookInstaller(target_dir=temp_claude_dir)
        
        # Create a test script
        script_path = temp_claude_dir / "test_script.py"
        script_path.write_text("#!/usr/bin/env python3\nprint('test')")
        
        # Initially should not be executable
        initial_mode = script_path.stat().st_mode
        
        # Make executable
        installer._make_executable(script_path)
        
        # Check that execute permissions were added
        new_mode = script_path.stat().st_mode
        assert new_mode & stat.S_IXUSR  # Owner execute
        assert new_mode & stat.S_IXGRP  # Group execute
        assert new_mode & stat.S_IXOTH  # Others execute
        
    def test_validate_python_script_valid(self, temp_claude_dir):
        """Test validation of valid Python script."""
        installer = HookInstaller(target_dir=temp_claude_dir)
        
        valid_script = "#!/usr/bin/env python3\nprint('Hello, world!')\n"
        errors = installer._validate_python_script(valid_script, "test.py")
        
        assert len(errors) == 0
        
    def test_validate_python_script_invalid(self, temp_claude_dir):
        """Test validation of invalid Python script."""
        installer = HookInstaller(target_dir=temp_claude_dir)
        
        invalid_script = "#!/usr/bin/env python3\nprint('Hello, world!'\n"  # Missing closing quote
        errors = installer._validate_python_script(invalid_script, "test.py")
        
        assert len(errors) > 0
        assert any("syntax error" in error.lower() for error in errors)
        
    def test_validate_python_script_no_shebang(self, temp_claude_dir):
        """Test validation of Python script without shebang."""
        installer = HookInstaller(target_dir=temp_claude_dir)
        
        no_shebang_script = "print('Hello, world!')\n"
        errors = installer._validate_python_script(no_shebang_script, "test.py")
        
        assert len(errors) > 0
        assert any("shebang" in error.lower() for error in errors)
        
    def test_validate_shell_script_valid(self, temp_claude_dir):
        """Test validation of valid shell script."""
        installer = HookInstaller(target_dir=temp_claude_dir)
        
        valid_script = "#!/bin/bash\necho 'Hello, world!'\n"
        errors = installer._validate_shell_script(valid_script, "test.sh")
        
        assert len(errors) == 0
        
    def test_validate_shell_script_unmatched_quotes(self, temp_claude_dir):
        """Test validation of shell script with unmatched quotes."""
        installer = HookInstaller(target_dir=temp_claude_dir)
        
        invalid_script = "#!/bin/bash\necho 'Hello, world!\n"  # Missing closing quote
        errors = installer._validate_shell_script(invalid_script, "test.sh")
        
        assert len(errors) > 0
        assert any("unmatched" in error.lower() for error in errors)
        
    def test_validate_shell_script_unmatched_braces(self, temp_claude_dir):
        """Test validation of shell script with unmatched braces."""
        installer = HookInstaller(target_dir=temp_claude_dir)
        
        invalid_script = "#!/bin/bash\nif [ -f file ]; then\n  echo 'found'\n"  # Missing fi
        errors = installer._validate_shell_script(invalid_script, "test.sh")
        
        assert len(errors) > 0
        assert any("unmatched" in error.lower() for error in errors)
        
    def test_uninstall_hook_success(self, temp_claude_dir, mock_hook):
        """Test successful hook uninstallation."""
        installer = HookInstaller(target_dir=temp_claude_dir)
        
        # First install a hook
        with patch('claude_code_setup.utils.hook_installer.get_hook_sync') as mock_get:
            mock_get.return_value = mock_hook
            installer.install_hook("test-hook")
        
        # Verify it was installed
        hook_dir = temp_claude_dir / "hooks" / "testing" / "test-hook"
        assert hook_dir.exists()
        
        # Now uninstall it
        result = installer.uninstall_hook("test-hook")
        
        assert result.success
        assert "successfully" in result.message.lower()
        assert not hook_dir.exists()
        
    def test_uninstall_hook_not_found(self, temp_claude_dir):
        """Test uninstalling a hook that doesn't exist."""
        installer = HookInstaller(target_dir=temp_claude_dir)
        
        result = installer.uninstall_hook("nonexistent-hook")
        
        assert not result.success
        assert "not found" in result.message.lower()


class TestHookInstallerFactory:
    """Test hook installer factory functions."""
    
    def test_create_hook_installer(self, temp_claude_dir):
        """Test creating hook installer with factory function."""
        installer = create_hook_installer(
            target_dir=temp_claude_dir,
            dry_run=True,
            force=True,
            backup=False,
            validate_dependencies=False,
        )
        
        assert isinstance(installer, HookInstaller)
        assert installer.target_dir == temp_claude_dir
        assert installer.dry_run
        assert installer.force
        assert not installer.backup
        assert not installer.validate_dependencies
        
    def test_install_hook_simple_success(self, temp_claude_dir, mock_hook):
        """Test simple hook installation function."""
        with patch('claude_code_setup.utils.hook_installer.get_hook_sync') as mock_get:
            mock_get.return_value = mock_hook
            
            success = install_hook_simple("test-hook", target_dir=temp_claude_dir)
            
            assert success
            
            # Check that hook was installed
            hook_dir = temp_claude_dir / "hooks" / "testing" / "test-hook"
            assert hook_dir.exists()
            
    def test_install_hook_simple_failure(self, temp_claude_dir):
        """Test simple hook installation function with failure."""
        with patch('claude_code_setup.utils.hook_installer.get_hook_sync') as mock_get:
            mock_get.return_value = None  # Hook not found
            
            success = install_hook_simple("nonexistent-hook", target_dir=temp_claude_dir)
            
            assert not success


class TestHookInstallationReport:
    """Test hook installation reporting."""
    
    def test_installation_report_properties(self):
        """Test installation report properties."""
        report = HookInstallationReport(total_requested=10)
        report.successful_installs = 8
        report.failed_installs = 2
        
        assert report.success_rate == 80.0
        
        # Test with zero requests
        empty_report = HookInstallationReport(total_requested=0)
        assert empty_report.success_rate == 100.0
        
    def test_installation_report_duration(self):
        """Test installation report duration calculation."""
        import time
        from datetime import datetime
        
        report = HookInstallationReport(total_requested=1)
        start_time = report.start_time
        
        # Simulate some time passing
        time.sleep(0.1)
        report.end_time = datetime.now()
        
        assert report.duration > 0
        assert report.duration < 1.0  # Should be less than 1 second


class TestErrorHandling:
    """Test error handling in hook installation."""
    
    def test_install_hook_exception(self, temp_claude_dir):
        """Test handling of exceptions during installation."""
        installer = HookInstaller(target_dir=temp_claude_dir)
        
        with patch('claude_code_setup.utils.hook_installer.get_hook_sync') as mock_get:
            mock_get.side_effect = Exception("Simulated error")
            
            result = installer.install_hook("test-hook")
            
            assert not result.success
            assert "failed" in result.message.lower()
            assert result.error is not None
            
    def test_uninstall_hook_exception(self, temp_claude_dir):
        """Test handling of exceptions during uninstallation."""
        installer = HookInstaller(target_dir=temp_claude_dir)
        
        # Create a hook directory that will cause issues
        hook_dir = temp_claude_dir / "hooks" / "testing" / "test-hook"
        hook_dir.mkdir(parents=True)
        
        with patch('shutil.rmtree') as mock_rmtree:
            mock_rmtree.side_effect = Exception("Simulated removal error")
            
            result = installer.uninstall_hook("test-hook")
            
            assert not result.success
            assert "failed" in result.message.lower()
            assert result.error is not None