"""Tests for agent executor."""

import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from claude_code_setup.plugins.agents.executor import AgentExecutor, AgentExecutionError
from claude_code_setup.plugins.agents.types import (
    AgentContext,
    AgentDefinition,
    AgentResponse,
    AgentStatus,
    AgentCapability,
    AgentMessage,
)


class TestAgentExecutor:
    """Test agent executor functionality."""
    
    @pytest.fixture
    def script_agent(self, tmp_path):
        """Create a script-based agent definition."""
        return AgentDefinition(
            name="script-agent",
            display_name="Script Agent",
            description="A test script agent",
            capabilities=[AgentCapability.CODE_REVIEW],
            entry_point="test_script.py",
            timeout_seconds=5
        )
    
    @pytest.fixture
    def module_agent(self, tmp_path):
        """Create a module-based agent definition."""
        return AgentDefinition(
            name="module-agent",
            display_name="Module Agent",
            description="A test module agent",
            capabilities=[AgentCapability.TESTING],
            entry_point="test_module",
            timeout_seconds=5
        )
    
    @pytest.fixture
    def plugin_path(self, tmp_path):
        """Create a test plugin directory structure."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        agents_dir = plugin_dir / "agents"
        agents_dir.mkdir()
        return plugin_dir
    
    @pytest.fixture
    def context(self):
        """Create a test context."""
        return AgentContext(
            project_path="/test",
            current_file="/test/file.py",
            variables={"USER": "test", "test": True}
        )
    
    @pytest.mark.asyncio
    async def test_execute_script_success(self, script_agent, plugin_path, context):
        """Test successful script execution."""
        # Create test script
        script_path = plugin_path / "agents" / "test_script.py"
        script_content = """
import json
import sys

input_data = json.loads(sys.stdin.read())
response = {
    "status": "completed",
    "messages": [
        {"role": "assistant", "content": "Script executed successfully"}
    ],
    "results": {"processed": True}
}
print(json.dumps(response))
"""
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        
        # Execute
        executor = AgentExecutor(script_agent, plugin_path)
        response = await executor.execute(context, {})
        
        assert response.status == AgentStatus.COMPLETED
        assert len(response.messages) == 1
        assert response.messages[0].content == "Script executed successfully"
        assert response.results["processed"] is True
    
    @pytest.mark.asyncio
    async def test_execute_script_failure(self, script_agent, plugin_path, context):
        """Test script execution failure."""
        # Create failing script
        script_path = plugin_path / "agents" / "test_script.py"
        script_content = """
import sys
sys.exit(1)
"""
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        
        # Execute
        executor = AgentExecutor(script_agent, plugin_path)
        response = await executor.execute(context, {})
        
        assert response.status == AgentStatus.FAILED
        assert len(response.errors) > 0
    
    @pytest.mark.asyncio
    async def test_execute_script_not_found(self, script_agent, plugin_path, context):
        """Test script not found error."""
        # Don't create the script
        
        executor = AgentExecutor(script_agent, plugin_path)
        response = await executor.execute(context, {})
        
        assert response.status == AgentStatus.FAILED
        assert any("not found" in err for err in response.errors)
    
    @pytest.mark.asyncio
    async def test_execute_script_timeout(self, script_agent, plugin_path, context):
        """Test script timeout."""
        # Create slow script
        script_path = plugin_path / "agents" / "test_script.py"
        script_content = """
import time
time.sleep(10)  # Longer than timeout
"""
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        
        # Set short timeout
        script_agent.timeout_seconds = 1
        
        # Execute
        executor = AgentExecutor(script_agent, plugin_path)
        response = await executor.execute(context, {})
        
        assert response.status == AgentStatus.FAILED
        assert any("timed out" in err for err in response.errors)
    
    @pytest.mark.asyncio
    async def test_execute_module_success(self, module_agent, plugin_path, context):
        """Test successful module execution."""
        # Create test module
        module_path = plugin_path / "agents" / "test_module.py"
        module_content = """
from claude_code_setup.plugins.agents.types import AgentResponse, AgentStatus, AgentMessage

async def execute(context, config, stream=False, debug=False):
    response = AgentResponse(
        status=AgentStatus.COMPLETED,
        messages=[
            AgentMessage(role="assistant", content="Module executed successfully")
        ],
        results={"module": True}
    )
    return response
"""
        module_path.write_text(module_content)
        
        # Execute
        executor = AgentExecutor(module_agent, plugin_path)
        response = await executor.execute(context, {})
        
        assert response.status == AgentStatus.COMPLETED
        assert len(response.messages) == 1
        assert response.messages[0].content == "Module executed successfully"
        assert response.results["module"] is True
    
    @pytest.mark.asyncio
    async def test_execute_module_sync_function(self, module_agent, plugin_path, context):
        """Test module with synchronous execute function."""
        # Create test module with sync function
        module_path = plugin_path / "agents" / "test_module.py"
        module_content = """
from claude_code_setup.plugins.agents.types import AgentResponse, AgentStatus, AgentMessage

def execute(context, config, stream=False, debug=False):
    response = AgentResponse(
        status=AgentStatus.COMPLETED,
        messages=[
            AgentMessage(role="assistant", content="Sync function executed")
        ]
    )
    return response
"""
        module_path.write_text(module_content)
        
        # Execute
        executor = AgentExecutor(module_agent, plugin_path)
        response = await executor.execute(context, {})
        
        assert response.status == AgentStatus.COMPLETED
        assert response.messages[0].content == "Sync function executed"
    
    @pytest.mark.asyncio
    async def test_execute_module_dict_return(self, module_agent, plugin_path, context):
        """Test module returning dict instead of AgentResponse."""
        # Create test module returning dict
        module_path = plugin_path / "agents" / "test_module.py"
        module_content = """
async def execute(context, config, stream=False, debug=False):
    return {
        "status": "completed",
        "messages": [
            {"role": "assistant", "content": "Dict response"}
        ]
    }
"""
        module_path.write_text(module_content)
        
        # Execute
        executor = AgentExecutor(module_agent, plugin_path)
        response = await executor.execute(context, {})
        
        assert response.status == AgentStatus.COMPLETED
        assert response.messages[0].content == "Dict response"
    
    @pytest.mark.asyncio
    async def test_execute_module_string_return(self, module_agent, plugin_path, context):
        """Test module returning string."""
        # Create test module returning string
        module_path = plugin_path / "agents" / "test_module.py"
        module_content = """
async def execute(context, config, stream=False, debug=False):
    return "Simple string output"
"""
        module_path.write_text(module_content)
        
        # Execute
        executor = AgentExecutor(module_agent, plugin_path)
        response = await executor.execute(context, {})
        
        assert response.status == AgentStatus.COMPLETED
        assert response.results["output"] == "Simple string output"
    
    @pytest.mark.asyncio
    async def test_execute_module_no_execute_function(self, module_agent, plugin_path, context):
        """Test module without execute function."""
        # Create test module without execute
        module_path = plugin_path / "agents" / "test_module.py"
        module_content = """
def some_other_function():
    pass
"""
        module_path.write_text(module_content)
        
        # Execute
        executor = AgentExecutor(module_agent, plugin_path)
        response = await executor.execute(context, {})
        
        assert response.status == AgentStatus.FAILED
        assert any("execute" in err for err in response.errors)
    
    @pytest.mark.asyncio
    async def test_execute_module_not_found(self, module_agent, plugin_path, context):
        """Test module not found error."""
        # Don't create the module
        
        executor = AgentExecutor(module_agent, plugin_path)
        response = await executor.execute(context, {})
        
        assert response.status == AgentStatus.FAILED
        assert any("not found" in err for err in response.errors)
    
    @pytest.mark.asyncio
    async def test_execute_with_debug_mode(self, script_agent, plugin_path, context):
        """Test execution with debug mode enabled."""
        # Create script with error
        script_path = plugin_path / "agents" / "test_script.py"
        script_content = """
raise Exception("Test error")
"""
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        
        # Execute with debug
        executor = AgentExecutor(script_agent, plugin_path)
        response = await executor.execute(context, {}, debug_mode=True)
        
        assert response.status == AgentStatus.FAILED
        # Should include traceback in debug mode
        assert any("Traceback" in err for err in response.errors)
    
    @pytest.mark.asyncio
    async def test_execute_with_config(self, script_agent, plugin_path, context):
        """Test passing configuration to agent."""
        # Create script that uses config
        script_path = plugin_path / "agents" / "test_script.py"
        script_content = """
import json
import sys

input_data = json.loads(sys.stdin.read())
config = input_data.get("config", {})
response = {
    "status": "completed",
    "results": {"config_value": config.get("test_key", "default")}
}
print(json.dumps(response))
"""
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        
        # Execute with config
        executor = AgentExecutor(script_agent, plugin_path)
        config = {"test_key": "test_value"}
        response = await executor.execute(context, config)
        
        assert response.status == AgentStatus.COMPLETED
        assert response.results["config_value"] == "test_value"
    
    def test_cancel_execution(self, script_agent, plugin_path):
        """Test cancelling agent execution."""
        executor = AgentExecutor(script_agent, plugin_path)
        
        # Mock process
        mock_process = Mock()
        mock_process.poll.return_value = None
        executor._process = mock_process
        
        # Cancel
        executor.cancel()
        
        mock_process.terminate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_duration_tracking(self, script_agent, plugin_path, context):
        """Test execution duration tracking."""
        # Create quick script
        script_path = plugin_path / "agents" / "test_script.py"
        script_content = """
import json
import sys
import time

time.sleep(0.1)
response = {"status": "completed"}
print(json.dumps(response))
"""
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        
        # Execute
        executor = AgentExecutor(script_agent, plugin_path)
        response = await executor.execute(context, {})
        
        assert response.status == AgentStatus.COMPLETED
        assert response.duration_seconds is not None
        assert response.duration_seconds >= 0.1