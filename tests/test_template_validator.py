"""Tests for enhanced template validation."""

import pytest
from rich.panel import Panel

from claude_code_setup.utils.template_validator import (
    TemplateValidator,
    ValidationIssue,
    ValidationSeverity,
    validate_template_content_enhanced,
    format_validation_report,
)
from claude_code_setup.types import Template, TemplateCategory


class TestTemplateValidator:
    """Test the TemplateValidator class."""
    
    def test_valid_template(self):
        """Test validation of a valid template."""
        template = Template(
            name="test-template",
            description="A test template for validation",
            category=TemplateCategory.GENERAL,
            content="""# Test Template

This is a test template that demonstrates proper structure.

## Description
This template helps with testing validation logic.

## Usage
Use this template to test the validation system.

### Example
```python
# Example code
print("Hello, world!")
```

## Notes
- This is a valid template
- It has all required sections
- The markdown structure is correct
"""
        )
        
        validator = TemplateValidator()
        is_valid, issues = validator.validate(template)
        
        assert is_valid is True
        assert len(issues) == 0
    
    def test_empty_content(self):
        """Test validation of template with empty content."""
        template = Template(
            name="empty-template",
            description="Empty template",
            category=TemplateCategory.GENERAL,
            content=""
        )
        
        validator = TemplateValidator()
        is_valid, issues = validator.validate(template)
        
        assert is_valid is False
        assert any(issue.code == "CONTENT_EMPTY" for issue in issues)
    
    def test_missing_title(self):
        """Test validation of template without title."""
        template = Template(
            name="no-title",
            description="Template without title",
            category=TemplateCategory.GENERAL,
            content="This template has no markdown title heading."
        )
        
        validator = TemplateValidator()
        is_valid, issues = validator.validate(template)
        
        assert is_valid is False
        assert any(issue.code == "CONTENT_NO_TITLE" for issue in issues)
        assert any(issue.code == "CONTENT_TOO_SHORT" for issue in issues)
    
    def test_security_patterns(self):
        """Test detection of security issues."""
        dangerous_content = """# Dangerous Template

<script>alert('XSS')</script>

Run this command:
```bash
rm -rf /
```

Or try: $(rm -rf ~)
"""
        
        validator = TemplateValidator()
        is_valid, issues = validator.validate_content_only(dangerous_content)
        
        assert is_valid is False
        
        # Check for specific security issues
        security_codes = [issue.code for issue in issues if issue.code and issue.code.startswith("SECURITY_")]
        assert "SECURITY_SCRIPT" in security_codes
        assert "SECURITY_RM_RF" in security_codes
        assert "SECURITY_CMD_INJECTION" in security_codes
    
    def test_invalid_metadata(self):
        """Test validation of invalid metadata."""
        template = Template(
            name="Invalid Name!",  # Contains invalid characters
            description="Short",  # Too short
            category=TemplateCategory.GENERAL,
            content="# Valid Content\n\nThis is valid content for testing metadata validation."
        )
        
        validator = TemplateValidator()
        is_valid, issues = validator.validate(template)
        
        assert is_valid is False
        assert any(issue.code == "METADATA_INVALID_NAME" for issue in issues)
        assert any(issue.code == "METADATA_SHORT_DESCRIPTION" for issue in issues)
    
    def test_unclosed_code_block(self):
        """Test detection of unclosed code blocks."""
        content = """# Template

Here's some code:
```python
def hello():
    print("Hello")
# Missing closing ```
"""
        
        validator = TemplateValidator()
        is_valid, issues = validator.validate_content_only(content)
        
        assert is_valid is False
        assert any(issue.code == "MARKDOWN_UNCLOSED_CODE" for issue in issues)
    
    def test_quality_warnings(self):
        """Test detection of quality issues."""
        content = """# Template with Issues

TODO: Fix this later
FIXME: This needs work

API_KEY = "secret123"
password = "admin"

Check http://localhost:8080 for details.
"""
        
        validator = TemplateValidator()
        is_valid, issues = validator.validate_content_only(content)
        
        # Should be valid but with warnings
        assert is_valid is True
        
        warning_codes = [issue.code for issue in issues if issue.severity == ValidationSeverity.WARNING]
        assert "QUALITY_TODO" in warning_codes
        assert "QUALITY_LOCALHOST" in warning_codes
        assert "QUALITY_SENSITIVE" in warning_codes
    
    def test_line_length_warning(self):
        """Test detection of overly long lines."""
        long_line = "x" * 600
        content = f"""# Template

This is normal.

{long_line}

This is also normal.
"""
        
        validator = TemplateValidator()
        is_valid, issues = validator.validate_content_only(content)
        
        assert is_valid is True  # Long lines are warnings, not errors
        assert any(issue.code == "CONTENT_LONG_LINE" for issue in issues)
        
        # Check line number is correct
        long_line_issue = next(i for i in issues if i.code == "CONTENT_LONG_LINE")
        assert long_line_issue.line_number == 5
    
    def test_heading_hierarchy(self):
        """Test markdown heading hierarchy validation."""
        content = """### Starting with H3

# Now H1

##### Skipping to H5
"""
        
        validator = TemplateValidator()
        is_valid, issues = validator.validate_content_only(content)
        
        warning_issues = [i for i in issues if i.severity == ValidationSeverity.WARNING]
        assert any("First heading should be level 1" in i.message for i in warning_issues)
        assert any("Heading level skipped" in i.message for i in warning_issues)
    
    def test_backward_compatibility(self):
        """Test backward compatibility function."""
        content = """# Valid Template

This is valid content.

<script>alert('bad')</script>
"""
        
        is_valid, errors = validate_template_content_enhanced(content)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Script tags are not allowed" in error for error in errors)


class TestValidationReport:
    """Test validation report formatting."""
    
    def test_format_empty_report(self):
        """Test formatting report with no issues."""
        report = format_validation_report([])
        assert "No validation issues found" in str(report.renderable)
    
    def test_format_report_with_issues(self):
        """Test formatting report with various issues."""
        issues = [
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Template has no title",
                code="CONTENT_NO_TITLE"
            ),
            ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Line too long",
                line_number=42,
                code="CONTENT_LONG_LINE",
                suggestion="Break into multiple lines"
            ),
            ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="Consider adding examples",
                code="QUALITY_NO_EXAMPLES"
            ),
        ]
        
        report = format_validation_report(issues)
        
        # The report is a Panel, we need to check its content
        # For now, just verify it was created successfully
        assert report is not None
        assert isinstance(report, Panel)


class TestSecurityValidation:
    """Test security-specific validation."""
    
    def test_javascript_protocols(self):
        """Test detection of javascript: protocols."""
        content = """# Template
        
[Click me](javascript:alert('XSS'))
"""
        validator = TemplateValidator()
        is_valid, issues = validator.validate_content_only(content)
        
        assert is_valid is False
        assert any(i.code == "SECURITY_JS_PROTOCOL" for i in issues)
    
    def test_event_handlers(self):
        """Test detection of event handlers."""
        content = """# Template
        
<div onclick="alert('XSS')">Click</div>
"""
        validator = TemplateValidator()
        is_valid, issues = validator.validate_content_only(content)
        
        assert is_valid is False
        assert any(i.code == "SECURITY_EVENT_HANDLER" for i in issues)
    
    def test_dangerous_commands(self):
        """Test detection of dangerous shell commands."""
        templates = [
            ("Fork bomb", ":(){ :|:& };:", "SECURITY_FORK_BOMB"),
            ("Base64 decode", "echo 'data' | base64 -d", "SECURITY_BASE64"),
            ("Eval usage", "eval(user_input)", "SECURITY_EVAL"),
        ]
        
        for desc, dangerous_code, expected_code in templates:
            content = f"""# {desc}
            
```bash
{dangerous_code}
```
"""
            validator = TemplateValidator()
            is_valid, issues = validator.validate_content_only(content)
            
            assert is_valid is False, f"Failed to detect: {desc}"
            assert any(i.code == expected_code for i in issues), f"Missing code: {expected_code}"