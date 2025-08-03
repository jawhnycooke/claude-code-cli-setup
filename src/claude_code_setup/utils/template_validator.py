"""Enhanced template validation for claude-code-setup.

This module provides comprehensive template validation with detailed error
reporting, security checks, and user-friendly feedback.
"""

import re
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from rich.panel import Panel

from ..types import Template, TemplateCategory
from ..ui.styles import (
    console,
    create_validation_error,
    create_panel,
    COLORS,
)
from .dependency_validator import create_dependency_validator


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a validation issue found in a template."""
    severity: ValidationSeverity
    message: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    code: Optional[str] = None  # Error code for programmatic handling


class TemplateValidator:
    """Comprehensive template validator with enhanced error reporting."""
    
    # Validation rules configuration
    MIN_CONTENT_LENGTH = 50  # Minimum meaningful content
    MAX_CONTENT_LENGTH = 100_000  # 100KB limit
    MAX_LINE_LENGTH = 500  # Prevent extremely long lines
    
    # Required sections for a complete template
    REQUIRED_SECTIONS = [
        "description",  # What the template does
        "usage",  # How to use it
    ]
    
    # Suspicious patterns that might indicate security issues
    SECURITY_PATTERNS = [
        # Script injection
        (r'<script[^>]*>', "Script tags are not allowed in templates", "SECURITY_SCRIPT"),
        (r'javascript:', "JavaScript protocol is not allowed", "SECURITY_JS_PROTOCOL"),
        (r'on\w+\s*=', "Event handlers are not allowed", "SECURITY_EVENT_HANDLER"),
        
        # Data protocols that could be malicious
        (r'data:text/html', "HTML data URIs are not allowed", "SECURITY_DATA_URI"),
        (r'data:application/javascript', "JavaScript data URIs are not allowed", "SECURITY_JS_DATA"),
        
        # File system operations
        (r'rm\s+-rf\s+/', "Dangerous file removal commands detected", "SECURITY_RM_RF"),
        (r':(){ :|:& };:', "Fork bomb pattern detected", "SECURITY_FORK_BOMB"),
        
        # Command injection patterns
        (r'\$\(.*rm.*\)', "Command substitution with rm detected", "SECURITY_CMD_INJECTION"),
        (r'`.*rm.*`', "Backtick command with rm detected", "SECURITY_BACKTICK_RM"),
        
        # Obfuscation attempts
        (r'eval\s*\(', "Eval usage detected", "SECURITY_EVAL"),
        (r'exec\s*\(', "Exec usage detected", "SECURITY_EXEC"),
        (r'base64\s+-d', "Base64 decode command detected", "SECURITY_BASE64"),
    ]
    
    # Common template issues to warn about
    WARNING_PATTERNS = [
        (r'TODO|FIXME|XXX', "Template contains TODO/FIXME markers", "QUALITY_TODO"),
        (r'http://localhost', "Template contains localhost URLs", "QUALITY_LOCALHOST"),
        (r'api[_-]?key|password|secret', "Template may contain sensitive information", "QUALITY_SENSITIVE"),
    ]
    
    def __init__(self):
        """Initialize the template validator."""
        self.issues: List[ValidationIssue] = []
    
    def validate(self, template: Template) -> Tuple[bool, List[ValidationIssue]]:
        """Validate a template with comprehensive checks.
        
        Args:
            template: Template to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        self.issues = []
        
        # Validate metadata
        self._validate_metadata(template)
        
        # Validate content
        if template.content:
            self._validate_content(template.content)
            self._check_security_patterns(template.content)
            self._check_quality_patterns(template.content)
            self._validate_markdown_structure(template.content)
        else:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Template has no content",
                code="CONTENT_EMPTY"
            ))
        
        # Check if there are any errors
        has_errors = any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)
        return not has_errors, self.issues
    
    def validate_content_only(self, content: str) -> Tuple[bool, List[ValidationIssue]]:
        """Validate just the content string.
        
        Args:
            content: Template content to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        self.issues = []
        self._validate_content(content)
        self._check_security_patterns(content)
        self._check_quality_patterns(content)
        self._validate_markdown_structure(content)
        self._validate_dependencies(content)
        
        has_errors = any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)
        return not has_errors, self.issues
    
    def _validate_metadata(self, template: Template) -> None:
        """Validate template metadata."""
        # Check name
        if not template.name:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Template must have a name",
                code="METADATA_NO_NAME"
            ))
        elif not re.match(r'^[a-z0-9-]+$', template.name):
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Template name must contain only lowercase letters, numbers, and hyphens",
                suggestion=f"Try: {template.name.lower().replace('_', '-').replace(' ', '-')}",
                code="METADATA_INVALID_NAME"
            ))
        
        # Check description
        if not template.description:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Template must have a description",
                code="METADATA_NO_DESCRIPTION"
            ))
        elif len(template.description) < 10:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Template description is too short",
                suggestion="Add a more detailed description of what this template does",
                code="METADATA_SHORT_DESCRIPTION"
            ))
        
        # Check category
        if not template.category:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Template must have a category",
                code="METADATA_NO_CATEGORY"
            ))
    
    def _validate_content(self, content: str) -> None:
        """Validate template content basics."""
        # Check if empty
        if not content or not content.strip():
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Template content is empty",
                code="CONTENT_EMPTY"
            ))
            return
        
        # Check length
        content_length = len(content)
        if content_length < self.MIN_CONTENT_LENGTH:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"Template content is too short (minimum {self.MIN_CONTENT_LENGTH} characters)",
                suggestion="Add more detailed instructions and examples",
                code="CONTENT_TOO_SHORT"
            ))
        elif content_length > self.MAX_CONTENT_LENGTH:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"Template content is too large (maximum {self.MAX_CONTENT_LENGTH} characters)",
                suggestion="Consider splitting into multiple templates",
                code="CONTENT_TOO_LARGE"
            ))
        
        # Check for title
        if not re.search(r'^#\s+.+$', content, re.MULTILINE):
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Template must have a title (# heading)",
                suggestion="Add a title at the beginning: # Template Title",
                code="CONTENT_NO_TITLE"
            ))
        
        # Check line length
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if len(line) > self.MAX_LINE_LENGTH:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Line {i} is too long ({len(line)} characters)",
                    line_number=i,
                    suggestion="Consider breaking long lines for better readability",
                    code="CONTENT_LONG_LINE"
                ))
    
    def _check_security_patterns(self, content: str) -> None:
        """Check for security issues in template content."""
        for pattern, message, code in self.SECURITY_PATTERNS:
            matches = list(re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE))
            for match in matches:
                # Find line number
                line_num = content[:match.start()].count('\n') + 1
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Security issue: {message}",
                    line_number=line_num,
                    code=code
                ))
    
    def _check_quality_patterns(self, content: str) -> None:
        """Check for quality issues in template content."""
        for pattern, message, code in self.WARNING_PATTERNS:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            if matches:
                # Only report first occurrence to avoid spam
                match = matches[0]
                line_num = content[:match.start()].count('\n') + 1
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=message,
                    line_number=line_num,
                    code=code
                ))
    
    def _validate_markdown_structure(self, content: str) -> None:
        """Validate markdown structure and formatting."""
        lines = content.split('\n')
        in_code_block = False
        code_block_lang = None
        code_block_start = 0
        has_content = False
        heading_levels = []
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Track code blocks
            if stripped.startswith('```'):
                if in_code_block:
                    in_code_block = False
                    code_block_lang = None
                else:
                    in_code_block = True
                    code_block_start = i
                    # Extract language
                    lang_match = re.match(r'```(\w+)', stripped)
                    if lang_match:
                        code_block_lang = lang_match.group(1)
            
            # Check for content
            if stripped and not stripped.startswith('#') and not in_code_block:
                has_content = True
            
            # Track heading hierarchy
            heading_match = re.match(r'^(#+)\s+(.+)$', stripped)
            if heading_match and not in_code_block:
                level = len(heading_match.group(1))
                heading_levels.append((level, i))
        
        # Check for unclosed code blocks
        if in_code_block:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Unclosed code block",
                line_number=code_block_start,
                suggestion="Add ``` to close the code block",
                code="MARKDOWN_UNCLOSED_CODE"
            ))
        
        # Check for content
        if not has_content:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Template must have content beyond just headings",
                suggestion="Add descriptions, usage examples, or instructions",
                code="MARKDOWN_NO_CONTENT"
            ))
        
        # Check heading hierarchy
        if heading_levels:
            # Check if first heading is not level 1
            if heading_levels[0][0] != 1:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message="First heading should be level 1 (#)",
                    line_number=heading_levels[0][1],
                    code="MARKDOWN_HEADING_HIERARCHY"
                ))
            
            # Check for skipped levels
            prev_level = heading_levels[0][0]
            for level, line_num in heading_levels[1:]:
                if level > prev_level + 1:
                    self.issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Heading level skipped (from {prev_level} to {level})",
                        line_number=line_num,
                        suggestion="Use sequential heading levels",
                        code="MARKDOWN_HEADING_SKIP"
                    ))
                prev_level = level
    
    def _validate_dependencies(self, content: str) -> None:
        """Validate template dependencies are available."""
        validator = create_dependency_validator()
        
        # Check dependencies
        all_valid, missing_tools, warnings = validator.validate_template_dependencies(
            content, "template"
        )
        
        # Add issues for missing tools
        for tool in missing_tools:
            self._add_issue(
                ValidationSeverity.WARNING,
                f"Required tool '{tool}' may not be installed",
                suggestion=f"Install {tool} before using this template"
            )
            
        # Add warnings
        for warning_msg in warnings:
            self._add_issue(
                ValidationSeverity.INFO,
                warning_msg
            )
    
    def _add_issue(
        self,
        severity: ValidationSeverity,
        message: str,
        line_number: Optional[int] = None,
        suggestion: Optional[str] = None,
        code: Optional[str] = None,
    ) -> None:
        """Add a validation issue to the list.
        
        Args:
            severity: Issue severity level
            message: Issue message
            line_number: Optional line number
            suggestion: Optional suggestion for fixing
            code: Optional error code
        """
        self.issues.append(ValidationIssue(
            severity=severity,
            message=message,
            line_number=line_number,
            suggestion=suggestion,
            code=code,
        ))


def format_validation_report(issues: List[ValidationIssue], title: str = "Template Validation Report") -> Panel:
    """Format validation issues into a user-friendly report.
    
    Args:
        issues: List of validation issues
        title: Report title
        
    Returns:
        Formatted panel with validation report
    """
    from rich.table import Table
    from rich.text import Text
    
    if not issues:
        content = Text("✅ No validation issues found!", style=COLORS['success'])
        return create_panel(content, title=title, border_style=COLORS['success'])
    
    # Group issues by severity
    errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
    warnings = [i for i in issues if i.severity == ValidationSeverity.WARNING]
    info = [i for i in issues if i.severity == ValidationSeverity.INFO]
    
    # Create table
    table = Table(show_header=True, show_edge=False, box=None)
    table.add_column("Severity", style="bold")
    table.add_column("Line", justify="right")
    table.add_column("Issue")
    table.add_column("Suggestion")
    
    # Add errors
    for issue in errors:
        line_str = str(issue.line_number) if issue.line_number else "-"
        suggestion = issue.suggestion or ""
        table.add_row(
            Text("ERROR", style=COLORS['error']),
            line_str,
            issue.message,
            suggestion
        )
    
    # Add warnings
    for issue in warnings:
        line_str = str(issue.line_number) if issue.line_number else "-"
        suggestion = issue.suggestion or ""
        table.add_row(
            Text("WARN", style=COLORS['warning']),
            line_str,
            issue.message,
            suggestion
        )
    
    # Add info
    for issue in info:
        line_str = str(issue.line_number) if issue.line_number else "-"
        suggestion = issue.suggestion or ""
        table.add_row(
            Text("INFO", style=COLORS['info']),
            line_str,
            issue.message,
            suggestion
        )
    
    # Create summary
    summary = f"\n"
    if errors:
        summary += f"[{COLORS['error']}]❌ {len(errors)} error(s)[/{COLORS['error']}] "
    if warnings:
        summary += f"[{COLORS['warning']}]⚠️  {len(warnings)} warning(s)[/{COLORS['warning']}] "
    if info:
        summary += f"[{COLORS['info']}]ℹ️  {len(info)} info[/{COLORS['info']}]"
    
    # Combine table and summary
    from rich.console import Group
    content = Group(table, Text(summary))
    
    # Determine border style
    border_style = COLORS['error'] if errors else COLORS['warning']
    
    return create_panel(
        content,
        title=title,
        border_style=border_style
    )


# Backward compatibility function
def validate_template_content_enhanced(content: str) -> Tuple[bool, List[str]]:
    """Enhanced validation with backward compatibility.
    
    Args:
        content: Template content to validate
        
    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    validator = TemplateValidator()
    is_valid, issues = validator.validate_content_only(content)
    
    # Convert issues to simple error messages for backward compatibility
    error_messages = []
    for issue in issues:
        if issue.severity == ValidationSeverity.ERROR:
            msg = issue.message
            if issue.line_number:
                msg = f"Line {issue.line_number}: {msg}"
            error_messages.append(msg)
    
    return is_valid, error_messages