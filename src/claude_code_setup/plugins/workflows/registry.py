"""Workflow registry for managing plugin workflows."""

import threading
from typing import Dict, List, Optional

from ...utils.logger import debug, info, warning
from .types import WorkflowDefinition


class WorkflowRegistry:
    """Registry for managing workflows from plugins."""
    
    def __init__(self) -> None:
        """Initialize workflow registry."""
        self._workflows: Dict[str, Dict[str, WorkflowDefinition]] = {}
        self._lock = threading.RLock()
    
    def register_workflow(
        self,
        plugin_name: str,
        workflow: WorkflowDefinition
    ) -> None:
        """Register a workflow from a plugin.
        
        Args:
            plugin_name: Plugin providing the workflow
            workflow: Workflow definition
        """
        with self._lock:
            if plugin_name not in self._workflows:
                self._workflows[plugin_name] = {}
            
            self._workflows[plugin_name][workflow.name] = workflow
            info(f"Registered workflow: {plugin_name}/{workflow.name}")
    
    def unregister_workflow(
        self,
        plugin_name: str,
        workflow_name: str
    ) -> bool:
        """Unregister a specific workflow.
        
        Args:
            plugin_name: Plugin name
            workflow_name: Workflow name
            
        Returns:
            True if workflow was removed
        """
        with self._lock:
            if plugin_name in self._workflows:
                if workflow_name in self._workflows[plugin_name]:
                    del self._workflows[plugin_name][workflow_name]
                    info(f"Unregistered workflow: {plugin_name}/{workflow_name}")
                    
                    # Clean up empty plugin entry
                    if not self._workflows[plugin_name]:
                        del self._workflows[plugin_name]
                    
                    return True
            
            return False
    
    def unregister_plugin_workflows(self, plugin_name: str) -> int:
        """Remove all workflows from a plugin.
        
        Args:
            plugin_name: Plugin to remove workflows from
            
        Returns:
            Number of workflows removed
        """
        with self._lock:
            if plugin_name not in self._workflows:
                return 0
            
            count = len(self._workflows[plugin_name])
            del self._workflows[plugin_name]
            info(f"Unregistered {count} workflows from plugin: {plugin_name}")
            return count
    
    def get_workflow(
        self,
        plugin_name: str,
        workflow_name: str
    ) -> Optional[WorkflowDefinition]:
        """Get a specific workflow.
        
        Args:
            plugin_name: Plugin name
            workflow_name: Workflow name
            
        Returns:
            Workflow definition or None
        """
        with self._lock:
            if plugin_name in self._workflows:
                return self._workflows[plugin_name].get(workflow_name)
            return None
    
    def get_all_workflows(self) -> Dict[str, WorkflowDefinition]:
        """Get all registered workflows.
        
        Returns:
            Dictionary mapping workflow_key to definition
        """
        with self._lock:
            all_workflows = {}
            for plugin_name, workflows in self._workflows.items():
                for workflow_name, workflow in workflows.items():
                    workflow_key = f"{plugin_name}/{workflow_name}"
                    all_workflows[workflow_key] = workflow
            return all_workflows
    
    def get_workflows_by_tag(self, tag: str) -> List[WorkflowDefinition]:
        """Get workflows with a specific tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of workflows with the tag
        """
        with self._lock:
            matching = []
            for plugin_workflows in self._workflows.values():
                for workflow in plugin_workflows.values():
                    if tag in workflow.tags:
                        matching.append(workflow)
            return matching
    
    def list_workflows(self, plugin_name: Optional[str] = None) -> List[str]:
        """List workflow keys.
        
        Args:
            plugin_name: Plugin to list workflows for (all if None)
            
        Returns:
            List of workflow keys
        """
        with self._lock:
            if plugin_name:
                # List workflows for specific plugin
                if plugin_name not in self._workflows:
                    return []
                return sorted(list(self._workflows[plugin_name].keys()))
            else:
                # List all workflow keys
                workflow_keys = []
                for plugin_name, workflows in self._workflows.items():
                    for workflow_name in workflows:
                        workflow_keys.append(f"{plugin_name}/{workflow_name}")
                return sorted(workflow_keys)
    
    def validate_workflow_requirements(
        self,
        workflow: WorkflowDefinition,
        available_agents: List[str],
        available_hooks: List[str],
        available_templates: List[str]
    ) -> List[str]:
        """Validate workflow requirements are met.
        
        Args:
            workflow: Workflow to validate
            available_agents: Available agent keys
            available_hooks: Available hook names
            available_templates: Available template names
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check required agents
        for agent in workflow.requires_agents:
            if agent not in available_agents:
                errors.append(f"Required agent not found: {agent}")
        
        # Check required hooks
        for hook in workflow.requires_hooks:
            if hook not in available_hooks:
                errors.append(f"Required hook not found: {hook}")
        
        # Check required templates
        for template in workflow.requires_templates:
            if template not in available_templates:
                errors.append(f"Required template not found: {template}")
        
        # Validate step references
        step_ids = {step.id for step in workflow.steps}
        
        for step in workflow.steps:
            # Check on_success reference
            if step.on_success and step.on_success not in step_ids:
                errors.append(
                    f"Step {step.id} references unknown on_success: {step.on_success}"
                )
            
            # Check on_failure reference
            if step.on_failure and step.on_failure not in step_ids:
                errors.append(
                    f"Step {step.id} references unknown on_failure: {step.on_failure}"
                )
        
        # Check entry point
        if workflow.entry_point not in step_ids:
            errors.append(f"Entry point not found: {workflow.entry_point}")
        
        return errors
    
    def search_workflows(
        self,
        query: str,
        tags: Optional[List[str]] = None
    ) -> List[WorkflowDefinition]:
        """Search workflows by query and tags.
        
        Args:
            query: Search query (searches name and description)
            tags: Optional tags to filter by
            
        Returns:
            List of matching workflows
        """
        with self._lock:
            matching = []
            query_lower = query.lower()
            
            for plugin_workflows in self._workflows.values():
                for workflow in plugin_workflows.values():
                    # Check query match
                    if (query_lower in workflow.name.lower() or
                        query_lower in workflow.display_name.lower() or
                        query_lower in workflow.description.lower()):
                        
                        # Check tag match if specified
                        if tags is None or any(tag in workflow.tags for tag in tags):
                            matching.append(workflow)
            
            return matching