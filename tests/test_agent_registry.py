"""Tests for agent registry."""

import pytest
from pathlib import Path

from claude_code_setup.plugins.agents.registry import AgentRegistry
from claude_code_setup.plugins.agents.types import AgentCapability, AgentDefinition


class TestAgentRegistry:
    """Test agent registry functionality."""
    
    @pytest.fixture
    def registry(self):
        """Create a test registry."""
        return AgentRegistry()
    
    @pytest.fixture
    def sample_agent(self):
        """Create a sample agent definition."""
        return AgentDefinition(
            name="test-agent",
            display_name="Test Agent",
            description="A test agent",
            capabilities=[AgentCapability.CODE_REVIEW],
            entry_point="test_agent.py"
        )
    
    def test_register_agent(self, registry, sample_agent):
        """Test registering an agent."""
        registry.register_agent("test-plugin", sample_agent)
        
        # Check agent is registered
        agent = registry.get_agent("test-plugin", "test-agent")
        assert agent is not None
        assert agent.name == "test-agent"
        assert agent.display_name == "Test Agent"
    
    def test_register_duplicate_agent(self, registry, sample_agent):
        """Test registering duplicate agent."""
        registry.register_agent("test-plugin", sample_agent)
        
        # Should not raise, just update
        registry.register_agent("test-plugin", sample_agent)
        
        # Still only one agent
        agents = registry.list_agents("test-plugin")
        assert len(agents) == 1
    
    def test_unregister_agent(self, registry, sample_agent):
        """Test unregistering an agent."""
        registry.register_agent("test-plugin", sample_agent)
        
        # Remove agent
        removed_count = registry.unregister_plugin_agents("test-plugin")
        assert removed_count == 1
        
        # Check agent is gone
        agent = registry.get_agent("test-plugin", "test-agent")
        assert agent is None
    
    def test_unregister_nonexistent_agent(self, registry):
        """Test unregistering non-existent agent."""
        # When plugin doesn't exist
        result = registry.unregister_plugin_agents("no-such-plugin")
        assert result == 0
    
    def test_get_agent(self, registry, sample_agent):
        """Test getting an agent."""
        registry.register_agent("test-plugin", sample_agent)
        
        # Get existing agent
        agent = registry.get_agent("test-plugin", "test-agent")
        assert agent is not None
        assert agent.name == "test-agent"
        
        # Get non-existent agent
        agent = registry.get_agent("test-plugin", "no-such-agent")
        assert agent is None
        
        # Get from non-existent plugin
        agent = registry.get_agent("no-plugin", "test-agent")
        assert agent is None
    
    def test_list_agents(self, registry):
        """Test listing agents."""
        # Empty registry
        agents = registry.list_agents("test-plugin")
        assert agents == []
        
        # Add agents
        agent1 = AgentDefinition(
            name="agent1",
            display_name="Agent 1",
            description="First agent",
            capabilities=[AgentCapability.CODE_REVIEW],
            entry_point="agent1.py"
        )
        agent2 = AgentDefinition(
            name="agent2",
            display_name="Agent 2",
            description="Second agent",
            capabilities=[AgentCapability.TESTING],
            entry_point="agent2.py"
        )
        
        registry.register_agent("test-plugin", agent1)
        registry.register_agent("test-plugin", agent2)
        
        # List agents
        agents = registry.list_agents("test-plugin")
        assert len(agents) == 2
        assert "agent1" in agents
        assert "agent2" in agents
    
    def test_list_all_agents(self, registry):
        """Test listing all agents from all plugins."""
        # Add agents to different plugins
        agent1 = AgentDefinition(
            name="agent1",
            display_name="Agent 1",
            description="First agent",
            capabilities=[AgentCapability.CODE_REVIEW],
            entry_point="agent1.py"
        )
        agent2 = AgentDefinition(
            name="agent2",
            display_name="Agent 2",
            description="Second agent",
            capabilities=[AgentCapability.TESTING],
            entry_point="agent2.py"
        )
        
        registry.register_agent("plugin1", agent1)
        registry.register_agent("plugin2", agent2)
        
        # List all
        all_agents = registry.list_agents()
        assert len(all_agents) == 2
        assert "plugin1/agent1" in all_agents
        assert "plugin2/agent2" in all_agents
    
    def test_unregister_plugin_agents(self, registry):
        """Test unregistering all agents from a plugin."""
        # Add multiple agents
        agent1 = AgentDefinition(
            name="agent1",
            display_name="Agent 1",
            description="First agent",
            capabilities=[AgentCapability.CODE_REVIEW],
            entry_point="agent1.py"
        )
        agent2 = AgentDefinition(
            name="agent2",
            display_name="Agent 2",
            description="Second agent",
            capabilities=[AgentCapability.TESTING],
            entry_point="agent2.py"
        )
        
        registry.register_agent("test-plugin", agent1)
        registry.register_agent("test-plugin", agent2)
        
        # Unregister all
        count = registry.unregister_plugin_agents("test-plugin")
        assert count == 2
        
        # Check all are gone
        agents = registry.list_agents("test-plugin")
        assert agents == []
    
    def test_search_agents_by_capability(self, registry):
        """Test searching agents by capability."""
        # Add agents with different capabilities
        agent1 = AgentDefinition(
            name="reviewer",
            display_name="Code Reviewer",
            description="Reviews code quality",
            capabilities=[AgentCapability.CODE_REVIEW, AgentCapability.DOCUMENTATION],
            entry_point="reviewer.py"
        )
        agent2 = AgentDefinition(
            name="tester",
            display_name="Test Generator",
            description="Generates tests",
            capabilities=[AgentCapability.TESTING],
            entry_point="tester.py"
        )
        agent3 = AgentDefinition(
            name="analyzer",
            display_name="Performance Analyzer",
            description="Analyzes performance",
            capabilities=[AgentCapability.PERFORMANCE_ANALYSIS, AgentCapability.CODE_REVIEW],
            entry_point="analyzer.py"
        )
        
        registry.register_agent("plugin1", agent1)
        registry.register_agent("plugin1", agent2)
        registry.register_agent("plugin2", agent3)
        
        # Search by CODE_REVIEW
        results = registry.get_agents_by_capability(AgentCapability.CODE_REVIEW.value)
        assert len(results) == 2
        agent_names = [a.name for a in results]
        assert "reviewer" in agent_names
        assert "analyzer" in agent_names
        
        # Search by TESTING
        results = registry.get_agents_by_capability(AgentCapability.TESTING.value)
        assert len(results) == 1
        assert results[0].name == "tester"
        
        # Search by DEPENDENCY_ANALYSIS (none)
        results = registry.get_agents_by_capability(AgentCapability.DEPENDENCY_ANALYSIS.value)
        assert results == []
    
    def test_registry_thread_safety(self, registry):
        """Test thread safety of registry operations."""
        import threading
        import time
        
        errors = []
        
        def register_agents(plugin_name, start, count):
            try:
                for i in range(start, start + count):
                    agent = AgentDefinition(
                        name=f"agent{i}",
                        display_name=f"Agent {i}",
                        description=f"Test agent {i}",
                        capabilities=[AgentCapability.GENERAL],
                        entry_point=f"agent{i}.py"
                    )
                    registry.register_agent(plugin_name, agent)
                    time.sleep(0.001)  # Small delay to increase contention
            except Exception as e:
                errors.append(e)
        
        # Create threads
        threads = []
        for i in range(4):
            t = threading.Thread(
                target=register_agents,
                args=(f"plugin{i}", i * 10, 10)
            )
            threads.append(t)
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # Check no errors
        assert errors == []
        
        # Check all agents registered
        all_agents = registry.list_agents()
        assert len(all_agents) == 40