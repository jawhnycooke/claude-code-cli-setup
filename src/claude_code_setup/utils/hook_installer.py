"""Hook installation utilities for claude-code-setup.

This module provides comprehensive hook installation functionality with
progress tracking, validation, error handling, and rollback capabilities.
"""

import os
import stat
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime

from ..types import Hook, HookEvent
from ..utils.logger import debug, info, warning, error as log_error
from ..ui.progress import MultiStepProgress, ProgressStep, StepStatus
from ..ui.styles import console, create_validation_error, create_success_banner
from .hook import get_hook_sync, get_all_hooks_sync
from .dependency_validator import create_dependency_validator
from .fs import ensure_claude_directories
from .settings import register_hook_in_settings, unregister_hook_from_settings, validate_hook_settings


@dataclass
class HookInstallationResult:
    """Result of a hook installation operation."""
    hook_name: str
    success: bool
    message: str
    installed_path: Optional[Path] = None
    scripts_installed: List[str] = field(default_factory=list)
    error: Optional[Exception] = None
    rollback_performed: bool = False


@dataclass 
class HookInstallationReport:
    """Report of a batch hook installation."""
    total_requested: int
    successful_installs: int = 0
    failed_installs: int = 0
    skipped_installs: int = 0
    results: List[HookInstallationResult] = field(default_factory=list)
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
            return 100.0
        return (self.successful_installs / self.total_requested) * 100.0


class HookInstaller:
    """Hook installer with comprehensive features."""
    
    def __init__(
        self,
        target_dir: Optional[Path] = None,
        dry_run: bool = False,
        force: bool = False,
        backup: bool = True,
        validate_dependencies: bool = True,
    ):
        """Initialize hook installer.
        
        Args:
            target_dir: Target directory for installation (defaults to .claude)
            dry_run: If True, simulate installation without making changes
            force: If True, overwrite existing hooks
            backup: If True, backup existing hooks before overwriting
            validate_dependencies: If True, validate hook dependencies
        """
        self.target_dir = target_dir or (Path.home() / ".claude")
        self.dry_run = dry_run
        self.force = force
        self.backup = backup
        self.validate_dependencies = validate_dependencies
        self.dependency_validator = create_dependency_validator() if validate_dependencies else None
        
        # Ensure hooks directory exists
        self.hooks_dir = self.target_dir / "hooks"
        
    def install_hook(self, hook_name: str) -> HookInstallationResult:
        """Install a single hook.
        
        Args:
            hook_name: Name of the hook to install
            
        Returns:
            HookInstallationResult with installation details
        """
        try:
            # Get hook from registry
            hook = get_hook_sync(hook_name)
            if not hook:
                return HookInstallationResult(
                    hook_name=hook_name,
                    success=False,
                    message=f"Hook '{hook_name}' not found in registry"
                )
            
            # Validate dependencies if enabled
            if self.validate_dependencies:
                validation_result = self._validate_hook_dependencies(hook)
                if not validation_result[0]:
                    return HookInstallationResult(
                        hook_name=hook_name,
                        success=False,
                        message=f"Dependency validation failed: {', '.join(validation_result[1])}"
                    )
            
            # Check if hook already exists
            hook_install_dir = self.hooks_dir / hook.category / hook_name
            if hook_install_dir.exists() and not self.force:
                return HookInstallationResult(
                    hook_name=hook_name,
                    success=False,
                    message=f"Hook '{hook_name}' already exists (use --force to overwrite)"
                )
            
            # Backup existing hook if requested
            backup_path = None
            if hook_install_dir.exists() and self.backup and not self.dry_run:
                backup_path = self._backup_existing_hook(hook_install_dir)
            
            # Remove existing directory if force is enabled
            if hook_install_dir.exists() and self.force and not self.dry_run:
                import shutil
                shutil.rmtree(hook_install_dir)
                debug(f"Removed existing hook directory: {hook_install_dir}")
            
            # Create installation directory
            if not self.dry_run:
                hook_install_dir.mkdir(parents=True, exist_ok=True)
                debug(f"Created hook directory: {hook_install_dir}")
            
            # Install hook scripts
            installed_scripts = []
            for script_name, script_content in hook.scripts.items():
                script_path = hook_install_dir / script_name
                
                if not self.dry_run:
                    # Write script content
                    script_path.write_text(script_content, encoding='utf-8')
                    
                    # Set executable permissions for script files
                    if script_name.endswith(('.py', '.sh', '.bash')):
                        self._make_executable(script_path)
                    
                    debug(f"Installed script: {script_path}")
                
                installed_scripts.append(script_name)
            
            # Create metadata file
            metadata_path = hook_install_dir / "metadata.json"
            if not self.dry_run:
                metadata_content = {
                    "name": hook.name,
                    "description": hook.description,
                    "category": hook.category,
                    "event": hook.event.value,
                    "matcher": hook.matcher,
                    "dependencies": hook.dependencies,
                    "config": hook.config.model_dump()
                }
                
                with metadata_path.open('w', encoding='utf-8') as f:
                    import json
                    json.dump(metadata_content, f, indent=2)
                
                debug(f"Created metadata file: {metadata_path}")
            
            # Register hook in settings if not dry run
            if not self.dry_run:
                # Validate hook for settings integration
                is_valid, validation_errors = validate_hook_settings(hook)
                if is_valid:
                    settings_registered = register_hook_in_settings(hook)
                    if settings_registered:
                        debug(f"Registered hook '{hook_name}' in settings")
                    else:
                        warning(f"Failed to register hook '{hook_name}' in settings")
                else:
                    warning(f"Hook '{hook_name}' validation failed for settings integration: {', '.join(validation_errors)}")
            
            info(f"{'[DRY RUN] ' if self.dry_run else ''}Successfully installed hook: {hook_name}")
            
            return HookInstallationResult(
                hook_name=hook_name,
                success=True,
                message=f"Hook '{hook_name}' installed successfully",
                installed_path=hook_install_dir,
                scripts_installed=installed_scripts
            )
            
        except Exception as e:
            log_error(f"Failed to install hook '{hook_name}': {e}")
            return HookInstallationResult(
                hook_name=hook_name,
                success=False,
                message=f"Installation failed: {e}",
                error=e
            )
    
    def install_hooks(self, hook_names: List[str]) -> HookInstallationReport:
        """Install multiple hooks with progress tracking.
        
        Args:
            hook_names: List of hook names to install
            
        Returns:
            HookInstallationReport with detailed results
        """
        report = HookInstallationReport(total_requested=len(hook_names))
        
        if not hook_names:
            report.end_time = datetime.now()
            return report
        
        # Create progress tracker
        steps = [
            ProgressStep(f"install_{i}", f"Installing {name}", StepStatus.PENDING)
            for i, name in enumerate(hook_names)
        ]
        
        progress = MultiStepProgress(
            title="Installing Hooks",
            steps=steps,
            show_details=True
        )
        
        with progress.live_display() as (live, update):
            
            for i, hook_name in enumerate(hook_names):
                step_id = f"install_{i}"
                progress.start_step(step_id)
                update()
                
                result = self.install_hook(hook_name)
                report.results.append(result)
                
                if result.success:
                    report.successful_installs += 1
                    progress.complete_step(step_id, success=True)
                    progress.update_step_progress(step_id, 100.0, f"✓ {hook_name}")
                else:
                    report.failed_installs += 1
                    progress.complete_step(step_id, success=False, error_message=result.message)
                    progress.update_step_progress(step_id, 100.0, f"✗ {hook_name}: {result.message}")
                
                update()
        
        report.end_time = datetime.now()
        return report
    
    def _validate_hook_dependencies(self, hook: Hook) -> Tuple[bool, List[str]]:
        """Validate hook dependencies.
        
        Args:
            hook: Hook to validate
            
        Returns:
            Tuple of (is_valid, list_of_missing_dependencies)
        """
        if not hook.dependencies or not self.dependency_validator:
            return True, []
        
        missing_deps = []
        
        for dep in hook.dependencies:
            # Check if dependency is available
            if not self.dependency_validator._check_tool_available(dep):
                missing_deps.append(dep)
        
        return len(missing_deps) == 0, missing_deps
    
    def _backup_existing_hook(self, hook_dir: Path) -> Path:
        """Backup existing hook directory.
        
        Args:
            hook_dir: Directory to backup
            
        Returns:
            Path to backup directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{hook_dir.name}_backup_{timestamp}"
        backup_path = hook_dir.parent / backup_name
        
        shutil.copytree(hook_dir, backup_path)
        info(f"Backed up existing hook to: {backup_path}")
        
        return backup_path
    
    def _make_executable(self, script_path: Path) -> None:
        """Make script file executable.
        
        Args:
            script_path: Path to script file
        """
        try:
            # Get current permissions
            current_mode = script_path.stat().st_mode
            
            # Add execute permissions for owner, group, and others
            new_mode = current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            
            # Set new permissions
            script_path.chmod(new_mode)
            debug(f"Made script executable: {script_path}")
            
        except Exception as e:
            warning(f"Failed to set executable permissions for {script_path}: {e}")
    
    def validate_hook_scripts(self, hook: Hook) -> Tuple[bool, List[str]]:
        """Validate hook scripts for syntax and compatibility.
        
        Args:
            hook: Hook to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        for script_name, script_content in hook.scripts.items():
            # Validate Python scripts
            if script_name.endswith('.py'):
                python_errors = self._validate_python_script(script_content, script_name)
                errors.extend(python_errors)
            
            # Validate shell scripts
            elif script_name.endswith(('.sh', '.bash')):
                shell_errors = self._validate_shell_script(script_content, script_name)
                errors.extend(shell_errors)
        
        return len(errors) == 0, errors
    
    def _validate_python_script(self, content: str, script_name: str) -> List[str]:
        """Validate Python script syntax.
        
        Args:
            content: Script content
            script_name: Script filename
            
        Returns:
            List of validation errors
        """
        errors = []
        
        try:
            # Check Python syntax
            compile(content, script_name, 'exec')
        except SyntaxError as e:
            errors.append(f"Python syntax error in {script_name}: {e}")
        
        # Check for required shebang
        lines = content.splitlines()
        if lines and not lines[0].startswith('#!'):
            errors.append(f"Python script {script_name} missing shebang line")
        
        return errors
    
    def _validate_shell_script(self, content: str, script_name: str) -> List[str]:
        """Validate shell script syntax.
        
        Args:
            content: Script content
            script_name: Script filename
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check for required shebang
        lines = content.splitlines()
        if not lines:
            errors.append(f"Shell script {script_name} is empty")
            return errors
        
        if not lines[0].startswith('#!'):
            errors.append(f"Shell script {script_name} missing shebang line")
        
        # Basic syntax checks
        content_lower = content.lower()
        
        # Check for balanced quotes (basic check)
        single_quotes = content.count("'") - content.count("\\'")
        double_quotes = content.count('"') - content.count('\\"')
        
        if single_quotes % 2 != 0:
            errors.append(f"Unmatched single quotes in {script_name}")
        if double_quotes % 2 != 0:
            errors.append(f"Unmatched double quotes in {script_name}")
        
        # Check for balanced braces/brackets
        if content.count('{') != content.count('}'):
            errors.append(f"Unmatched braces in {script_name}")
        if content.count('[') != content.count(']'):
            errors.append(f"Unmatched brackets in {script_name}")
        if content.count('(') != content.count(')'):
            errors.append(f"Unmatched parentheses in {script_name}")
        
        # Check for balanced if/then/fi statements
        import re
        if_count = len(re.findall(r'\bif\b', content, re.IGNORECASE))
        fi_count = len(re.findall(r'\bfi\b', content, re.IGNORECASE))
        
        if if_count != fi_count:
            errors.append(f"Unmatched if/fi statements in {script_name} (if: {if_count}, fi: {fi_count})")
        
        return errors
    
    def uninstall_hook(self, hook_name: str) -> HookInstallationResult:
        """Uninstall a hook.
        
        Args:
            hook_name: Name of hook to uninstall
            
        Returns:
            HookInstallationResult with uninstallation details
        """
        try:
            # Find hook installation directory
            hook_found = False
            hook_install_dir = None
            
            # Check each category directory
            for category_dir in self.hooks_dir.iterdir():
                if category_dir.is_dir():
                    potential_hook_dir = category_dir / hook_name
                    if potential_hook_dir.exists():
                        hook_install_dir = potential_hook_dir
                        hook_found = True
                        break
            
            if not hook_found:
                return HookInstallationResult(
                    hook_name=hook_name,
                    success=False,
                    message=f"Hook '{hook_name}' not found in installation directory"
                )
            
            # Read hook metadata for settings unregistration
            hook_to_unregister = None
            if not self.dry_run:
                metadata_path = hook_install_dir / "metadata.json"
                if metadata_path.exists():
                    try:
                        with metadata_path.open('r', encoding='utf-8') as f:
                            import json
                            metadata = json.load(f)
                        
                        # Reconstruct hook object for unregistration
                        from ..types import Hook, HookEvent, HookConfig
                        hook_to_unregister = Hook(
                            name=metadata["name"],
                            description=metadata["description"],
                            category=metadata["category"],
                            event=HookEvent(metadata["event"]),
                            matcher=metadata.get("matcher"),
                            dependencies=metadata.get("dependencies", []),
                            config=HookConfig(**metadata["config"]),
                            scripts={}  # Not needed for unregistration
                        )
                    except Exception as e:
                        warning(f"Failed to read hook metadata for settings unregistration: {e}")
                
                # Unregister hook from settings before removing files
                if hook_to_unregister:
                    settings_unregistered = unregister_hook_from_settings(hook_to_unregister)
                    if settings_unregistered:
                        debug(f"Unregistered hook '{hook_name}' from settings")
                    else:
                        warning(f"Failed to unregister hook '{hook_name}' from settings")
            
            # Backup before removal if requested
            if self.backup and not self.dry_run:
                self._backup_existing_hook(hook_install_dir)
            
            # Remove hook directory
            if not self.dry_run:
                shutil.rmtree(hook_install_dir)
                info(f"Removed hook directory: {hook_install_dir}")
            
            # Clean up empty category directory
            if not self.dry_run and hook_install_dir.parent.exists():
                try:
                    hook_install_dir.parent.rmdir()  # Only removes if empty
                    debug(f"Removed empty category directory: {hook_install_dir.parent}")
                except OSError:
                    pass  # Directory not empty, that's fine
            
            info(f"{'[DRY RUN] ' if self.dry_run else ''}Successfully uninstalled hook: {hook_name}")
            
            return HookInstallationResult(
                hook_name=hook_name,
                success=True,
                message=f"Hook '{hook_name}' uninstalled successfully"
            )
            
        except Exception as e:
            log_error(f"Failed to uninstall hook '{hook_name}': {e}")
            return HookInstallationResult(
                hook_name=hook_name,
                success=False,
                message=f"Uninstallation failed: {e}",
                error=e
            )


def create_hook_installer(
    target_dir: Optional[Path] = None,
    dry_run: bool = False,
    force: bool = False,
    backup: bool = True,
    validate_dependencies: bool = True,
) -> HookInstaller:
    """Create a hook installer instance.
    
    Args:
        target_dir: Target directory for installation
        dry_run: Simulate installation without changes
        force: Overwrite existing hooks
        backup: Backup existing hooks before overwriting
        validate_dependencies: Validate hook dependencies
        
    Returns:
        HookInstaller instance
    """
    return HookInstaller(
        target_dir=target_dir,
        dry_run=dry_run,
        force=force,
        backup=backup,
        validate_dependencies=validate_dependencies,
    )


def install_hook_simple(
    hook_name: str,
    target_dir: Optional[Path] = None,
    force: bool = False,
) -> bool:
    """Simple hook installation function.
    
    Args:
        hook_name: Name of hook to install
        target_dir: Target directory for installation
        force: Overwrite existing hooks
        
    Returns:
        True if installation successful, False otherwise
    """
    installer = create_hook_installer(target_dir=target_dir, force=force)
    result = installer.install_hook(hook_name)
    return result.success