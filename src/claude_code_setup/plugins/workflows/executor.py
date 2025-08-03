"""Workflow executor implementation."""

import asyncio
import json
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ...exceptions import ClaudeSetupError
from ...utils.logger import debug, error, info, warning
from ...utils.template import get_template_sync
from ..agents.executor import AgentExecutor
from ..agents.registry import AgentRegistry
from ..agents.types import AgentContext, AgentStatus
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


class WorkflowExecutionError(ClaudeSetupError):
    """Workflow execution specific errors."""
    pass


class StepExecutor:
    """Executes individual workflow steps."""
    
    def __init__(
        self,
        workflow_def: WorkflowDefinition,
        context: WorkflowContext,
        plugin_path: Path,
        agent_registry: Optional[AgentRegistry] = None
    ) -> None:
        """Initialize step executor.
        
        Args:
            workflow_def: Workflow definition
            context: Workflow context
            plugin_path: Path to plugin directory
            agent_registry: Optional agent registry
        """
        self.workflow_def = workflow_def
        self.context = context
        self.plugin_path = plugin_path
        self.agent_registry = agent_registry
    
    async def execute_step(self, step: WorkflowStep) -> StepResult:
        """Execute a single workflow step.
        
        Args:
            step: Step to execute
            
        Returns:
            Step execution result
        """
        start_time = datetime.now()
        result = StepResult(
            step_id=step.id,
            status=WorkflowStatus.RUNNING,
            started_at=start_time
        )
        
        try:
            # Check condition
            if step.condition and not self._evaluate_condition(step.condition):
                result.status = WorkflowStatus.SKIPPED
                result.logs.append(f"Step skipped due to condition")
                return result
            
            # Execute based on type
            if step.type == StepType.TEMPLATE:
                await self._execute_template_step(step, result)
            elif step.type == StepType.HOOK:
                await self._execute_hook_step(step, result)
            elif step.type == StepType.AGENT:
                await self._execute_agent_step(step, result)
            elif step.type == StepType.COMMAND:
                await self._execute_command_step(step, result)
            elif step.type == StepType.CONDITIONAL:
                await self._execute_conditional_step(step, result)
            elif step.type == StepType.LOOP:
                await self._execute_loop_step(step, result)
            elif step.type == StepType.PARALLEL:
                await self._execute_parallel_step(step, result)
            elif step.type == StepType.SEQUENTIAL:
                await self._execute_sequential_step(step, result)
            else:
                raise WorkflowExecutionError(f"Unknown step type: {step.type}")
            
            # Update context with outputs
            for key, value in result.outputs.items():
                if key in step.outputs:
                    context_key = step.outputs[key]
                    self.context.variables[context_key] = value
            
            result.status = WorkflowStatus.COMPLETED
            
        except Exception as e:
            result.status = WorkflowStatus.FAILED
            result.error = str(e)
            result.error_details = {
                "type": type(e).__name__,
                "message": str(e)
            }
            error(f"Step {step.id} failed: {e}")
        finally:
            result.completed_at = datetime.now()
            result.duration_seconds = (
                result.completed_at - start_time
            ).total_seconds()
        
        return result
    
    def _evaluate_condition(self, condition: StepCondition) -> bool:
        """Evaluate a step condition.
        
        Args:
            condition: Condition to evaluate
            
        Returns:
            True if condition passes
        """
        try:
            # Get field value from context
            field_value = self._get_context_value(condition.field)
            
            # Evaluate based on type
            if condition.type == "equals":
                result = field_value == condition.value
            elif condition.type == "not_equals":
                result = field_value != condition.value
            elif condition.type == "contains":
                result = condition.value in str(field_value)
            elif condition.type == "exists":
                result = field_value is not None
            elif condition.type == "not_exists":
                result = field_value is None
            elif condition.type == "greater_than":
                result = float(field_value) > float(condition.value)
            elif condition.type == "less_than":
                result = float(field_value) < float(condition.value)
            else:
                warning(f"Unknown condition type: {condition.type}")
                result = False
            
            # Handle compound conditions
            if condition.conditions:
                sub_results = [
                    self._evaluate_condition(c)
                    for c in condition.conditions
                ]
                
                if condition.operator == "and":
                    result = result and all(sub_results)
                elif condition.operator == "or":
                    result = result or any(sub_results)
                elif condition.operator == "not":
                    result = not result
            
            return result
            
        except Exception as e:
            warning(f"Condition evaluation failed: {e}")
            return False
    
    def _get_context_value(self, path: str) -> Any:
        """Get value from context using dot notation.
        
        Args:
            path: Dot-separated path (e.g., "variables.foo.bar")
            
        Returns:
            Value from context
        """
        parts = path.split(".")
        value = self.context.model_dump()
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        
        return value
    
    def _resolve_inputs(self, inputs: Dict[str, str]) -> Dict[str, Any]:
        """Resolve step inputs from context.
        
        Args:
            inputs: Input mappings
            
        Returns:
            Resolved input values
        """
        resolved = {}
        for key, path in inputs.items():
            resolved[key] = self._get_context_value(path)
        return resolved
    
    async def _execute_template_step(
        self,
        step: WorkflowStep,
        result: StepResult
    ) -> None:
        """Execute template step."""
        if not step.template:
            raise WorkflowExecutionError("Template step missing template name")
        
        # Get template
        template = get_template_sync(step.template)
        if not template:
            raise WorkflowExecutionError(f"Template not found: {step.template}")
        
        # Resolve inputs
        inputs = self._resolve_inputs(step.inputs)
        
        # Apply template (simplified - would integrate with template system)
        result.outputs["template"] = step.template
        result.outputs["applied"] = True
        result.logs.append(f"Applied template: {step.template}")
    
    async def _execute_hook_step(
        self,
        step: WorkflowStep,
        result: StepResult
    ) -> None:
        """Execute hook step."""
        if not step.hook:
            raise WorkflowExecutionError("Hook step missing hook name")
        
        # Resolve inputs
        inputs = self._resolve_inputs(step.inputs)
        
        # Trigger hook (simplified - would integrate with hook system)
        result.outputs["hook"] = step.hook
        result.outputs["triggered"] = True
        result.logs.append(f"Triggered hook: {step.hook}")
    
    async def _execute_agent_step(
        self,
        step: WorkflowStep,
        result: StepResult
    ) -> None:
        """Execute agent step."""
        if not step.agent:
            raise WorkflowExecutionError("Agent step missing agent name")
        
        if not self.agent_registry:
            raise WorkflowExecutionError("Agent registry not available")
        
        # Parse agent key
        if "/" not in step.agent:
            raise WorkflowExecutionError(f"Invalid agent key: {step.agent}")
        
        plugin_name, agent_name = step.agent.split("/", 1)
        
        # Get agent
        agent_def = self.agent_registry.get_agent(plugin_name, agent_name)
        if not agent_def:
            raise WorkflowExecutionError(f"Agent not found: {step.agent}")
        
        # Prepare context
        agent_context = AgentContext(
            project_path=self.context.project_path,
            variables=self._resolve_inputs(step.inputs)
        )
        
        # Execute agent
        executor = AgentExecutor(agent_def, self.plugin_path)
        agent_result = await executor.execute(
            agent_context,
            step.config
        )
        
        # Process results
        if agent_result.status == AgentStatus.COMPLETED:
            result.outputs.update(agent_result.results)
            result.artifacts.update(agent_result.artifacts)
            result.logs.extend([
                f"Agent {step.agent}: {msg.content}"
                for msg in agent_result.messages
            ])
        else:
            raise WorkflowExecutionError(
                f"Agent failed: {', '.join(agent_result.errors)}"
            )
    
    async def _execute_command_step(
        self,
        step: WorkflowStep,
        result: StepResult
    ) -> None:
        """Execute command step."""
        if not step.command:
            raise WorkflowExecutionError("Command step missing command")
        
        # Resolve inputs as environment variables
        env_vars = self._resolve_inputs(step.inputs)
        env = {**subprocess.os.environ, **{k: str(v) for k, v in env_vars.items()}}
        
        # Execute command
        timeout = step.timeout_seconds or 300
        process = await asyncio.create_subprocess_shell(
            step.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=self.context.project_path
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            if process.returncode == 0:
                result.outputs["stdout"] = stdout.decode()
                result.outputs["stderr"] = stderr.decode()
                result.outputs["returncode"] = process.returncode
                result.logs.append(f"Command completed: {step.command}")
            else:
                raise WorkflowExecutionError(
                    f"Command failed with code {process.returncode}: {stderr.decode()}"
                )
                
        except asyncio.TimeoutError:
            process.terminate()
            await process.wait()
            raise WorkflowExecutionError(f"Command timed out after {timeout}s")
    
    async def _execute_conditional_step(
        self,
        step: WorkflowStep,
        result: StepResult
    ) -> None:
        """Execute conditional step."""
        if not step.steps or len(step.steps) < 2:
            raise WorkflowExecutionError(
                "Conditional step requires at least 2 child steps"
            )
        
        # First step is condition, rest are branches
        condition_step = step.steps[0]
        condition_result = await self.execute_step(condition_step)
        
        # Check condition result
        if condition_result.status == WorkflowStatus.COMPLETED:
            # Execute success branch
            if len(step.steps) > 1:
                branch_result = await self.execute_step(step.steps[1])
                result.outputs.update(branch_result.outputs)
                result.artifacts.update(branch_result.artifacts)
        else:
            # Execute failure branch if exists
            if len(step.steps) > 2:
                branch_result = await self.execute_step(step.steps[2])
                result.outputs.update(branch_result.outputs)
                result.artifacts.update(branch_result.artifacts)
    
    async def _execute_loop_step(
        self,
        step: WorkflowStep,
        result: StepResult
    ) -> None:
        """Execute loop step."""
        if not step.steps:
            raise WorkflowExecutionError("Loop step missing child steps")
        
        # Get loop items
        if isinstance(step.loop_items, str):
            items = self._get_context_value(step.loop_items) or []
        else:
            items = step.loop_items or []
        
        # Execute for each item
        loop_outputs = []
        for i, item in enumerate(items):
            # Set loop variable
            if step.loop_variable:
                self.context.variables[step.loop_variable] = item
                self.context.variables[f"{step.loop_variable}_index"] = i
            
            # Execute child steps
            for child_step in step.steps:
                child_result = await self.execute_step(child_step)
                if child_result.status == WorkflowStatus.FAILED:
                    result.status = WorkflowStatus.FAILED
                    result.error = f"Loop iteration {i} failed"
                    return
                
                loop_outputs.append(child_result.outputs)
        
        result.outputs["iterations"] = len(items)
        result.outputs["results"] = loop_outputs
    
    async def _execute_parallel_step(
        self,
        step: WorkflowStep,
        result: StepResult
    ) -> None:
        """Execute parallel step."""
        if not step.steps:
            raise WorkflowExecutionError("Parallel step missing child steps")
        
        # Execute all steps in parallel
        tasks = [
            self.execute_step(child_step)
            for child_step in step.steps
        ]
        
        child_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        all_outputs = {}
        all_artifacts = {}
        failures = []
        
        for i, child_result in enumerate(child_results):
            if isinstance(child_result, Exception):
                failures.append(str(child_result))
            elif child_result.status == WorkflowStatus.FAILED:
                failures.append(child_result.error or "Unknown error")
            else:
                all_outputs.update(child_result.outputs)
                all_artifacts.update(child_result.artifacts)
        
        if failures:
            result.status = WorkflowStatus.FAILED
            result.error = f"Parallel execution failed: {', '.join(failures)}"
        else:
            result.outputs.update(all_outputs)
            result.artifacts.update(all_artifacts)
    
    async def _execute_sequential_step(
        self,
        step: WorkflowStep,
        result: StepResult
    ) -> None:
        """Execute sequential step."""
        if not step.steps:
            raise WorkflowExecutionError("Sequential step missing child steps")
        
        # Execute steps in sequence
        for child_step in step.steps:
            child_result = await self.execute_step(child_step)
            
            if child_result.status == WorkflowStatus.FAILED:
                result.status = WorkflowStatus.FAILED
                result.error = f"Step {child_step.id} failed"
                return
            
            result.outputs.update(child_result.outputs)
            result.artifacts.update(child_result.artifacts)


class WorkflowExecutor:
    """Executes complete workflows."""
    
    def __init__(
        self,
        workflow_def: WorkflowDefinition,
        plugin_path: Path,
        agent_registry: Optional[AgentRegistry] = None
    ) -> None:
        """Initialize workflow executor.
        
        Args:
            workflow_def: Workflow definition
            plugin_path: Path to plugin directory
            agent_registry: Optional agent registry
        """
        self.workflow_def = workflow_def
        self.plugin_path = plugin_path
        self.agent_registry = agent_registry
        self._cancelled = False
    
    async def execute(
        self,
        project_path: str,
        config: Optional[Dict[str, Any]] = None,
        initial_variables: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """Execute the workflow.
        
        Args:
            project_path: Project path
            config: Workflow configuration
            initial_variables: Initial context variables
            
        Returns:
            Workflow execution result
        """
        # Initialize context
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            workflow_name=self.workflow_def.name,
            project_path=project_path,
            config=config or self.workflow_def.default_config,
            variables=initial_variables or {},
            started_at=datetime.now()
        )
        
        # Initialize result
        result = WorkflowResult(
            workflow_id=context.workflow_id,
            workflow_name=self.workflow_def.name,
            status=WorkflowStatus.RUNNING,
            started_at=context.started_at,
            total_steps=len(self.workflow_def.steps)
        )
        
        # Create step executor
        step_executor = StepExecutor(
            self.workflow_def,
            context,
            self.plugin_path,
            self.agent_registry
        )
        
        try:
            # Build step index
            step_index = {
                step.id: step
                for step in self.workflow_def.steps
            }
            
            # Execute workflow
            visited_steps: Set[str] = set()
            current_step_id = self.workflow_def.entry_point
            
            while current_step_id and not self._cancelled:
                # Check for cycles
                if current_step_id in visited_steps:
                    raise WorkflowExecutionError(
                        f"Workflow cycle detected at step: {current_step_id}"
                    )
                
                visited_steps.add(current_step_id)
                
                # Get step
                if current_step_id not in step_index:
                    raise WorkflowExecutionError(
                        f"Step not found: {current_step_id}"
                    )
                
                step = step_index[current_step_id]
                context.current_step = current_step_id
                
                # Execute step with retries
                step_result = None
                for attempt in range(step.retry_count + 1):
                    if attempt > 0:
                        info(f"Retrying step {step.id} (attempt {attempt + 1})")
                    
                    step_result = await step_executor.execute_step(step)
                    result.step_results[step.id] = step_result
                    
                    if step_result.status != WorkflowStatus.FAILED:
                        break
                    
                    if attempt < step.retry_count:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
                # Update counters
                if step_result.status == WorkflowStatus.COMPLETED:
                    result.completed_steps += 1
                    context.completed_steps.append(step.id)
                elif step_result.status == WorkflowStatus.FAILED:
                    result.failed_steps += 1
                    context.failed_steps.append(step.id)
                    result.errors.append(step_result.error or "Unknown error")
                elif step_result.status == WorkflowStatus.SKIPPED:
                    result.skipped_steps += 1
                
                # Determine next step
                if step_result.status == WorkflowStatus.COMPLETED and step.on_success:
                    current_step_id = step.on_success
                elif step_result.status == WorkflowStatus.FAILED and step.on_failure:
                    current_step_id = step.on_failure
                else:
                    # No explicit next step, workflow ends
                    current_step_id = None
            
            # Set final status
            if self._cancelled:
                result.status = WorkflowStatus.CANCELLED
            elif result.failed_steps > 0:
                result.status = WorkflowStatus.FAILED
            else:
                result.status = WorkflowStatus.COMPLETED
            
            # Collect final outputs and artifacts
            for step_result in result.step_results.values():
                result.outputs.update(step_result.outputs)
                result.artifacts.update(step_result.artifacts)
            
        except Exception as e:
            result.status = WorkflowStatus.FAILED
            result.errors.append(str(e))
            error(f"Workflow execution failed: {e}")
        finally:
            result.completed_at = datetime.now()
            result.duration_seconds = (
                result.completed_at - result.started_at
            ).total_seconds()
            result.final_context = context
        
        return result
    
    def cancel(self) -> None:
        """Cancel workflow execution."""
        self._cancelled = True
        info(f"Workflow {self.workflow_def.name} cancelled")