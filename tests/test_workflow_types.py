"""Tests for workflow types and models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from claude_code_setup.plugins.workflows.types import (
    StepCondition,
    StepResult,
    StepType,
    WorkflowContext,
    WorkflowDefinition,
    WorkflowResult,
    WorkflowStatus,
    WorkflowStep,
)


class TestWorkflowTypes:
    """Test workflow type definitions."""
    
    def test_workflow_status_enum(self):
        """Test WorkflowStatus enum values."""
        assert WorkflowStatus.PENDING.value == "pending"
        assert WorkflowStatus.RUNNING.value == "running"
        assert WorkflowStatus.PAUSED.value == "paused"
        assert WorkflowStatus.COMPLETED.value == "completed"
        assert WorkflowStatus.FAILED.value == "failed"
        assert WorkflowStatus.CANCELLED.value == "cancelled"
        assert WorkflowStatus.SKIPPED.value == "skipped"
    
    def test_step_type_enum(self):
        """Test StepType enum values."""
        assert StepType.TEMPLATE.value == "template"
        assert StepType.HOOK.value == "hook"
        assert StepType.AGENT.value == "agent"
        assert StepType.COMMAND.value == "command"
        assert StepType.CONDITIONAL.value == "conditional"
        assert StepType.LOOP.value == "loop"
        assert StepType.PARALLEL.value == "parallel"
        assert StepType.SEQUENTIAL.value == "sequential"
    
    def test_step_condition_creation(self):
        """Test StepCondition creation."""
        condition = StepCondition(
            type="equals",
            field="variables.status",
            value="active"
        )
        assert condition.type == "equals"
        assert condition.field == "variables.status"
        assert condition.value == "active"
        assert condition.operator is None
        assert condition.conditions is None
        
        # With nested conditions
        condition = StepCondition(
            type="exists",
            field="variables.user",
            value=True,
            operator="and",
            conditions=[
                StepCondition(
                    type="equals",
                    field="variables.role",
                    value="admin"
                )
            ]
        )
        assert condition.operator == "and"
        assert len(condition.conditions) == 1
    
    def test_workflow_step_creation(self):
        """Test WorkflowStep creation."""
        # Template step
        step = WorkflowStep(
            id="apply-template",
            name="Apply Template",
            type=StepType.TEMPLATE,
            template="code-review"
        )
        assert step.id == "apply-template"
        assert step.type == StepType.TEMPLATE
        assert step.template == "code-review"
        assert step.config == {}
        assert step.inputs == {}
        assert step.outputs == {}
        
        # Agent step with full config
        step = WorkflowStep(
            id="run-agent",
            name="Run Agent",
            type=StepType.AGENT,
            description="Execute code review agent",
            agent="plugin/agent",
            config={"level": "strict"},
            inputs={"file": "current_file"},
            outputs={"result": "review_result"},
            condition=StepCondition(
                type="exists",
                field="current_file",
                value=True
            ),
            on_success="next-step",
            on_failure="error-handler",
            retry_count=2,
            timeout_seconds=120
        )
        assert step.agent == "plugin/agent"
        assert step.config["level"] == "strict"
        assert step.retry_count == 2
        assert step.condition.type == "exists"
    
    def test_workflow_step_validation(self):
        """Test WorkflowStep validation."""
        # Missing required fields
        with pytest.raises(ValidationError):
            WorkflowStep()
        
        # Invalid type
        with pytest.raises(ValidationError):
            WorkflowStep(
                id="test",
                name="Test",
                type="invalid"
            )
    
    def test_workflow_definition_creation(self):
        """Test WorkflowDefinition creation."""
        workflow = WorkflowDefinition(
            name="test-workflow",
            display_name="Test Workflow",
            description="A test workflow",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="Step 1",
                    type=StepType.COMMAND,
                    command="echo 'hello'"
                )
            ]
        )
        assert workflow.name == "test-workflow"
        assert workflow.version == "1.0.0"  # default
        assert workflow.entry_point == "main"  # default
        assert len(workflow.steps) == 1
        assert workflow.requires_agents == []
        assert workflow.default_config == {}
    
    def test_workflow_definition_with_all_fields(self):
        """Test WorkflowDefinition with all fields."""
        workflow = WorkflowDefinition(
            name="complex-workflow",
            display_name="Complex Workflow",
            description="A complex workflow",
            version="2.0.0",
            author="Test Author",
            tags=["test", "complex"],
            requires_agents=["plugin/agent1"],
            requires_hooks=["hook1"],
            requires_templates=["template1"],
            steps=[
                WorkflowStep(
                    id="main",
                    name="Main",
                    type=StepType.SEQUENTIAL,
                    steps=[
                        WorkflowStep(
                            id="child1",
                            name="Child 1",
                            type=StepType.COMMAND,
                            command="echo 'child'"
                        )
                    ]
                )
            ],
            entry_point="main",
            config_schema={
                "type": "object",
                "properties": {
                    "level": {"type": "string"}
                }
            },
            default_config={"level": "normal"},
            examples=[
                {
                    "description": "Run workflow",
                    "command": "workflow run complex-workflow"
                }
            ]
        )
        assert workflow.version == "2.0.0"
        assert workflow.author == "Test Author"
        assert "complex" in workflow.tags
        assert len(workflow.requires_agents) == 1
    
    def test_workflow_context_creation(self):
        """Test WorkflowContext creation."""
        context = WorkflowContext(
            workflow_id="123",
            workflow_name="test",
            project_path="/project"
        )
        assert context.workflow_id == "123"
        assert context.project_path == "/project"
        assert context.variables == {}
        assert context.config == {}
        assert context.current_step is None
        assert context.completed_steps == []
        assert context.failed_steps == []
        
        # With values
        context = WorkflowContext(
            workflow_id="456",
            workflow_name="test",
            project_path="/project",
            variables={"user": "admin"},
            config={"level": "strict"},
            current_step="step1",
            completed_steps=["step0"],
            started_at=datetime.now()
        )
        assert context.variables["user"] == "admin"
        assert context.current_step == "step1"
        assert len(context.completed_steps) == 1
    
    def test_step_result_creation(self):
        """Test StepResult creation."""
        now = datetime.now()
        result = StepResult(
            step_id="step1",
            status=WorkflowStatus.RUNNING,
            started_at=now
        )
        assert result.step_id == "step1"
        assert result.status == WorkflowStatus.RUNNING
        assert result.outputs == {}
        assert result.artifacts == {}
        assert result.error is None
        assert result.logs == []
        
        # With completion
        result = StepResult(
            step_id="step2",
            status=WorkflowStatus.COMPLETED,
            started_at=now,
            completed_at=datetime.now(),
            duration_seconds=1.5,
            outputs={"result": "success"},
            artifacts={"report.txt": "content"},
            logs=["Step completed"]
        )
        assert result.status == WorkflowStatus.COMPLETED
        assert result.duration_seconds == 1.5
        assert result.outputs["result"] == "success"
    
    def test_workflow_result_creation(self):
        """Test WorkflowResult creation."""
        now = datetime.now()
        result = WorkflowResult(
            workflow_id="123",
            workflow_name="test",
            status=WorkflowStatus.RUNNING,
            started_at=now,
            total_steps=5
        )
        assert result.workflow_id == "123"
        assert result.status == WorkflowStatus.RUNNING
        assert result.total_steps == 5
        assert result.completed_steps == 0
        assert result.failed_steps == 0
        assert result.step_results == {}
        
        # With completion
        result = WorkflowResult(
            workflow_id="456",
            workflow_name="test",
            status=WorkflowStatus.COMPLETED,
            started_at=now,
            completed_at=datetime.now(),
            duration_seconds=10.5,
            total_steps=3,
            completed_steps=3,
            step_results={
                "step1": StepResult(
                    step_id="step1",
                    status=WorkflowStatus.COMPLETED,
                    started_at=now
                )
            },
            outputs={"final": "result"},
            artifacts={"output.txt": "content"}
        )
        assert result.status == WorkflowStatus.COMPLETED
        assert result.completed_steps == 3
        assert len(result.step_results) == 1
        assert result.outputs["final"] == "result"