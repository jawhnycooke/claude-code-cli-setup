"""Agent type definitions for the plugin system."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class AgentCapability(str, Enum):
    """Agent capabilities that can be declared."""
    
    CODE_REVIEW = "code_review"
    CODE_GENERATION = "code_generation"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    REFACTORING = "refactoring"
    SECURITY_ANALYSIS = "security_analysis"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    ARCHITECTURE_REVIEW = "architecture_review"
    GENERAL = "general"


class AgentStatus(str, Enum):
    """Agent execution status."""
    
    IDLE = "idle"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentMessage(BaseModel):
    """Message in agent conversation."""
    
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Message timestamp"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional message metadata"
    )


class AgentContext(BaseModel):
    """Context provided to an agent for execution."""
    
    project_path: str = Field(..., description="Path to the project")
    current_file: Optional[str] = Field(
        None,
        description="Current file being worked on"
    )
    selected_text: Optional[str] = Field(
        None,
        description="Selected text in editor"
    )
    variables: Dict[str, Any] = Field(
        default_factory=dict,
        description="Context variables"
    )
    history: List[AgentMessage] = Field(
        default_factory=list,
        description="Conversation history"
    )
    tools_available: List[str] = Field(
        default_factory=list,
        description="Available tool names"
    )


class AgentDefinition(BaseModel):
    """Agent definition from a plugin."""
    
    name: str = Field(..., description="Agent unique name")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Agent description")
    capabilities: List[AgentCapability] = Field(
        ...,
        description="Agent capabilities"
    )
    entry_point: str = Field(
        ...,
        description="Python module path or script path"
    )
    config_schema: Optional[Dict[str, Any]] = Field(
        None,
        description="Configuration schema"
    )
    requires_tools: List[str] = Field(
        default_factory=list,
        description="Required Claude tools"
    )
    max_iterations: int = Field(
        10,
        description="Maximum iterations allowed"
    )
    timeout_seconds: int = Field(
        300,
        description="Execution timeout in seconds"
    )
    system_prompt: Optional[str] = Field(
        None,
        description="Custom system prompt"
    )
    examples: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Usage examples"
    )


class AgentResponse(BaseModel):
    """Response from agent execution."""
    
    status: AgentStatus = Field(..., description="Execution status")
    messages: List[AgentMessage] = Field(
        default_factory=list,
        description="Response messages"
    )
    results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution results"
    )
    artifacts: Dict[str, str] = Field(
        default_factory=dict,
        description="Generated artifacts (name -> content)"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Any errors encountered"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    duration_seconds: Optional[float] = Field(
        None,
        description="Execution duration"
    )


class AgentExecutor(BaseModel):
    """Agent executor configuration."""
    
    agent_name: str = Field(..., description="Agent to execute")
    plugin_name: str = Field(..., description="Plugin providing the agent")
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Agent configuration"
    )
    context: AgentContext = Field(..., description="Execution context")
    stream: bool = Field(
        False,
        description="Stream responses"
    )
    debug: bool = Field(
        False,
        description="Enable debug mode"
    )