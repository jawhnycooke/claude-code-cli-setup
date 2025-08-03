"""Tests for workflow registry."""

import pytest

from claude_code_setup.plugins.workflows.registry import WorkflowRegistry
from claude_code_setup.plugins.workflows.types import (
    WorkflowDefinition,
    WorkflowStep,
    StepType,
)


class TestWorkflowRegistry:
    """Test workflow registry functionality."""
    
    @pytest.fixture
    def registry(self):
        """Create a test registry."""
        return WorkflowRegistry()
    
    @pytest.fixture
    def sample_workflow(self):
        """Create a sample workflow definition."""
        return WorkflowDefinition(
            name="test-workflow",
            display_name="Test Workflow",
            description="A test workflow",
            steps=[
                WorkflowStep(
                    id="main",
                    name="Main Step",
                    type=StepType.COMMAND,
                    command="echo test"
                )
            ]
        )
    
    def test_register_workflow(self, registry, sample_workflow):
        """Test registering a workflow."""
        registry.register_workflow("test-plugin", sample_workflow)
        
        # Check workflow is registered
        workflow = registry.get_workflow("test-plugin", "test-workflow")
        assert workflow is not None
        assert workflow.name == "test-workflow"
        assert workflow.display_name == "Test Workflow"
    
    def test_register_duplicate_workflow(self, registry, sample_workflow):
        """Test registering duplicate workflow."""
        registry.register_workflow("test-plugin", sample_workflow)
        
        # Should not raise, just update
        registry.register_workflow("test-plugin", sample_workflow)
        
        # Still only one workflow
        workflows = registry.list_workflows("test-plugin")
        assert len(workflows) == 1
    
    def test_unregister_workflow(self, registry, sample_workflow):
        """Test unregistering a workflow."""
        registry.register_workflow("test-plugin", sample_workflow)
        
        # Unregister
        result = registry.unregister_workflow("test-plugin", "test-workflow")
        assert result is True
        
        # Check workflow is gone
        workflow = registry.get_workflow("test-plugin", "test-workflow")
        assert workflow is None
    
    def test_unregister_nonexistent_workflow(self, registry):
        """Test unregistering non-existent workflow."""
        result = registry.unregister_workflow("test-plugin", "no-such-workflow")
        assert result is False
    
    def test_get_workflow(self, registry, sample_workflow):
        """Test getting a workflow."""
        registry.register_workflow("test-plugin", sample_workflow)
        
        # Get existing workflow
        workflow = registry.get_workflow("test-plugin", "test-workflow")
        assert workflow is not None
        assert workflow.name == "test-workflow"
        
        # Get non-existent workflow
        workflow = registry.get_workflow("test-plugin", "no-such-workflow")
        assert workflow is None
        
        # Get from non-existent plugin
        workflow = registry.get_workflow("no-plugin", "test-workflow")
        assert workflow is None
    
    def test_list_workflows(self, registry):
        """Test listing workflows."""
        # Empty registry
        workflows = registry.list_workflows("test-plugin")
        assert workflows == []
        
        # Add workflows
        workflow1 = WorkflowDefinition(
            name="workflow1",
            display_name="Workflow 1",
            description="First workflow",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="Step 1",
                    type=StepType.COMMAND,
                    command="echo 1"
                )
            ]
        )
        workflow2 = WorkflowDefinition(
            name="workflow2",
            display_name="Workflow 2",
            description="Second workflow",
            steps=[
                WorkflowStep(
                    id="step2",
                    name="Step 2",
                    type=StepType.COMMAND,
                    command="echo 2"
                )
            ]
        )
        
        registry.register_workflow("test-plugin", workflow1)
        registry.register_workflow("test-plugin", workflow2)
        
        # List workflows
        workflows = registry.list_workflows("test-plugin")
        assert len(workflows) == 2
        assert "workflow1" in workflows
        assert "workflow2" in workflows
    
    def test_list_all_workflows(self, registry):
        """Test listing all workflows from all plugins."""
        # Add workflows to different plugins
        workflow1 = WorkflowDefinition(
            name="workflow1",
            display_name="Workflow 1",
            description="First workflow",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="Step 1",
                    type=StepType.COMMAND,
                    command="echo 1"
                )
            ]
        )
        workflow2 = WorkflowDefinition(
            name="workflow2",
            display_name="Workflow 2",
            description="Second workflow",
            steps=[
                WorkflowStep(
                    id="step2",
                    name="Step 2",
                    type=StepType.COMMAND,
                    command="echo 2"
                )
            ]
        )
        
        registry.register_workflow("plugin1", workflow1)
        registry.register_workflow("plugin2", workflow2)
        
        # List all
        all_workflows = registry.list_workflows()
        assert len(all_workflows) == 2
        assert "plugin1/workflow1" in all_workflows
        assert "plugin2/workflow2" in all_workflows
    
    def test_unregister_plugin_workflows(self, registry):
        """Test unregistering all workflows from a plugin."""
        # Add multiple workflows
        workflow1 = WorkflowDefinition(
            name="workflow1",
            display_name="Workflow 1",
            description="First workflow",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="Step 1",
                    type=StepType.COMMAND,
                    command="echo 1"
                )
            ]
        )
        workflow2 = WorkflowDefinition(
            name="workflow2",
            display_name="Workflow 2",
            description="Second workflow",
            steps=[
                WorkflowStep(
                    id="step2",
                    name="Step 2",
                    type=StepType.COMMAND,
                    command="echo 2"
                )
            ]
        )
        
        registry.register_workflow("test-plugin", workflow1)
        registry.register_workflow("test-plugin", workflow2)
        
        # Unregister all
        count = registry.unregister_plugin_workflows("test-plugin")
        assert count == 2
        
        # Check all are gone
        workflows = registry.list_workflows("test-plugin")
        assert workflows == []
    
    def test_get_workflows_by_tag(self, registry):
        """Test getting workflows by tag."""
        # Add workflows with different tags
        workflow1 = WorkflowDefinition(
            name="review-workflow",
            display_name="Review Workflow",
            description="Code review workflow",
            tags=["code-review", "quality"],
            steps=[
                WorkflowStep(
                    id="review",
                    name="Review",
                    type=StepType.AGENT,
                    agent="plugin/reviewer"
                )
            ]
        )
        workflow2 = WorkflowDefinition(
            name="test-workflow",
            display_name="Test Workflow",
            description="Testing workflow",
            tags=["testing", "validation"],
            steps=[
                WorkflowStep(
                    id="test",
                    name="Test",
                    type=StepType.COMMAND,
                    command="pytest"
                )
            ]
        )
        workflow3 = WorkflowDefinition(
            name="quality-workflow",
            display_name="Quality Workflow",
            description="Quality check workflow",
            tags=["quality", "automated"],
            steps=[
                WorkflowStep(
                    id="check",
                    name="Check",
                    type=StepType.HOOK,
                    hook="quality-check"
                )
            ]
        )
        
        registry.register_workflow("plugin1", workflow1)
        registry.register_workflow("plugin1", workflow2)
        registry.register_workflow("plugin2", workflow3)
        
        # Search by tag
        results = registry.get_workflows_by_tag("quality")
        assert len(results) == 2
        workflow_names = [w.name for w in results]
        assert "review-workflow" in workflow_names
        assert "quality-workflow" in workflow_names
        
        # Search by another tag
        results = registry.get_workflows_by_tag("testing")
        assert len(results) == 1
        assert results[0].name == "test-workflow"
        
        # Search by non-existent tag
        results = registry.get_workflows_by_tag("deployment")
        assert results == []
    
    def test_validate_workflow_requirements(self, registry):
        """Test validating workflow requirements."""
        workflow = WorkflowDefinition(
            name="test-workflow",
            display_name="Test Workflow",
            description="Test workflow with requirements",
            requires_agents=["plugin/agent1", "plugin/agent2"],
            requires_hooks=["hook1"],
            requires_templates=["template1", "template2"],
            steps=[
                WorkflowStep(
                    id="step1",
                    name="Step 1",
                    type=StepType.COMMAND,
                    command="echo test",
                    on_success="step2"
                ),
                WorkflowStep(
                    id="step2",
                    name="Step 2",
                    type=StepType.COMMAND,
                    command="echo done",
                    on_failure="missing-step"
                )
            ]
        )
        
        # Test with missing requirements
        errors = registry.validate_workflow_requirements(
            workflow,
            available_agents=["plugin/agent1"],  # Missing agent2
            available_hooks=[],  # Missing hook1
            available_templates=["template1"]  # Missing template2
        )
        
        assert len(errors) == 5  # Including entry point error
        assert any("agent not found: plugin/agent2" in err for err in errors)
        assert any("hook not found: hook1" in err for err in errors)
        assert any("template not found: template2" in err for err in errors)
        assert any("unknown on_failure: missing-step" in err for err in errors)
        
        # Test with all requirements met
        errors = registry.validate_workflow_requirements(
            workflow,
            available_agents=["plugin/agent1", "plugin/agent2"],
            available_hooks=["hook1"],
            available_templates=["template1", "template2"]
        )
        
        # Step reference error and entry point error remain
        assert len(errors) == 2
        assert "unknown on_failure: missing-step" in errors[0]
    
    def test_search_workflows(self, registry):
        """Test searching workflows."""
        # Add workflows
        workflow1 = WorkflowDefinition(
            name="code-review",
            display_name="Code Review Process",
            description="Automated code review workflow",
            tags=["review", "quality"],
            steps=[WorkflowStep(id="main", name="Main", type=StepType.COMMAND, command="echo review")]
        )
        workflow2 = WorkflowDefinition(
            name="deploy-app",
            display_name="Deploy Application",
            description="Application deployment workflow",
            tags=["deployment", "production"],
            steps=[WorkflowStep(id="main", name="Main", type=StepType.COMMAND, command="echo deploy")]
        )
        workflow3 = WorkflowDefinition(
            name="test-suite",
            display_name="Test Suite Runner",
            description="Run comprehensive test suite",
            tags=["testing", "quality"],
            steps=[WorkflowStep(id="main", name="Main", type=StepType.COMMAND, command="echo test")]
        )
        
        registry.register_workflow("plugin1", workflow1)
        registry.register_workflow("plugin2", workflow2)
        registry.register_workflow("plugin2", workflow3)
        
        # Search by name
        results = registry.search_workflows("code")
        assert len(results) == 1
        assert results[0].name == "code-review"
        
        # Search by display name
        results = registry.search_workflows("application")
        assert len(results) == 1
        assert results[0].name == "deploy-app"
        
        # Search by description
        results = registry.search_workflows("workflow")
        assert len(results) == 2  # code-review and deploy-app
        
        # Search with tags
        results = registry.search_workflows("test", tags=["quality"])
        assert len(results) == 1
        assert results[0].name == "test-suite"
        
        # No matches
        results = registry.search_workflows("nonexistent")
        assert results == []