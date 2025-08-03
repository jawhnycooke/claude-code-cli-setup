"""Agent registry for managing plugin agents."""

import threading
from pathlib import Path
from typing import Dict, List, Optional

from ...exceptions import ClaudeSetupError
from ...utils.logger import debug, error, info, warning
from .types import AgentDefinition


class AgentRegistryError(ClaudeSetupError):
    """Agent registry specific errors."""
    pass


class AgentRegistry:
    """Registry for managing plugin agents."""
    
    def __init__(self) -> None:
        """Initialize agent registry."""
        self._agents: Dict[str, Dict[str, AgentDefinition]] = {}
        self._lock = threading.RLock()
    
    def register_agent(
        self,
        plugin_name: str,
        agent: AgentDefinition
    ) -> None:
        """Register an agent from a plugin.
        
        Args:
            plugin_name: Name of the plugin
            agent: Agent definition
            
        Raises:
            AgentRegistryError: If registration fails
        """
        with self._lock:
            if plugin_name not in self._agents:
                self._agents[plugin_name] = {}
            
            agent_key = f"{plugin_name}/{agent.name}"
            
            if agent.name in self._agents[plugin_name]:
                warning(f"Overwriting agent {agent_key}")
            
            self._agents[plugin_name][agent.name] = agent
            debug(f"Registered agent: {agent_key}")
    
    def unregister_plugin_agents(self, plugin_name: str) -> int:
        """Remove all agents from a plugin.
        
        Args:
            plugin_name: Plugin to remove agents from
            
        Returns:
            Number of agents removed
        """
        with self._lock:
            if plugin_name not in self._agents:
                return 0
            
            count = len(self._agents[plugin_name])
            del self._agents[plugin_name]
            info(f"Unregistered {count} agents from {plugin_name}")
            return count
    
    def get_agent(
        self,
        plugin_name: str,
        agent_name: str
    ) -> Optional[AgentDefinition]:
        """Get a specific agent.
        
        Args:
            plugin_name: Plugin name
            agent_name: Agent name
            
        Returns:
            Agent definition if found
        """
        with self._lock:
            if plugin_name not in self._agents:
                return None
            return self._agents[plugin_name].get(agent_name)
    
    def get_all_agents(self) -> Dict[str, AgentDefinition]:
        """Get all registered agents.
        
        Returns:
            Dictionary mapping agent_key to definition
        """
        with self._lock:
            all_agents = {}
            for plugin_name, agents in self._agents.items():
                for agent_name, agent in agents.items():
                    agent_key = f"{plugin_name}/{agent_name}"
                    all_agents[agent_key] = agent
            return all_agents
    
    def get_agents_by_capability(
        self,
        capability: str
    ) -> List[AgentDefinition]:
        """Get agents with a specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of agents with the capability
        """
        with self._lock:
            matching = []
            for plugin_agents in self._agents.values():
                for agent in plugin_agents.values():
                    if capability in [c.value for c in agent.capabilities]:
                        matching.append(agent)
            return matching
    
    def list_agents(self, plugin_name: Optional[str] = None) -> List[str]:
        """List agent keys.
        
        Args:
            plugin_name: Plugin to list agents for (all if None)
            
        Returns:
            List of agent keys (plugin/agent format if no plugin specified,
            just agent names if plugin specified)
        """
        with self._lock:
            if plugin_name:
                # List agents for specific plugin
                if plugin_name not in self._agents:
                    return []
                return sorted(list(self._agents[plugin_name].keys()))
            else:
                # List all agent keys
                agent_keys = []
                for plugin_name, agents in self._agents.items():
                    for agent_name in agents:
                        agent_keys.append(f"{plugin_name}/{agent_name}")
                return sorted(agent_keys)