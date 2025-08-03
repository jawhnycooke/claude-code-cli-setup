"""Plugin-aware agent loader.

This module extends the agent loading functionality to include agents
provided by activated plugins.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional

from ..plugins.registry import PluginRegistry
from ..plugins.types import PluginStatus
from ..plugins.agents.types import AgentDefinition, AgentCapability
from ..plugins.agents.registry import AgentRegistry
from ..utils.logger import debug, warning, info, error


def load_plugin_agents(plugin_dir: Path) -> Dict[str, AgentDefinition]:
    """Load agents from a plugin directory.
    
    Args:
        plugin_dir: Path to the plugin directory
        
    Returns:
        Dictionary of agents by name
    """
    agents = {}
    agents_dir = plugin_dir / "agents"
    
    if not agents_dir.exists():
        return agents
    
    # Look for agents.yaml manifest
    manifest_file = agents_dir / "agents.yaml"
    if manifest_file.exists():
        try:
            with open(manifest_file, 'r') as f:
                manifest = yaml.safe_load(f)
            
            if isinstance(manifest, dict) and 'agents' in manifest:
                for agent_data in manifest['agents']:
                    try:
                        agent = AgentDefinition.model_validate(agent_data)
                        agents[agent.name] = agent
                        debug(f"Loaded agent: {agent.name}")
                    except Exception as e:
                        warning(f"Failed to load agent: {e}")
        except Exception as e:
            error(f"Failed to load agents manifest: {e}")
    
    # Also look for individual agent files
    for agent_file in agents_dir.glob("*.yaml"):
        if agent_file.name == "agents.yaml":
            continue
        
        try:
            with open(agent_file, 'r') as f:
                agent_data = yaml.safe_load(f)
            
            # Convert capability strings to enums
            if 'capabilities' in agent_data:
                agent_data['capabilities'] = [
                    AgentCapability(cap) if isinstance(cap, str) else cap
                    for cap in agent_data['capabilities']
                ]
            
            agent = AgentDefinition.model_validate(agent_data)
            agents[agent.name] = agent
            debug(f"Loaded agent: {agent.name} from {agent_file.name}")
        except Exception as e:
            warning(f"Failed to load agent from {agent_file}: {e}")
    
    return agents


def register_plugin_agents(
    plugin_registry: PluginRegistry,
    agent_registry: AgentRegistry
) -> int:
    """Register agents from all active plugins.
    
    Args:
        plugin_registry: Plugin registry
        agent_registry: Agent registry
        
    Returns:
        Number of agents registered
    """
    count = 0
    active_plugins = plugin_registry.get_active_plugins()
    
    for plugin_name, plugin in active_plugins.items():
        if not plugin.install_path:
            continue
            
        plugin_dir = Path(plugin.install_path)
        if not plugin_dir.exists():
            warning(f"Plugin directory not found: {plugin_dir}")
            continue
        
        # Check if plugin provides agents
        if not plugin.manifest.provides.agents:
            continue
        
        debug(f"Loading agents from plugin: {plugin_name}")
        plugin_agents = load_plugin_agents(plugin_dir)
        
        # Register agents
        for agent_name, agent in plugin_agents.items():
            agent_registry.register_agent(plugin_name, agent)
            count += 1
            info(f"Registered agent: {plugin_name}/{agent_name}")
    
    return count


def validate_agent_definition(agent: AgentDefinition, plugin_dir: Path) -> List[str]:
    """Validate an agent definition.
    
    Args:
        agent: Agent definition to validate
        plugin_dir: Plugin directory
        
    Returns:
        List of validation errors
    """
    errors = []
    
    # Check entry point exists
    if agent.entry_point.endswith('.py'):
        script_path = plugin_dir / "agents" / agent.entry_point
        if not script_path.exists():
            errors.append(f"Agent script not found: {agent.entry_point}")
        elif not script_path.is_file():
            errors.append(f"Agent entry point is not a file: {agent.entry_point}")
    else:
        # Module path
        module_path = agent.entry_point.replace('.', '/') + '.py'
        if module_path.startswith('/'):
            module_path = module_path[1:]
        full_path = plugin_dir / "agents" / module_path
        if not full_path.exists():
            errors.append(f"Agent module not found: {agent.entry_point}")
    
    # Validate capabilities
    for cap in agent.capabilities:
        if not isinstance(cap, AgentCapability):
            errors.append(f"Invalid capability: {cap}")
    
    # Validate configuration
    if agent.max_iterations < 1:
        errors.append("max_iterations must be at least 1")
    
    if agent.timeout_seconds < 1:
        errors.append("timeout_seconds must be at least 1")
    
    return errors


def get_agent_by_key(
    agent_key: str,
    plugin_registry: PluginRegistry,
    agent_registry: AgentRegistry
) -> Optional[AgentDefinition]:
    """Get an agent by its key (plugin/agent format).
    
    Args:
        agent_key: Agent key
        plugin_registry: Plugin registry
        agent_registry: Agent registry
        
    Returns:
        Agent definition if found
    """
    if '/' not in agent_key:
        return None
    
    plugin_name, agent_name = agent_key.split('/', 1)
    
    # Check if plugin is active
    plugin = plugin_registry.get_plugin(plugin_name)
    if not plugin or not plugin.is_active:
        return None
    
    return agent_registry.get_agent(plugin_name, agent_name)