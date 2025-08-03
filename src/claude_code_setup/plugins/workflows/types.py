"""Workflow type definitions for plugin system."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class StepType(str, Enum):
    """Types of workflow steps."""
    
    TEMPLATE = "template"
    HOOK = "hook"
    AGENT = "agent"
    COMMAND = "command"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"


class StepCondition(BaseModel):
    """Condition for conditional execution."""
    
    type: str = Field(..., description="Condition type (equals, contains, exists, etc.)")
    field: str = Field(..., description="Field to check")
    value: Any = Field(..., description="Value to compare against")
    operator: Optional[str] = Field(None, description="Logical operator (and, or, not)")
    conditions: Optional[List["StepCondition"]] = Field(
        None,
        description="Nested conditions for compound logic"
    )


class WorkflowStep(BaseModel):
    """Individual step in a workflow."""
    
    id: str = Field(..., description="Unique step identifier")
    name: str = Field(..., description="Step name")
    type: StepType = Field(..., description="Type of step")
    description: Optional[str] = Field(None, description="Step description")
    
    # Execution target based on type
    template: Optional[str] = Field(None, description="Template to apply (for template type)")
    hook: Optional[str] = Field(None, description="Hook to trigger (for hook type)")
    agent: Optional[str] = Field(None, description="Agent to run (for agent type)")
    command: Optional[str] = Field(None, description="Command to execute (for command type)")
    
    # Step configuration
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Step-specific configuration"
    )
    inputs: Dict[str, str] = Field(
        default_factory=dict,
        description="Input mappings from context"
    )
    outputs: Dict[str, str] = Field(
        default_factory=dict,
        description="Output mappings to context"
    )
    
    # Control flow
    condition: Optional[StepCondition] = Field(
        None,
        description="Condition for step execution"
    )
    on_success: Optional[str] = Field(
        None,
        description="Next step ID on success"
    )
    on_failure: Optional[str] = Field(
        None,
        description="Next step ID on failure"
    )
    retry_count: int = Field(
        0,
        description="Number of retries on failure"
    )
    timeout_seconds: Optional[int] = Field(
        None,
        description="Step timeout in seconds"
    )
    
    # For composite steps
    steps: Optional[List["WorkflowStep"]] = Field(
        None,
        description="Child steps for sequential/parallel types"
    )
    loop_variable: Optional[str] = Field(
        None,
        description="Variable name for loop iteration"
    )
    loop_items: Optional[Union[str, List[Any]]] = Field(
        None,
        description="Items to loop over (can be context reference)"
    )


class WorkflowDefinition(BaseModel):
    """Complete workflow definition."""
    
    name: str = Field(..., description="Workflow unique name")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Workflow description")
    version: str = Field("1.0.0", description="Workflow version")
    
    # Workflow metadata
    author: Optional[str] = Field(None, description="Workflow author")
    tags: List[str] = Field(
        default_factory=list,
        description="Workflow tags for categorization"
    )
    
    # Requirements
    requires_agents: List[str] = Field(
        default_factory=list,
        description="Required agents (plugin/agent format)"
    )
    requires_hooks: List[str] = Field(
        default_factory=list,
        description="Required hooks"
    )
    requires_templates: List[str] = Field(
        default_factory=list,
        description="Required templates"
    )
    
    # Workflow structure
    steps: List[WorkflowStep] = Field(
        ...,
        description="Workflow steps"
    )
    entry_point: str = Field(
        "main",
        description="ID of the first step"
    )
    
    # Configuration
    config_schema: Optional[Dict[str, Any]] = Field(
        None,
        description="Schema for workflow configuration"
    )
    default_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Default configuration values"
    )
    
    # Examples
    examples: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Usage examples"
    )


class WorkflowContext(BaseModel):
    """Runtime context for workflow execution."""
    
    workflow_id: str = Field(..., description="Workflow instance ID")
    workflow_name: str = Field(..., description="Workflow definition name")
    project_path: str = Field(..., description="Project path")
    
    # Runtime data
    variables: Dict[str, Any] = Field(
        default_factory=dict,
        description="Workflow variables"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Workflow configuration"
    )
    
    # Execution state
    current_step: Optional[str] = Field(None, description="Current step ID")
    completed_steps: List[str] = Field(
        default_factory=list,
        description="Completed step IDs"
    )
    failed_steps: List[str] = Field(
        default_factory=list,
        description="Failed step IDs"
    )
    
    # Metadata
    started_at: Optional[datetime] = Field(None, description="Workflow start time")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class StepResult(BaseModel):
    """Result from step execution."""
    
    step_id: str = Field(..., description="Step that was executed")
    status: WorkflowStatus = Field(..., description="Step execution status")
    
    # Outputs
    outputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Step outputs"
    )
    artifacts: Dict[str, str] = Field(
        default_factory=dict,
        description="Generated artifacts"
    )
    
    # Execution details
    started_at: datetime = Field(..., description="Step start time")
    completed_at: Optional[datetime] = Field(None, description="Step completion time")
    duration_seconds: Optional[float] = Field(None, description="Execution duration")
    
    # Error information
    error: Optional[str] = Field(None, description="Error message if failed")
    error_details: Optional[Dict[str, Any]] = Field(
        None,
        description="Detailed error information"
    )
    
    # Logging
    logs: List[str] = Field(
        default_factory=list,
        description="Step execution logs"
    )


class WorkflowResult(BaseModel):
    """Complete workflow execution result."""
    
    workflow_id: str = Field(..., description="Workflow instance ID")
    workflow_name: str = Field(..., description="Workflow definition name")
    status: WorkflowStatus = Field(..., description="Overall workflow status")
    
    # Execution timeline
    started_at: datetime = Field(..., description="Workflow start time")
    completed_at: Optional[datetime] = Field(None, description="Workflow completion time")
    duration_seconds: Optional[float] = Field(None, description="Total execution duration")
    
    # Step results
    step_results: Dict[str, StepResult] = Field(
        default_factory=dict,
        description="Results for each step"
    )
    
    # Final outputs
    outputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Final workflow outputs"
    )
    artifacts: Dict[str, str] = Field(
        default_factory=dict,
        description="All generated artifacts"
    )
    
    # Summary
    total_steps: int = Field(..., description="Total number of steps")
    completed_steps: int = Field(0, description="Number of completed steps")
    failed_steps: int = Field(0, description="Number of failed steps")
    skipped_steps: int = Field(0, description="Number of skipped steps")
    
    # Error information
    errors: List[str] = Field(
        default_factory=list,
        description="All errors encountered"
    )
    
    # Context snapshot
    final_context: Optional[WorkflowContext] = Field(
        None,
        description="Final workflow context"
    )


# Update forward references
WorkflowStep.model_rebuild()
StepCondition.model_rebuild()