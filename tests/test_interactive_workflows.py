"""Tests for interactive workflows and validation enhancements."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from claude_code_setup.cli import cli
from claude_code_setup.commands.interactive import (
    show_main_menu,
    template_management_menu,
    settings_configuration_menu,
    search_templates_interactive,
    preview_template_interactive,
    create_configuration_summary,
)
from claude_code_setup.utils.dependency_validator import DependencyValidator
from claude_code_setup.utils.template_validator import TemplateValidator, ValidationSeverity
from claude_code_setup.utils.template import Template


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_templates():
    """Create mock templates for testing."""
    return [
        Template(
            name="python-script",
            content="#!/usr/bin/env python\nimport requests\nprint('Hello')",
            category="python",
            description="Python script template",
        ),
        Template(
            name="node-app",
            content="const express = require('express');\nnpm install express",
            category="node",
            description="Node.js app template",
        ),
    ]


class TestInteractiveMenus:
    """Test interactive menu functions."""
    
    def test_show_main_menu_selection(self):
        """Test main menu selection."""
        with patch("claude_code_setup.commands.interactive.ValidatedPrompt") as mock_prompt:
            mock_prompt.return_value.ask.return_value = "1"
            
            result = show_main_menu()
            
            assert result == "quick-setup"
            
    def test_show_main_menu_exit(self):
        """Test main menu exit selection."""
        with patch("claude_code_setup.commands.interactive.ValidatedPrompt") as mock_prompt:
            mock_prompt.return_value.ask.return_value = "7"
            
            result = show_main_menu()
            
            assert result is None
            
    def test_template_management_menu(self):
        """Test template management submenu."""
        with patch("claude_code_setup.commands.interactive.ValidatedPrompt") as mock_prompt:
            mock_prompt.return_value.ask.return_value = "1"
            
            result = template_management_menu()
            
            assert result == "add-templates"
            
    def test_settings_configuration_menu(self):
        """Test settings configuration submenu."""
        with patch("claude_code_setup.commands.interactive.ValidatedPrompt") as mock_prompt:
            mock_prompt.return_value.ask.return_value = "1"
            
            result = settings_configuration_menu()
            
            assert result == "change-theme"


class TestSearchAndPreview:
    """Test search and preview functionality."""
    
    def test_search_templates_with_query(self, mock_templates):
        """Test searching templates with a query."""
        with patch("claude_code_setup.commands.interactive.ValidatedPrompt") as mock_prompt:
            with patch("claude_code_setup.commands.interactive.MultiSelectPrompt") as mock_select:
                mock_prompt.return_value.ask.return_value = "python"
                mock_select.return_value.ask.return_value = ["  python-script - Python script template"]
                
                result = search_templates_interactive(mock_templates)
                
                assert result == ["python-script"]
                
    def test_search_templates_no_results(self, mock_templates):
        """Test searching with no matching results."""
        with patch("claude_code_setup.commands.interactive.ValidatedPrompt") as mock_prompt:
            mock_prompt.return_value.ask.return_value = "nonexistent"
            
            result = search_templates_interactive(mock_templates)
            
            assert result is None
            
    def test_preview_template_interactive(self, mock_templates):
        """Test interactive template preview."""
        with patch("claude_code_setup.commands.interactive.ValidatedPrompt") as mock_prompt:
            with patch("claude_code_setup.utils.template.get_template_sync") as mock_get:
                mock_prompt.return_value.ask.side_effect = ["python-script", "n"]
                mock_get.return_value = mock_templates[0]
                
                result = preview_template_interactive(mock_templates)
                
                assert result is True  # Continue browsing
                

class TestDependencyValidation:
    """Test dependency validation functionality."""
    
    def test_validate_python_dependencies(self):
        """Test Python dependency validation."""
        validator = DependencyValidator()
        content = """
        import requests
        import numpy as np
        pip install requests
        """
        
        valid, missing, warnings = validator.validate_template_dependencies(
            content, "test-template"
        )
        
        # Should detect Python requirement
        assert "python" in validator._extract_tool_requirements(content)
        
    def test_validate_node_dependencies(self):
        """Test Node.js dependency validation."""
        validator = DependencyValidator()
        content = """
        npm install express
        const app = require('express')();
        """
        
        valid, missing, warnings = validator.validate_template_dependencies(
            content, "test-template"
        )
        
        # Should detect npm requirement
        assert "npm" in validator._extract_tool_requirements(content)
        
    def test_extract_tool_requirements(self):
        """Test tool requirement extraction."""
        validator = DependencyValidator()
        content = """
        npm install package
        python script.py
        git clone repo
        docker-compose up
        """
        
        tools = validator._extract_tool_requirements(content)
        
        assert "npm" in tools
        assert "python" in tools
        assert "git" in tools
        assert "docker-compose" in tools


class TestEnhancedValidation:
    """Test enhanced template validation with dependencies."""
    
    def test_template_validator_with_dependencies(self):
        """Test template validation includes dependency checks."""
        validator = TemplateValidator()
        content = """
        # Template with Dependencies
        
        This template requires Node.js:
        
        ```bash
        npm install express
        node server.js
        ```
        """
        
        # Mock dependency validator to return missing tools
        with patch("claude_code_setup.utils.template_validator.create_dependency_validator") as mock_create:
            mock_validator = MagicMock()
            mock_validator.validate_template_dependencies.return_value = (
                False, 
                ["npm", "node"], 
                ["Package 'express' may need to be installed"]
            )
            mock_create.return_value = mock_validator
            
            is_valid, issues = validator.validate_content_only(content)
            
            # Should have warnings for missing tools
            tool_warnings = [
                i for i in issues 
                if i.severity == ValidationSeverity.WARNING 
                and "npm" in i.message
            ]
            assert len(tool_warnings) > 0
            
    def test_configuration_summary(self, tmp_path):
        """Test configuration summary creation."""
        # Create test configuration
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        
        # Create settings
        settings_path = claude_dir / "settings.json"
        settings_path.write_text('{"theme": "dark", "allowedTools": ["npm", "git"]}')
        
        # Create some templates
        commands_dir = claude_dir / "commands"
        general_dir = commands_dir / "general"
        general_dir.mkdir(parents=True)
        (general_dir / "test.md").write_text("# Test")
        
        panel = create_configuration_summary(claude_dir)
        
        assert panel is not None
        assert isinstance(panel.renderable, str)


class TestCLIInteractiveCommand:
    """Test the CLI interactive command."""
    
    def test_cli_interactive_command_exists(self, runner):
        """Test that interactive command is available."""
        result = runner.invoke(cli, ["--help"])
        
        assert "interactive" in result.output
        assert result.exit_code == 0
        
    def test_cli_interactive_mode_exit(self, runner, tmp_path):
        """Test interactive mode with immediate exit."""
        with patch("claude_code_setup.commands.interactive.show_main_menu") as mock_menu:
            mock_menu.return_value = None  # Exit immediately
            
            result = runner.invoke(
                cli, 
                ["interactive", "--test-dir", str(tmp_path)]
            )
            
            assert result.exit_code == 0
            assert "Thank you for using Claude Code Setup" in result.output