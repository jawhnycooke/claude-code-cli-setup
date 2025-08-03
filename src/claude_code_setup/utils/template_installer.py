"""Template installation utilities for claude-code-setup.

This module provides comprehensive template installation functionality with
progress tracking, validation, error handling, and rollback capabilities.
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

from ..types import Template, TemplateCategory
from ..utils.logger import debug, info, warning, error as log_error
from ..ui.progress import MultiStepProgress, ProgressStep, StepStatus
from ..ui.styles import console, create_validation_error, create_success_banner
from .template import get_template_sync, get_all_templates_sync
from .template_validator import TemplateValidator, format_validation_report


@dataclass
class InstallationResult:
    """Result of a template installation operation."""
    template_name: str
    success: bool
    message: str
    installed_path: Optional[Path] = None
    error: Optional[Exception] = None
    rollback_performed: bool = False


@dataclass 
class InstallationReport:
    """Report of a batch template installation."""
    total_requested: int
    successful_installs: int = 0
    failed_installs: int = 0
    skipped_installs: int = 0
    results: List[InstallationResult] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    @property
    def duration(self) -> float:
        """Get installation duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.total_requested == 0:
            return 0.0
        return (self.successful_installs / self.total_requested) * 100


class TemplateInstaller:
    """Handles template installation with validation and progress tracking."""
    
    def __init__(
        self,
        target_dir: Optional[Path] = None,
        dry_run: bool = False,
        force: bool = False,
        backup: bool = True
    ):
        """Initialize template installer.
        
        Args:
            target_dir: Target directory for installation (defaults to ~/.claude)
            dry_run: If True, simulate installation without writing files
            force: If True, overwrite existing templates
            backup: If True, backup existing templates before overwriting
        """
        self.target_dir = Path(target_dir) if target_dir else Path.home() / ".claude"
        self.commands_dir = self.target_dir / "commands"
        self.dry_run = dry_run
        self.force = force
        self.backup = backup
        self._installed_templates: List[Path] = []
        
    def _ensure_category_dir(self, category: TemplateCategory) -> Path:
        """Ensure category directory exists.
        
        Args:
            category: Template category
            
        Returns:
            Path to category directory
        """
        category_dir = self.commands_dir / category.value
        if not self.dry_run:
            category_dir.mkdir(parents=True, exist_ok=True)
        return category_dir
    
    def _get_template_path(self, template: Template) -> Path:
        """Get the installation path for a template.
        
        Args:
            template: Template to install
            
        Returns:
            Path where template will be installed
        """
        category_dir = self._ensure_category_dir(template.category)
        # Remove any category prefix from name for file path
        clean_name = template.name.replace(f"{template.category.value}-", "")
        return category_dir / f"{clean_name}.md"
    
    def _backup_existing_template(self, template_path: Path) -> Optional[Path]:
        """Backup an existing template file.
        
        Args:
            template_path: Path to existing template
            
        Returns:
            Path to backup file if created, None otherwise
        """
        if not template_path.exists() or self.dry_run:
            return None
            
        backup_path = template_path.with_suffix(f".md.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        template_path.rename(backup_path)
        debug(f"Backed up existing template to {backup_path}")
        return backup_path
    
    def _validate_template_for_install(self, template: Template) -> Tuple[bool, Optional[str]]:
        """Validate a template before installation.
        
        Args:
            template: Template to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Use enhanced validator
        validator = TemplateValidator()
        is_valid, issues = validator.validate(template)
        
        if not is_valid:
            # Get first error for simple message
            error_issues = [i for i in issues if i.severity.value == 'error']
            if error_issues:
                return False, error_issues[0].message
            return False, "Template validation failed"
        
        # Check for warnings
        warning_issues = [i for i in issues if i.severity.value == 'warning']
        if warning_issues:
            for issue in warning_issues[:3]:  # Show first 3 warnings
                warning(f"Template warning: {issue.message}")
        
        return True, None
    
    def install_template(
        self,
        template_name: str,
        progress_callback: Optional[callable] = None
    ) -> InstallationResult:
        """Install a single template.
        
        Args:
            template_name: Name of template to install
            progress_callback: Optional callback for progress updates
            
        Returns:
            InstallationResult with details of the operation
        """
        try:
            # Get template from registry
            template = get_template_sync(template_name)
            if not template:
                return InstallationResult(
                    template_name=template_name,
                    success=False,
                    message=f"Template '{template_name}' not found in registry"
                )
            
            # Validate template
            is_valid, error_msg = self._validate_template_for_install(template)
            if not is_valid:
                return InstallationResult(
                    template_name=template_name,
                    success=False,
                    message=error_msg
                )
            
            # Get installation path
            template_path = self._get_template_path(template)
            
            # Check if already exists
            if template_path.exists() and not self.force:
                return InstallationResult(
                    template_name=template_name,
                    success=False,
                    message=f"Template already exists at {template_path}. Use --force to overwrite",
                    installed_path=template_path
                )
            
            # Backup existing if needed
            backup_path = None
            if template_path.exists() and self.backup:
                backup_path = self._backup_existing_template(template_path)
            
            # Install template
            if not self.dry_run:
                template_path.parent.mkdir(parents=True, exist_ok=True)
                template_path.write_text(template.content, encoding='utf-8')
                self._installed_templates.append(template_path)
            
            # Report progress
            if progress_callback:
                progress_callback(template_name, True)
            
            return InstallationResult(
                template_name=template_name,
                success=True,
                message=f"Successfully installed to {template_path}",
                installed_path=template_path
            )
            
        except Exception as e:
            log_error(f"Failed to install template {template_name}: {e}")
            return InstallationResult(
                template_name=template_name,
                success=False,
                message=f"Installation failed: {str(e)}",
                error=e
            )
    
    def install_templates(
        self,
        template_names: List[str],
        progress: Optional[MultiStepProgress] = None
    ) -> InstallationReport:
        """Install multiple templates with progress tracking.
        
        Args:
            template_names: List of template names to install
            progress: Optional MultiStepProgress for tracking
            
        Returns:
            InstallationReport with detailed results
        """
        report = InstallationReport(
            total_requested=len(template_names),
            successful_installs=0,
            failed_installs=0,
            skipped_installs=0
        )
        
        # Create progress steps if progress tracker provided
        if progress and not self.dry_run:
            for i, name in enumerate(template_names):
                progress.update_step_progress(
                    "install_templates",
                    (i / len(template_names)) * 100,
                    f"Installing {name}..."
                )
        
        # Install each template
        for i, template_name in enumerate(template_names):
            result = self.install_template(template_name)
            report.results.append(result)
            
            if result.success:
                report.successful_installs += 1
            elif "already exists" in result.message:
                report.skipped_installs += 1
            else:
                report.failed_installs += 1
            
            # Update progress
            if progress:
                progress.update_step_progress(
                    "install_templates",
                    ((i + 1) / len(template_names)) * 100,
                    f"Installed {i + 1}/{len(template_names)} templates"
                )
        
        report.end_time = datetime.now()
        return report
    
    def rollback(self) -> int:
        """Rollback all installed templates in this session.
        
        Returns:
            Number of templates rolled back
        """
        rollback_count = 0
        
        for template_path in reversed(self._installed_templates):
            try:
                if template_path.exists():
                    template_path.unlink()
                    rollback_count += 1
                    debug(f"Rolled back template: {template_path}")
            except Exception as e:
                log_error(f"Failed to rollback {template_path}: {e}")
        
        self._installed_templates.clear()
        return rollback_count
    
    def verify_installation(self, template_name: str) -> Tuple[bool, Optional[str]]:
        """Verify that a template was installed correctly.
        
        Args:
            template_name: Name of template to verify
            
        Returns:
            Tuple of (is_installed, error_message)
        """
        try:
            template = get_template_sync(template_name)
            if not template:
                return False, "Template not found in registry"
            
            template_path = self._get_template_path(template)
            
            if not template_path.exists():
                return False, f"Template file not found at {template_path}"
            
            # Verify content matches
            installed_content = template_path.read_text(encoding='utf-8')
            if installed_content != template.content:
                return False, "Installed content doesn't match template"
            
            return True, None
            
        except Exception as e:
            return False, f"Verification failed: {str(e)}"


def install_templates_interactive(
    template_names: List[str],
    target_dir: Optional[Path] = None,
    dry_run: bool = False,
    force: bool = False
) -> InstallationReport:
    """Install templates with interactive progress display.
    
    Args:
        template_names: List of template names to install
        target_dir: Target directory (defaults to ~/.claude)
        dry_run: If True, simulate installation
        force: If True, overwrite existing templates
        
    Returns:
        InstallationReport with results
    """
    # Create progress tracker
    steps = [
        ProgressStep(
            "validate",
            "Validate Templates",
            "Checking template availability and validity"
        ),
        ProgressStep(
            "install_templates",
            "Install Templates", 
            f"Installing {len(template_names)} templates"
        ),
        ProgressStep(
            "verify",
            "Verify Installation",
            "Verifying installed templates"
        )
    ]
    
    progress = MultiStepProgress(
        title="Template Installation",
        steps=steps,
        console_obj=console
    )
    
    installer = TemplateInstaller(
        target_dir=target_dir,
        dry_run=dry_run,
        force=force
    )
    
    try:
        with progress.live_display() as (live, update):
            # Validation step
            progress.start_step("validate")
            update()
            
            invalid_templates = []
            for name in template_names:
                template = get_template_sync(name)
                if not template:
                    invalid_templates.append(name)
            
            if invalid_templates:
                progress.complete_step(
                    "validate",
                    success=False,
                    error_message=f"Templates not found: {', '.join(invalid_templates)}"
                )
                update()
                return InstallationReport(
                    total_requested=len(template_names),
                    successful_installs=0,
                    failed_installs=len(template_names),
                    skipped_installs=0
                )
            
            progress.complete_step("validate")
            update()
            
            # Installation step
            progress.start_step("install_templates")
            update()
            
            report = installer.install_templates(template_names, progress)
            
            if report.failed_installs > 0:
                progress.complete_step(
                    "install_templates",
                    success=False,
                    error_message=f"{report.failed_installs} templates failed to install"
                )
            else:
                progress.complete_step("install_templates")
            update()
            
            # Verification step
            if not dry_run and report.successful_installs > 0:
                progress.start_step("verify")
                update()
                
                verification_failures = 0
                for result in report.results:
                    if result.success:
                        is_verified, error = installer.verify_installation(result.template_name)
                        if not is_verified:
                            verification_failures += 1
                            warning(f"Verification failed for {result.template_name}: {error}")
                
                if verification_failures > 0:
                    progress.complete_step(
                        "verify",
                        success=False,
                        error_message=f"{verification_failures} templates failed verification"
                    )
                else:
                    progress.complete_step("verify")
                update()
            else:
                progress.skip_step("verify", "No templates to verify")
                update()
        
        # Show installation report
        if report.successful_installs > 0 or report.skipped_installs > 0:
            console.print(progress.create_installation_report("templates"))
        
        return report
        
    except Exception as e:
        log_error(f"Template installation failed: {e}")
        if installer._installed_templates:
            rollback_count = installer.rollback()
            warning(f"Rolled back {rollback_count} templates due to error")
        raise


def get_installed_templates(target_dir: Optional[Path] = None) -> Dict[str, List[str]]:
    """Get list of installed templates organized by category.
    
    Args:
        target_dir: Target directory (defaults to ~/.claude)
        
    Returns:
        Dictionary mapping category names to list of template names
    """
    target = Path(target_dir) if target_dir else Path.home() / ".claude"
    commands_dir = target / "commands"
    
    installed = {}
    
    if not commands_dir.exists():
        return installed
    
    # Check each category directory
    for category_dir in commands_dir.iterdir():
        if not category_dir.is_dir():
            continue
        
        category = category_dir.name
        templates = []
        
        # Find all .md files in category
        for template_file in category_dir.glob("*.md"):
            template_name = template_file.stem
            # Add category prefix for optimization templates
            if template_name == "optimization":
                template_name = f"{category}-{template_name}"
            templates.append(template_name)
        
        if templates:
            installed[category] = sorted(templates)
    
    return installed


def check_template_installed(
    template_name: str,
    target_dir: Optional[Path] = None
) -> bool:
    """Check if a specific template is installed.
    
    Args:
        template_name: Name of template to check
        target_dir: Target directory (defaults to ~/.claude)
        
    Returns:
        True if template is installed
    """
    installed = get_installed_templates(target_dir)
    
    for category, templates in installed.items():
        if template_name in templates:
            return True
    
    return False