"""Tests for plugin agent loader."""

import pytest
import yaml
from pathlib import Path

from claude_code_setup.utils.plugin_agent_loader import (
    load_plugin_agents,
    register_plugin_agents,
    validate_agent_definition,
    get_agent_by_key,
)
from claude_code_setup.plugins.agents.types import AgentDefinition, AgentCapability
from claude_code_setup.plugins.agents.registry import AgentRegistry
from claude_code_setup.plugins.registry import PluginRegistry
from claude_code_setup.plugins.types import PluginManifest, PluginCapabilities, Plugin, PluginStatus


class TestPluginAgentLoader:
    """Test plugin agent loader functionality."""
    
    @pytest.fixture
    def plugin_dir(self, tmp_path):
        """Create test plugin directory."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        agents_dir = plugin_dir / "agents"
        agents_dir.mkdir()
        return plugin_dir
    
    @pytest.fixture
    def agent_registry(self):
        """Create agent registry."""
        return AgentRegistry()
    
    @pytest.fixture
    def plugin_registry(self, tmp_path):
        """Create plugin registry."""
        registry_path = tmp_path / "registry.json"
        return PluginRegistry(registry_path=registry_path)
    
    def test_load_plugin_agents_from_manifest(self, plugin_dir):
        """Test loading agents from agents.yaml manifest."""
        # Create agents.yaml
        manifest_file = plugin_dir / "agents" / "agents.yaml"
        manifest_content = {
            "agents": [
                {
                    "name": "agent1",
                    "display_name": "Agent 1",
                    "description": "First agent",
                    "capabilities": ["code_review"],
                    "entry_point": "agent1.py"
                },
                {
                    "name": "agent2",
                    "display_name": "Agent 2",
                    "description": "Second agent",
                    "capabilities": ["testing", "documentation"],
                    "entry_point": "agent2_module",
                    "max_iterations": 5,
                    "timeout_seconds": 120
                }
            ]
        }
        manifest_file.write_text(yaml.dump(manifest_content))
        
        # Load agents
        agents = load_plugin_agents(plugin_dir)
        
        assert len(agents) == 2
        assert "agent1" in agents
        assert "agent2" in agents
        
        # Check agent1
        agent1 = agents["agent1"]
        assert agent1.display_name == "Agent 1"
        assert agent1.capabilities == [AgentCapability.CODE_REVIEW]
        assert agent1.entry_point == "agent1.py"
        assert agent1.max_iterations == 10  # default
        
        # Check agent2
        agent2 = agents["agent2"]
        assert agent2.display_name == "Agent 2"
        assert len(agent2.capabilities) == 2
        assert AgentCapability.TESTING in agent2.capabilities
        assert AgentCapability.DOCUMENTATION in agent2.capabilities
        assert agent2.max_iterations == 5
        assert agent2.timeout_seconds == 120
    
    def test_load_plugin_agents_individual_files(self, plugin_dir):
        """Test loading agents from individual YAML files."""
        # Create individual agent files
        agent1_file = plugin_dir / "agents" / "reviewer.yaml"
        agent1_content = {
            "name": "reviewer",
            "display_name": "Code Reviewer",
            "description": "Reviews code",
            "capabilities": ["code_review"],
            "entry_point": "reviewer.py",
            "system_prompt": "You are a code review expert"
        }
        agent1_file.write_text(yaml.dump(agent1_content))
        
        agent2_file = plugin_dir / "agents" / "tester.yaml"
        agent2_content = {
            "name": "tester",
            "display_name": "Test Generator",
            "description": "Generates tests",
            "capabilities": ["testing"],
            "entry_point": "tester"
        }
        agent2_file.write_text(yaml.dump(agent2_content))
        
        # Load agents
        agents = load_plugin_agents(plugin_dir)
        
        assert len(agents) == 2
        assert "reviewer" in agents
        assert "tester" in agents
        
        # Check system prompt loaded
        assert agents["reviewer"].system_prompt == "You are a code review expert"
    
    def test_load_plugin_agents_no_agents_dir(self, plugin_dir):
        """Test loading when agents directory doesn't exist."""
        # Remove agents dir
        (plugin_dir / "agents").rmdir()
        
        agents = load_plugin_agents(plugin_dir)
        assert agents == {}
    
    def test_load_plugin_agents_invalid_manifest(self, plugin_dir):
        """Test loading with invalid manifest."""
        # Create invalid manifest
        manifest_file = plugin_dir / "agents" / "agents.yaml"
        manifest_file.write_text("invalid: yaml: content:")
        
        # Should not crash, just return empty
        agents = load_plugin_agents(plugin_dir)
        assert agents == {}
    
    def test_load_plugin_agents_invalid_agent_def(self, plugin_dir):
        """Test loading with invalid agent definition."""
        # Create manifest with invalid agent
        manifest_file = plugin_dir / "agents" / "agents.yaml"
        manifest_content = {
            "agents": [
                {
                    "name": "valid",
                    "display_name": "Valid Agent",
                    "description": "Valid agent",
                    "capabilities": ["general"],
                    "entry_point": "valid.py"
                },
                {
                    # Missing required fields
                    "name": "invalid",
                    "display_name": "Invalid"
                }
            ]
        }
        manifest_file.write_text(yaml.dump(manifest_content))
        
        # Should load valid agent, skip invalid
        agents = load_plugin_agents(plugin_dir)
        assert len(agents) == 1
        assert "valid" in agents
        assert "invalid" not in agents
    
    def test_register_plugin_agents(self, plugin_registry, agent_registry, tmp_path):
        """Test registering agents from active plugins."""
        # Create plugin with agents
        plugin_dir = tmp_path / "plugins" / "test-plugin"
        plugin_dir.mkdir(parents=True)
        agents_dir = plugin_dir / "agents"
        agents_dir.mkdir()
        
        # Create agents manifest
        manifest_file = agents_dir / "agents.yaml"
        manifest_content = {
            "agents": [
                {
                    "name": "agent1",
                    "display_name": "Agent 1",
                    "description": "First agent",
                    "capabilities": ["general"],
                    "entry_point": "agent1.py"
                }
            ]
        }
        manifest_file.write_text(yaml.dump(manifest_content))
        
        # Create plugin manifest
        plugin_manifest = PluginManifest(
            metadata={
                "name": "test-plugin",
                "display_name": "Test Plugin",
                "version": "1.0.0",
                "description": "Test plugin",
                "author": "Test Author",
                "category": "development"
            },
            provides=PluginCapabilities(agents=["agent1"])
        )
        
        # Register plugin
        plugin = Plugin(
            name="test-plugin",
            manifest=plugin_manifest,
            install_path=str(plugin_dir),
            status=PluginStatus.ACTIVE
        )
        plugin_registry._plugins["test-plugin"] = plugin
        
        # Register agents
        count = register_plugin_agents(plugin_registry, agent_registry)
        
        assert count == 1
        agent = agent_registry.get_agent("test-plugin", "agent1")
        assert agent is not None
        assert agent.display_name == "Agent 1"
    
    def test_register_plugin_agents_no_active_plugins(self, plugin_registry, agent_registry):
        """Test registering when no active plugins."""
        count = register_plugin_agents(plugin_registry, agent_registry)
        assert count == 0
    
    def test_register_plugin_agents_plugin_not_providing_agents(
        self, plugin_registry, agent_registry, tmp_path
    ):
        """Test registering when plugin doesn't provide agents."""
        # Create plugin without agents
        plugin_manifest = PluginManifest(
            metadata={
                "name": "no-agents",
                "display_name": "No Agents Plugin",
                "version": "1.0.0",
                "description": "Plugin without agents",
                "author": "Test Author",
                "category": "development"
            },
            provides=PluginCapabilities()  # No agents
        )
        
        plugin = Plugin(
            name="no-agents",
            manifest=plugin_manifest,
            install_path=str(tmp_path / "no-agents"),
            status=PluginStatus.ACTIVE
        )
        plugin_registry._plugins["no-agents"] = plugin
        
        # Register agents
        count = register_plugin_agents(plugin_registry, agent_registry)
        assert count == 0
    
    def test_validate_agent_definition_script(self, plugin_dir):
        """Test validating script-based agent."""
        # Create agent script
        script_path = plugin_dir / "agents" / "test.py"
        script_path.write_text("# test script")
        
        agent = AgentDefinition(
            name="test",
            display_name="Test",
            description="Test agent",
            capabilities=[AgentCapability.GENERAL],
            entry_point="test.py"
        )
        
        errors = validate_agent_definition(agent, plugin_dir)
        assert errors == []
        
        # Test with missing script
        agent.entry_point = "missing.py"
        errors = validate_agent_definition(agent, plugin_dir)
        assert len(errors) == 1
        assert "not found" in errors[0]
    
    def test_validate_agent_definition_module(self, plugin_dir):
        """Test validating module-based agent."""
        # Create module structure
        module_path = plugin_dir / "agents" / "test_module.py"
        module_path.write_text("# test module")
        
        agent = AgentDefinition(
            name="test",
            display_name="Test",
            description="Test agent",
            capabilities=[AgentCapability.GENERAL],
            entry_point="test_module"
        )
        
        errors = validate_agent_definition(agent, plugin_dir)
        assert errors == []
        
        # Test with nested module
        nested_dir = plugin_dir / "agents" / "submodule"
        nested_dir.mkdir()
        nested_module = nested_dir / "nested.py"
        nested_module.write_text("# nested module")
        
        agent.entry_point = "submodule.nested"
        errors = validate_agent_definition(agent, plugin_dir)
        assert errors == []
    
    def test_validate_agent_definition_invalid_params(self, plugin_dir):
        """Test validating agent with invalid parameters."""
        agent = AgentDefinition(
            name="test",
            display_name="Test",
            description="Test agent",
            capabilities=[AgentCapability.GENERAL],
            entry_point="test.py",
            max_iterations=0,  # Invalid
            timeout_seconds=-1  # Invalid
        )
        
        errors = validate_agent_definition(agent, plugin_dir)
        assert len(errors) >= 2
        assert any("max_iterations" in err for err in errors)
        assert any("timeout_seconds" in err for err in errors)
    
    def test_get_agent_by_key(self, plugin_registry, agent_registry, tmp_path):
        """Test getting agent by key."""
        # Register test plugin
        plugin_manifest = PluginManifest(
            metadata={
                "name": "test-plugin",
                "display_name": "Test Plugin",
                "version": "1.0.0",
                "description": "Test",
                "author": "Test Author",
                "category": "development"
            }
        )
        plugin = Plugin(
            name="test-plugin",
            manifest=plugin_manifest,
            status=PluginStatus.ACTIVE
        )
        plugin_registry._plugins["test-plugin"] = plugin
        
        # Register agent
        agent = AgentDefinition(
            name="test-agent",
            display_name="Test Agent",
            description="Test agent",
            capabilities=[AgentCapability.GENERAL],
            entry_point="test.py"
        )
        agent_registry.register_agent("test-plugin", agent)
        
        # Get by key
        result = get_agent_by_key("test-plugin/test-agent", plugin_registry, agent_registry)
        assert result is not None
        assert result.name == "test-agent"
        
        # Invalid key format
        result = get_agent_by_key("invalid-key", plugin_registry, agent_registry)
        assert result is None
        
        # Non-existent agent
        result = get_agent_by_key("test-plugin/no-such-agent", plugin_registry, agent_registry)
        assert result is None
        
        # Inactive plugin
        plugin.status = PluginStatus.DISABLED
        result = get_agent_by_key("test-plugin/test-agent", plugin_registry, agent_registry)
        assert result is None