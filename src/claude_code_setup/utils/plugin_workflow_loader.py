"""Plugin-aware workflow loader.

This module extends the workflow loading functionality to include workflows
provided by activated plugins.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional

from ..plugins.registry import PluginRegistry
from ..plugins.types import PluginStatus
from ..plugins.workflows.types import WorkflowDefinition, WorkflowStep, StepType
from ..plugins.workflows.registry import WorkflowRegistry
from ..utils.logger import debug, warning, info, error


def load_plugin_workflows(plugin_dir: Path) -> Dict[str, WorkflowDefinition]:
    """Load workflows from a plugin directory.
    
    Args:
        plugin_dir: Path to the plugin directory
        
    Returns:
        Dictionary of workflows by name
    """
    workflows = {}
    workflows_dir = plugin_dir / "workflows"
    
    if not workflows_dir.exists():
        return workflows
    
    # Look for workflows.yaml manifest
    manifest_file = workflows_dir / "workflows.yaml"
    if manifest_file.exists():
        try:
            with open(manifest_file, 'r') as f:
                manifest = yaml.safe_load(f)
            
            if isinstance(manifest, dict) and 'workflows' in manifest:
                for workflow_data in manifest['workflows']:
                    try:
                        # Convert step types from strings
                        if 'steps' in workflow_data:
                            _convert_step_types(workflow_data['steps'])
                        
                        workflow = WorkflowDefinition.model_validate(workflow_data)
                        workflows[workflow.name] = workflow
                        debug(f"Loaded workflow: {workflow.name}")
                    except Exception as e:
                        warning(f"Failed to load workflow: {e}")
        except Exception as e:
            error(f"Failed to load workflows manifest: {e}")
    
    # Also look for individual workflow files
    for workflow_file in workflows_dir.glob("*.yaml"):
        if workflow_file.name == "workflows.yaml":
            continue
        
        try:
            with open(workflow_file, 'r') as f:
                workflow_data = yaml.safe_load(f)
            
            # Convert step types
            if 'steps' in workflow_data:
                _convert_step_types(workflow_data['steps'])
            
            workflow = WorkflowDefinition.model_validate(workflow_data)
            workflows[workflow.name] = workflow
            debug(f"Loaded workflow: {workflow.name} from {workflow_file.name}")
        except Exception as e:
            warning(f"Failed to load workflow from {workflow_file}: {e}")
    
    return workflows


def _convert_step_types(steps: List[Dict]) -> None:
    """Convert step type strings to StepType enum values.
    
    Args:
        steps: List of step dictionaries to convert in-place
    """
    for step in steps:
        if 'type' in step and isinstance(step['type'], str):
            try:
                step['type'] = StepType(step['type'])
            except ValueError:
                warning(f"Unknown step type: {step['type']}")
        
        # Recursively convert child steps
        if 'steps' in step and isinstance(step['steps'], list):
            _convert_step_types(step['steps'])


def register_plugin_workflows(
    plugin_registry: PluginRegistry,
    workflow_registry: WorkflowRegistry
) -> int:
    """Register workflows from all active plugins.
    
    Args:
        plugin_registry: Plugin registry
        workflow_registry: Workflow registry
        
    Returns:
        Number of workflows registered
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
        
        # Check if plugin provides workflows
        if not plugin.manifest.provides.workflows:
            continue
        
        debug(f"Loading workflows from plugin: {plugin_name}")
        plugin_workflows = load_plugin_workflows(plugin_dir)
        
        # Register workflows
        for workflow_name, workflow in plugin_workflows.items():
            workflow_registry.register_workflow(plugin_name, workflow)
            count += 1
            info(f"Registered workflow: {plugin_name}/{workflow_name}")
    
    return count


def validate_workflow_definition(
    workflow: WorkflowDefinition,
    plugin_dir: Path
) -> List[str]:
    """Validate a workflow definition.
    
    Args:
        workflow: Workflow definition to validate
        plugin_dir: Plugin directory
        
    Returns:
        List of validation errors
    """
    errors = []
    
    # Check that all steps have unique IDs
    step_ids = set()
    duplicate_ids = set()
    
    def check_step_ids(steps: List[WorkflowStep]) -> None:
        for step in steps:
            if step.id in step_ids:
                duplicate_ids.add(step.id)
            step_ids.add(step.id)
            
            # Check child steps
            if step.steps:
                check_step_ids(step.steps)
    
    check_step_ids(workflow.steps)
    
    if duplicate_ids:
        errors.append(f"Duplicate step IDs found: {', '.join(duplicate_ids)}")
    
    # Validate step types and required fields
    def validate_step(step: WorkflowStep, path: str = "") -> None:
        step_path = f"{path}/{step.id}" if path else step.id
        
        if step.type == StepType.TEMPLATE and not step.template:
            errors.append(f"Step {step_path}: Template step missing template field")
        elif step.type == StepType.HOOK and not step.hook:
            errors.append(f"Step {step_path}: Hook step missing hook field")
        elif step.type == StepType.AGENT and not step.agent:
            errors.append(f"Step {step_path}: Agent step missing agent field")
        elif step.type == StepType.COMMAND and not step.command:
            errors.append(f"Step {step_path}: Command step missing command field")
        elif step.type == StepType.LOOP and not step.steps:
            errors.append(f"Step {step_path}: Loop step missing child steps")
        elif step.type in (StepType.PARALLEL, StepType.SEQUENTIAL) and not step.steps:
            errors.append(f"Step {step_path}: {step.type.value} step missing child steps")
        
        # Validate child steps
        if step.steps:
            for child_step in step.steps:
                validate_step(child_step, step_path)
    
    for step in workflow.steps:
        validate_step(step)
    
    # Validate entry point exists
    if workflow.entry_point not in step_ids:
        errors.append(f"Entry point '{workflow.entry_point}' not found in steps")
    
    # Validate step references
    for step in workflow.steps:
        if step.on_success and step.on_success not in step_ids:
            errors.append(f"Step {step.id}: on_success references unknown step '{step.on_success}'")
        if step.on_failure and step.on_failure not in step_ids:
            errors.append(f"Step {step.id}: on_failure references unknown step '{step.on_failure}'")
    
    return errors


def get_workflow_by_key(
    workflow_key: str,
    plugin_registry: PluginRegistry,
    workflow_registry: WorkflowRegistry
) -> Optional[WorkflowDefinition]:
    """Get a workflow by its key (plugin/workflow format).
    
    Args:
        workflow_key: Workflow key
        plugin_registry: Plugin registry
        workflow_registry: Workflow registry
        
    Returns:
        Workflow definition if found
    """
    if '/' not in workflow_key:
        return None
    
    plugin_name, workflow_name = workflow_key.split('/', 1)
    
    # Check if plugin is active
    plugin = plugin_registry.get_plugin(plugin_name)
    if not plugin or not plugin.is_active:
        return None
    
    return workflow_registry.get_workflow(plugin_name, workflow_name)