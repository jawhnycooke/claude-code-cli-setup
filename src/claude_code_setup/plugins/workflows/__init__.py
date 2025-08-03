"""Workflow engine for plugin system."""

from .executor import WorkflowExecutionError, WorkflowExecutor, StepExecutor
from .registry import WorkflowRegistry
from .types import (
    StepCondition,
    StepResult,
    StepType,
    WorkflowContext,
    WorkflowDefinition,
    WorkflowResult,
    WorkflowStatus,
    WorkflowStep,
)

__all__ = [
    # Types
    "StepCondition",
    "StepResult", 
    "StepType",
    "WorkflowContext",
    "WorkflowDefinition",
    "WorkflowResult",
    "WorkflowStatus",
    "WorkflowStep",
    # Executor
    "WorkflowExecutionError",
    "WorkflowExecutor",
    "StepExecutor",
    # Registry
    "WorkflowRegistry",
]