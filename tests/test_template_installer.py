"""Tests for template installation functionality."""

import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime
from unittest.mock import MagicMock, patch

from claude_code_setup.utils.template_installer import (
    TemplateInstaller,
    InstallationResult,
    InstallationReport,
    install_templates_interactive,
    get_installed_templates,
    check_template_installed,
)
from claude_code_setup.types import Template, TemplateCategory


@pytest.fixture
def temp_target_dir():
    """Create a temporary target directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_template():
    """Create a mock template for testing."""
    return Template(
        name="test-template",
        description="Test template",
        category=TemplateCategory.GENERAL,
        content="""# Test Template

This is a test template for validation.

## Description
This template is used for testing the installation system.

## Usage
Use this template to verify the installation process works correctly.
"""
    )


@pytest.fixture
def mock_templates():
    """Create multiple mock templates."""
    return {
        "code-review": Template(
            name="code-review",
            description="Code review template", 
            category=TemplateCategory.GENERAL,
            content="""# Code Review

Review code for quality and best practices.

## Description
This template provides guidelines for reviewing code.

## Process
1. Check code style and formatting
2. Review logic and algorithms
3. Verify tests and documentation
"""
        ),
        "python-optimization": Template(
            name="python-optimization",
            description="Python optimization template",
            category=TemplateCategory.PYTHON,
            content="""# Python Optimization

Optimize Python code for better performance.

## Description  
This template helps identify and fix performance bottlenecks.

## Steps
1. Profile the code
2. Identify hotspots
3. Apply optimization techniques
"""
        ),
        "fix-issue": Template(
            name="fix-issue",
            description="Fix issue template",
            category=TemplateCategory.GENERAL,
            content="""# Fix Issue

Fix GitHub issues systematically.

## Description
This template guides you through fixing reported issues.

## Process
1. Reproduce the issue
2. Identify root cause
3. Implement and test fix
"""
        )
    }


class TestInstallationResult:
    """Test InstallationResult dataclass."""
    
    def test_successful_result(self):
        """Test creating a successful installation result."""
        result = InstallationResult(
            template_name="test",
            success=True,
            message="Success",
            installed_path=Path("/test/path")
        )
        
        assert result.template_name == "test"
        assert result.success is True
        assert result.message == "Success"
        assert result.installed_path == Path("/test/path")
        assert result.error is None
        assert result.rollback_performed is False
    
    def test_failed_result(self):
        """Test creating a failed installation result."""
        error = ValueError("Test error")
        result = InstallationResult(
            template_name="test",
            success=False,
            message="Failed",
            error=error
        )
        
        assert result.success is False
        assert result.error == error


class TestInstallationReport:
    """Test InstallationReport dataclass."""
    
    def test_report_properties(self):
        """Test report calculated properties."""
        report = InstallationReport(
            total_requested=5,
            successful_installs=3,
            failed_installs=1,
            skipped_installs=1
        )
        
        assert report.success_rate == 60.0
        
        # Test duration
        report.end_time = datetime.now()
        assert report.duration >= 0.0
    
    def test_empty_report(self):
        """Test report with no installations."""
        report = InstallationReport(total_requested=0)
        assert report.success_rate == 0.0


class TestTemplateInstaller:
    """Test TemplateInstaller class."""
    
    def test_installer_initialization(self, temp_target_dir):
        """Test installer initialization."""
        installer = TemplateInstaller(
            target_dir=temp_target_dir,
            dry_run=True,
            force=True,
            backup=False
        )
        
        assert installer.target_dir == temp_target_dir
        assert installer.commands_dir == temp_target_dir / "commands"
        assert installer.dry_run is True
        assert installer.force is True
        assert installer.backup is False
    
    def test_ensure_category_dir(self, temp_target_dir):
        """Test category directory creation."""
        installer = TemplateInstaller(target_dir=temp_target_dir)
        
        category_dir = installer._ensure_category_dir(TemplateCategory.PYTHON)
        
        assert category_dir == temp_target_dir / "commands" / "python"
        assert category_dir.exists()
    
    def test_get_template_path(self, temp_target_dir, mock_template):
        """Test getting template installation path."""
        installer = TemplateInstaller(target_dir=temp_target_dir)
        
        path = installer._get_template_path(mock_template)
        
        assert path == temp_target_dir / "commands" / "general" / "test-template.md"
    
    def test_get_template_path_optimization(self, temp_target_dir):
        """Test path for optimization templates."""
        template = Template(
            name="python-optimization",
            description="Optimize Python",
            category=TemplateCategory.PYTHON,
            content="# Optimization"
        )
        
        installer = TemplateInstaller(target_dir=temp_target_dir)
        path = installer._get_template_path(template)
        
        # Should remove category prefix from filename
        assert path.name == "optimization.md"
    
    def test_backup_existing_template(self, temp_target_dir):
        """Test backing up existing template."""
        installer = TemplateInstaller(target_dir=temp_target_dir)
        
        # Create existing template
        template_path = temp_target_dir / "test.md"
        template_path.write_text("Original content")
        
        # Backup
        backup_path = installer._backup_existing_template(template_path)
        
        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.read_text() == "Original content"
        assert not template_path.exists()  # Original moved
    
    def test_validate_template_for_install(self, mock_template):
        """Test template validation."""
        installer = TemplateInstaller()
        
        # Valid template
        is_valid, error = installer._validate_template_for_install(mock_template)
        assert is_valid is True
        assert error is None
        
        # Invalid template - no name
        bad_template = Template(
            name="",
            description="Test",
            category=TemplateCategory.GENERAL,
            content="# Test\n\nThis is a test template with sufficient content."
        )
        is_valid, error = installer._validate_template_for_install(bad_template)
        assert is_valid is False
        assert "Template must have a name" in error
    
    @patch('claude_code_setup.utils.template_installer.get_template_sync')
    def test_install_template_success(self, mock_get_template, temp_target_dir, mock_template):
        """Test successful template installation."""
        mock_get_template.return_value = mock_template
        
        installer = TemplateInstaller(target_dir=temp_target_dir)
        result = installer.install_template("test-template")
        
        assert result.success is True
        assert result.installed_path.exists()
        assert result.installed_path.read_text() == mock_template.content
    
    @patch('claude_code_setup.utils.template_installer.get_template_sync')
    def test_install_template_not_found(self, mock_get_template, temp_target_dir):
        """Test installing non-existent template."""
        mock_get_template.return_value = None
        
        installer = TemplateInstaller(target_dir=temp_target_dir)
        result = installer.install_template("missing-template")
        
        assert result.success is False
        assert "not found in registry" in result.message
    
    @patch('claude_code_setup.utils.template_installer.get_template_sync')
    def test_install_template_already_exists(self, mock_get_template, temp_target_dir, mock_template):
        """Test installing template that already exists."""
        mock_get_template.return_value = mock_template
        
        # Create existing template
        installer = TemplateInstaller(target_dir=temp_target_dir, force=False)
        template_path = installer._get_template_path(mock_template)
        template_path.parent.mkdir(parents=True, exist_ok=True)
        template_path.write_text("Existing content")
        
        result = installer.install_template("test-template")
        
        assert result.success is False
        assert "already exists" in result.message
        assert template_path.read_text() == "Existing content"  # Not overwritten
    
    @patch('claude_code_setup.utils.template_installer.get_template_sync')
    def test_install_template_force_overwrite(self, mock_get_template, temp_target_dir, mock_template):
        """Test force overwriting existing template."""
        mock_get_template.return_value = mock_template
        
        # Create existing template
        installer = TemplateInstaller(target_dir=temp_target_dir, force=True, backup=True)
        template_path = installer._get_template_path(mock_template)
        template_path.parent.mkdir(parents=True, exist_ok=True)
        template_path.write_text("Existing content")
        
        result = installer.install_template("test-template")
        
        assert result.success is True
        assert template_path.read_text() == mock_template.content  # Overwritten
        
        # Check backup was created
        backup_files = list(template_path.parent.glob("*.backup_*"))
        assert len(backup_files) == 1
        assert backup_files[0].read_text() == "Existing content"
    
    @patch('claude_code_setup.utils.template_installer.get_template_sync')
    def test_install_template_dry_run(self, mock_get_template, temp_target_dir, mock_template):
        """Test dry run installation."""
        mock_get_template.return_value = mock_template
        
        installer = TemplateInstaller(target_dir=temp_target_dir, dry_run=True)
        result = installer.install_template("test-template")
        
        assert result.success is True
        assert not result.installed_path.exists()  # Not actually created
    
    @patch('claude_code_setup.utils.template_installer.get_template_sync')
    def test_install_templates_batch(self, mock_get_template, temp_target_dir, mock_templates):
        """Test batch template installation."""
        def get_template_side_effect(name):
            return mock_templates.get(name)
        
        mock_get_template.side_effect = get_template_side_effect
        
        installer = TemplateInstaller(target_dir=temp_target_dir)
        template_names = ["code-review", "python-optimization", "missing-template"]
        
        report = installer.install_templates(template_names)
        
        assert report.total_requested == 3
        assert report.successful_installs == 2
        assert report.failed_installs == 1
        assert report.skipped_installs == 0
        assert len(report.results) == 3
    
    @patch('claude_code_setup.utils.template_installer.get_template_sync')
    def test_rollback(self, mock_get_template, temp_target_dir, mock_template):
        """Test rollback functionality."""
        mock_get_template.return_value = mock_template
        
        installer = TemplateInstaller(target_dir=temp_target_dir)
        
        # Install template
        result = installer.install_template("test-template")
        assert result.success is True
        assert result.installed_path.exists()
        
        # Rollback
        rollback_count = installer.rollback()
        assert rollback_count == 1
        assert not result.installed_path.exists()
    
    @patch('claude_code_setup.utils.template_installer.get_template_sync')
    def test_verify_installation(self, mock_get_template, temp_target_dir, mock_template):
        """Test installation verification."""
        mock_get_template.return_value = mock_template
        
        installer = TemplateInstaller(target_dir=temp_target_dir)
        
        # Install template
        result = installer.install_template("test-template")
        assert result.success is True
        
        # Verify
        is_verified, error = installer.verify_installation("test-template")
        assert is_verified is True
        assert error is None
        
        # Corrupt the file
        result.installed_path.write_text("Corrupted content")
        is_verified, error = installer.verify_installation("test-template")
        assert is_verified is False
        assert "doesn't match" in error


class TestInstallTemplatesInteractive:
    """Test interactive template installation."""
    
    @patch('claude_code_setup.utils.template_installer.get_template_sync')
    @patch('claude_code_setup.utils.template_installer.console')
    def test_interactive_install_success(self, mock_console, mock_get_template, temp_target_dir, mock_templates):
        """Test successful interactive installation."""
        def get_template_side_effect(name):
            return mock_templates.get(name)
        
        mock_get_template.side_effect = get_template_side_effect
        
        template_names = ["code-review", "fix-issue"]
        report = install_templates_interactive(
            template_names,
            target_dir=temp_target_dir,
            dry_run=False,
            force=False
        )
        
        assert report.successful_installs == 2
        assert report.failed_installs == 0
    
    @patch('claude_code_setup.utils.template_installer.get_template_sync')
    def test_interactive_install_with_invalid(self, mock_get_template, temp_target_dir):
        """Test interactive installation with invalid templates."""
        mock_get_template.return_value = None  # Template not found
        
        template_names = ["invalid-template"]
        report = install_templates_interactive(
            template_names,
            target_dir=temp_target_dir
        )
        
        assert report.total_requested == 1
        assert report.failed_installs == 1


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_get_installed_templates(self, temp_target_dir):
        """Test getting installed templates."""
        # Create some template files
        commands_dir = temp_target_dir / "commands"
        
        # General templates
        general_dir = commands_dir / "general"
        general_dir.mkdir(parents=True, exist_ok=True)
        (general_dir / "code-review.md").write_text("# Code Review")
        (general_dir / "fix-issue.md").write_text("# Fix Issue")
        
        # Python templates
        python_dir = commands_dir / "python"
        python_dir.mkdir(parents=True, exist_ok=True)
        (python_dir / "optimization.md").write_text("# Optimization")
        
        # Get installed
        installed = get_installed_templates(temp_target_dir)
        
        assert "general" in installed
        assert "code-review" in installed["general"]
        assert "fix-issue" in installed["general"]
        assert "python" in installed
        assert "python-optimization" in installed["python"]  # Should add prefix
    
    def test_check_template_installed(self, temp_target_dir):
        """Test checking if template is installed."""
        # Create template file
        commands_dir = temp_target_dir / "commands"
        general_dir = commands_dir / "general"
        general_dir.mkdir(parents=True, exist_ok=True)
        (general_dir / "code-review.md").write_text("# Code Review")
        
        assert check_template_installed("code-review", temp_target_dir) is True
        assert check_template_installed("missing-template", temp_target_dir) is False