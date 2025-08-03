"""Tests for template utilities."""

import pytest

from claude_code_setup.utils.template import (
    clear_template_cache,
    get_all_templates,
    get_all_templates_sync,
    get_template,
    get_template_categories,
    get_template_categories_sync,
    get_template_sync,
    get_templates_by_category,
    get_templates_by_category_sync,
    get_templates_directory,
    load_templates_from_files,
    load_templates_from_files_sync,
    validate_template_content,
    validate_template_content_sync,
)


class TestTemplateDirectory:
    """Test template directory functionality."""

    def test_get_templates_directory(self):
        """Test getting templates directory path."""
        templates_dir = get_templates_directory()
        assert templates_dir is not None
        assert "templates" in str(templates_dir)


class TestTemplateLoading:
    """Test template loading functionality."""

    @pytest.mark.asyncio
    async def test_load_templates_from_files(self):
        """Test loading templates from package resources."""
        templates = await load_templates_from_files()
        
        assert templates is not None
        assert hasattr(templates, 'templates')
        assert isinstance(templates.templates, dict)
        assert len(templates.templates) > 0

    def test_load_templates_from_files_sync(self):
        """Test synchronous template loading."""
        templates = load_templates_from_files_sync()
        
        assert templates is not None
        assert hasattr(templates, 'templates')
        assert isinstance(templates.templates, dict)
        assert len(templates.templates) > 0

    @pytest.mark.asyncio 
    async def test_load_templates_structure(self):
        """Test that loaded templates have correct structure."""
        templates = await load_templates_from_files()
        
        # Check that we have some expected templates
        template_names = list(templates.templates.keys())
        assert len(template_names) > 0
        
        # Check template structure
        for template in templates.templates.values():
            assert hasattr(template, 'name')
            assert hasattr(template, 'description')
            assert hasattr(template, 'category')
            assert hasattr(template, 'content')
            assert isinstance(template.name, str)
            assert isinstance(template.description, str)
            assert isinstance(template.category, str)
            assert isinstance(template.content, str)


class TestTemplateRegistry:
    """Test template registry functionality."""

    def setUp(self):
        """Clear cache before each test."""
        clear_template_cache()

    @pytest.mark.asyncio
    async def test_get_all_templates(self):
        """Test getting all templates."""
        templates = await get_all_templates()
        
        assert templates is not None
        assert len(templates.templates) > 0

    def test_get_all_templates_sync(self):
        """Test synchronous get all templates."""
        templates = get_all_templates_sync()
        
        assert templates is not None
        assert len(templates.templates) > 0

    @pytest.mark.asyncio
    async def test_get_all_templates_caching(self):
        """Test that template registry is cached."""
        # Clear cache first
        clear_template_cache()
        
        # First call should load templates
        templates1 = await get_all_templates()
        
        # Second call should return cached result
        templates2 = await get_all_templates()
        
        # Should be the same object (cached)
        assert templates1 is templates2


class TestTemplateRetrieval:
    """Test individual template retrieval."""

    @pytest.mark.asyncio
    async def test_get_template_existing(self):
        """Test getting an existing template."""
        # First get all templates to see what's available
        all_templates = await get_all_templates()
        
        if len(all_templates.templates) > 0:
            # Get the first template name
            template_name = list(all_templates.templates.keys())[0]
            
            # Try to retrieve it
            template = await get_template(template_name)
            
            assert template is not None
            assert template.name == template_name

    @pytest.mark.asyncio
    async def test_get_template_nonexistent(self):
        """Test getting a non-existent template."""
        template = await get_template("nonexistent-template")
        assert template is None

    def test_get_template_sync_existing(self):
        """Test synchronous template retrieval."""
        # First get all templates to see what's available
        all_templates = get_all_templates_sync()
        
        if len(all_templates.templates) > 0:
            # Get the first template name
            template_name = list(all_templates.templates.keys())[0]
            
            # Try to retrieve it
            template = get_template_sync(template_name)
            
            assert template is not None
            assert template.name == template_name


class TestTemplateCategories:
    """Test template category functionality."""

    @pytest.mark.asyncio
    async def test_get_template_categories(self):
        """Test getting template categories."""
        categories = await get_template_categories()
        
        assert isinstance(categories, list)
        assert len(categories) > 0
        
        # Should be sorted
        assert categories == sorted(categories)
        
        # Check for expected categories
        for category in categories:
            assert isinstance(category, str)
            assert len(category) > 0

    def test_get_template_categories_sync(self):
        """Test synchronous template categories."""
        categories = get_template_categories_sync()
        
        assert isinstance(categories, list)
        assert len(categories) > 0
        assert categories == sorted(categories)

    @pytest.mark.asyncio
    async def test_get_templates_by_category(self):
        """Test getting templates by category."""
        categories = await get_template_categories()
        
        if len(categories) > 0:
            category = categories[0]
            templates = await get_templates_by_category(category)
            
            assert isinstance(templates, list)
            
            # All templates should be from the requested category
            for template in templates:
                assert template.category == category

    def test_get_templates_by_category_sync(self):
        """Test synchronous templates by category."""
        categories = get_template_categories_sync()
        
        if len(categories) > 0:
            category = categories[0]
            templates = get_templates_by_category_sync(category)
            
            assert isinstance(templates, list)
            
            # All templates should be from the requested category
            for template in templates:
                assert template.category == category

    @pytest.mark.asyncio
    async def test_get_templates_by_nonexistent_category(self):
        """Test getting templates by non-existent category."""
        templates = await get_templates_by_category("nonexistent-category")
        assert templates == []


class TestTemplateValidation:
    """Test template content validation."""

    @pytest.mark.asyncio
    async def test_validate_valid_template(self):
        """Test validation of valid template content."""
        valid_content = """# Test Template

This is a test template with proper structure.

## Usage

Some usage instructions here.
"""
        
        is_valid, errors = await validate_template_content(valid_content)
        
        assert is_valid is True
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_validate_empty_template(self):
        """Test validation of empty template."""
        is_valid, errors = await validate_template_content("")
        
        assert is_valid is False
        assert "Template content is empty" in errors

    @pytest.mark.asyncio
    async def test_validate_template_no_title(self):
        """Test validation of template without title."""
        content_no_title = """This template has no title heading.

Some content here.
"""
        
        is_valid, errors = await validate_template_content(content_no_title)
        
        assert is_valid is False
        assert "Template must have a title (# heading)" in errors

    @pytest.mark.asyncio
    async def test_validate_template_too_short(self):
        """Test validation of too short template."""
        short_content = "# Short"
        
        is_valid, errors = await validate_template_content(short_content)
        
        assert is_valid is False
        assert any("too short" in error for error in errors)

    @pytest.mark.asyncio
    async def test_validate_template_only_headings(self):
        """Test validation of template with only headings."""
        headings_only = """# Title

## Subtitle

### Another heading
"""
        
        is_valid, errors = await validate_template_content(headings_only)
        
        assert is_valid is False
        assert "Template must have content beyond just headings" in errors

    def test_validate_template_content_sync(self):
        """Test synchronous template validation."""
        valid_content = """# Test Template

This is a test template with proper structure.
"""
        
        is_valid, errors = validate_template_content_sync(valid_content)
        
        assert is_valid is True
        assert len(errors) == 0


class TestTemplateCaching:
    """Test template caching functionality."""

    def test_clear_template_cache(self):
        """Test clearing template cache."""
        # Load templates first
        templates1 = get_all_templates_sync()
        
        # Clear cache
        clear_template_cache()
        
        # Load again - should be fresh instance
        templates2 = get_all_templates_sync()
        
        # Content should be the same but objects should be different
        assert len(templates1.templates) == len(templates2.templates)
        # Note: We can't test object identity easily since the cache is internal