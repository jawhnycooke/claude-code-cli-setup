"""Tests for agent types and models."""

import pytest
from pydantic import ValidationError

from claude_code_setup.plugins.agents.types import (
    AgentCapability,
    AgentContext,
    AgentDefinition,
    AgentMessage,
    AgentResponse,
    AgentStatus,
)


class TestAgentTypes:
    """Test agent type definitions."""
    
    def test_agent_capability_enum(self):
        """Test AgentCapability enum values."""
        assert AgentCapability.CODE_REVIEW.value == "code_review"
        assert AgentCapability.CODE_GENERATION.value == "code_generation"
        assert AgentCapability.DOCUMENTATION.value == "documentation"
        assert AgentCapability.TESTING.value == "testing"
        assert AgentCapability.REFACTORING.value == "refactoring"
        assert AgentCapability.SECURITY_ANALYSIS.value == "security_analysis"
        assert AgentCapability.PERFORMANCE_ANALYSIS.value == "performance_analysis"
        assert AgentCapability.DEPENDENCY_ANALYSIS.value == "dependency_analysis"
        assert AgentCapability.ARCHITECTURE_REVIEW.value == "architecture_review"
        assert AgentCapability.GENERAL.value == "general"
    
    def test_agent_status_enum(self):
        """Test AgentStatus enum values."""
        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.INITIALIZING.value == "initializing"
        assert AgentStatus.READY.value == "ready"
        assert AgentStatus.RUNNING.value == "running"
        assert AgentStatus.PAUSED.value == "paused"
        assert AgentStatus.COMPLETED.value == "completed"
        assert AgentStatus.FAILED.value == "failed"
        assert AgentStatus.CANCELLED.value == "cancelled"
    
    def test_agent_context_creation(self):
        """Test AgentContext creation."""
        context = AgentContext(project_path="/test")
        assert context.current_file is None
        assert context.project_path == "/test"
        assert context.selected_text is None
        assert context.variables == {}
        assert context.history == []
        assert context.tools_available == []
        
        # With values
        context = AgentContext(
            project_path="/path",
            current_file="/path/to/file.py",
            selected_text="def foo():",
            variables={"USER": "test"},
            history=[AgentMessage(role="user", content="Hello")],
            tools_available=["Read", "Write"]
        )
        assert context.current_file == "/path/to/file.py"
        assert context.project_path == "/path"
        assert context.selected_text == "def foo():"
        assert context.variables == {"USER": "test"}
        assert len(context.history) == 1
        assert context.tools_available == ["Read", "Write"]
    
    def test_agent_message_creation(self):
        """Test AgentMessage creation."""
        msg = AgentMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.metadata == {}
        
        msg = AgentMessage(
            role="assistant",
            content="Hi there",
            metadata={"source": "agent"}
        )
        assert msg.role == "assistant"
        assert msg.content == "Hi there"
        assert msg.metadata == {"source": "agent"}
    
    def test_agent_definition_creation(self):
        """Test AgentDefinition creation."""
        agent = AgentDefinition(
            name="test-agent",
            display_name="Test Agent",
            description="A test agent",
            capabilities=[AgentCapability.CODE_REVIEW],
            entry_point="test_agent.py"
        )
        assert agent.name == "test-agent"
        assert agent.display_name == "Test Agent"
        assert agent.description == "A test agent"
        assert agent.capabilities == [AgentCapability.CODE_REVIEW]
        assert agent.entry_point == "test_agent.py"
        assert agent.system_prompt is None
        assert agent.max_iterations == 10
        assert agent.timeout_seconds == 300
        assert agent.config_schema is None
        assert agent.examples == []
        assert agent.examples == []
    
    def test_agent_definition_with_all_fields(self):
        """Test AgentDefinition with all fields."""
        agent = AgentDefinition(
            name="complex-agent",
            display_name="Complex Agent",
            description="A complex test agent",
            capabilities=[
                AgentCapability.CODE_REVIEW,
                AgentCapability.REFACTORING
            ],
            entry_point="complex_agent",
            system_prompt="You are a code expert",
            max_iterations=5,
            timeout_seconds=120,
            config_schema={
                "type": "object",
                "properties": {
                    "level": {"type": "string"}
                }
            },
            examples=[
                {
                    "description": "Review code",
                    "command": "agent run complex-agent"
                }
            ]
        )
        assert agent.name == "complex-agent"
        assert agent.system_prompt == "You are a code expert"
        assert agent.max_iterations == 5
        assert agent.timeout_seconds == 120
        assert agent.config_schema["type"] == "object"
        assert len(agent.examples) == 1
        assert agent.examples[0]["command"] == "agent run complex-agent"
    
    def test_agent_definition_validation(self):
        """Test AgentDefinition validation."""
        # Missing required fields
        with pytest.raises(ValidationError):
            AgentDefinition()
        
        # Empty name
        with pytest.raises(ValidationError):
            AgentDefinition(
                name="",
                display_name="Test",
                capabilities=[],
                entry_point="test.py"
            )
        
        # Invalid max_iterations
        with pytest.raises(ValidationError):
            AgentDefinition(
                name="test",
                display_name="Test",
                capabilities=[],
                entry_point="test.py",
                max_iterations=0
            )
        
        # Invalid timeout
        with pytest.raises(ValidationError):
            AgentDefinition(
                name="test",
                display_name="Test",
                capabilities=[],
                entry_point="test.py",
                timeout_seconds=-1
            )
    
    def test_agent_response_creation(self):
        """Test AgentResponse creation."""
        response = AgentResponse(status=AgentStatus.INITIALIZING)
        assert response.status == AgentStatus.INITIALIZING
        assert response.messages == []
        assert response.errors == []
        assert response.results == {}
        assert response.metadata == {}
        assert response.artifacts == {}
        assert response.duration_seconds is None
        
        # With values
        response = AgentResponse(
            status=AgentStatus.COMPLETED,
            messages=[
                AgentMessage(role="assistant", content="Done")
            ],
            results={"output": "success"},
            artifacts={"report.txt": "Generated report content"},
            duration_seconds=1.5
        )
        assert response.status == AgentStatus.COMPLETED
        assert len(response.messages) == 1
        assert response.results["output"] == "success"
        assert response.artifacts["report.txt"] == "Generated report content"
        assert response.duration_seconds == 1.5
    
    def test_agent_response_with_errors(self):
        """Test AgentResponse with errors."""
        response = AgentResponse(
            status=AgentStatus.FAILED,
            errors=["Error 1", "Error 2"]
        )
        assert response.status == AgentStatus.FAILED
        assert len(response.errors) == 2
        assert "Error 1" in response.errors
        assert "Error 2" in response.errors