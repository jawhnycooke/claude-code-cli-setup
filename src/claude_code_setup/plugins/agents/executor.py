"""Agent executor implementation."""

import asyncio
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

from ...exceptions import ClaudeSetupError
from ...utils.logger import debug, error, info, warning
from .types import (
    AgentContext,
    AgentDefinition,
    AgentMessage,
    AgentResponse,
    AgentStatus,
)


class AgentExecutionError(ClaudeSetupError):
    """Agent execution specific errors."""
    pass


class AgentExecutor:
    """Executes plugin agents."""
    
    def __init__(
        self,
        agent_def: AgentDefinition,
        plugin_path: Path
    ) -> None:
        """Initialize agent executor.
        
        Args:
            agent_def: Agent definition
            plugin_path: Path to plugin directory
        """
        self.agent_def = agent_def
        self.plugin_path = plugin_path
        self._process: Optional[subprocess.Popen] = None
        self._start_time: Optional[float] = None
    
    async def execute(
        self,
        context: AgentContext,
        config: Dict[str, Any],
        stream: bool = False,
        debug_mode: bool = False
    ) -> AgentResponse:
        """Execute the agent.
        
        Args:
            context: Execution context
            config: Agent configuration
            stream: Whether to stream responses
            debug_mode: Enable debug logging
            
        Returns:
            Agent response
        """
        self._start_time = time.time()
        response = AgentResponse(status=AgentStatus.INITIALIZING)
        
        try:
            # Validate configuration
            if self.agent_def.config_schema:
                # TODO: Validate config against schema
                pass
            
            # Determine execution method
            if self.agent_def.entry_point.endswith('.py'):
                response = await self._execute_script(
                    context, config, stream, debug_mode
                )
            else:
                response = await self._execute_module(
                    context, config, stream, debug_mode
                )
            
        except asyncio.TimeoutError:
            response.status = AgentStatus.FAILED
            response.errors.append(
                f"Agent timed out after {self.agent_def.timeout_seconds}s"
            )
        except Exception as e:
            response.status = AgentStatus.FAILED
            response.errors.append(f"Execution error: {str(e)}")
            if debug_mode:
                import traceback
                response.errors.append(traceback.format_exc())
        finally:
            if self._start_time:
                response.duration_seconds = time.time() - self._start_time
            if self._process and self._process.poll() is None:
                self._process.terminate()
        
        return response
    
    async def _execute_script(
        self,
        context: AgentContext,
        config: Dict[str, Any],
        stream: bool,
        debug_mode: bool
    ) -> AgentResponse:
        """Execute agent as a script.
        
        Args:
            context: Execution context
            config: Agent configuration
            stream: Whether to stream responses
            debug_mode: Enable debug logging
            
        Returns:
            Agent response
        """
        response = AgentResponse(status=AgentStatus.RUNNING)
        
        # Prepare script path
        script_path = self.plugin_path / "agents" / self.agent_def.entry_point
        if not script_path.exists():
            raise AgentExecutionError(f"Agent script not found: {script_path}")
        
        # Prepare input data
        input_data = {
            "context": context.model_dump(),
            "config": config,
            "agent": self.agent_def.model_dump(),
        }
        
        # Execute script
        cmd = [sys.executable, str(script_path)]
        if debug_mode:
            cmd.append("--debug")
        
        self._process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(self.plugin_path)
        )
        
        # Send input
        stdout, stderr = self._process.communicate(
            input=json.dumps(input_data),
            timeout=self.agent_def.timeout_seconds
        )
        
        if self._process.returncode != 0:
            response.status = AgentStatus.FAILED
            response.errors.append(f"Script failed: {stderr}")
            return response
        
        # Parse output
        try:
            output = json.loads(stdout)
            response = AgentResponse.model_validate(output)
        except (json.JSONDecodeError, ValueError) as e:
            response.status = AgentStatus.FAILED
            response.errors.append(f"Invalid output: {str(e)}")
            if debug_mode:
                response.metadata["raw_output"] = stdout
        
        return response
    
    async def _execute_module(
        self,
        context: AgentContext,
        config: Dict[str, Any],
        stream: bool,
        debug_mode: bool
    ) -> AgentResponse:
        """Execute agent as a Python module.
        
        Args:
            context: Execution context
            config: Agent configuration
            stream: Whether to stream responses
            debug_mode: Enable debug logging
            
        Returns:
            Agent response
        """
        response = AgentResponse(status=AgentStatus.RUNNING)
        
        try:
            # Import the module
            module_path = self.agent_def.entry_point.replace('.', '/')
            if module_path.startswith('/'):
                module_path = module_path[1:]
            
            full_path = self.plugin_path / "agents" / f"{module_path}.py"
            if not full_path.exists():
                raise AgentExecutionError(f"Agent module not found: {full_path}")
            
            # Load module dynamically
            spec = importlib.util.spec_from_file_location(
                f"plugin_agent_{self.agent_def.name}",
                full_path
            )
            if not spec or not spec.loader:
                raise AgentExecutionError("Failed to load agent module")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find and execute main function
            if not hasattr(module, 'execute'):
                raise AgentExecutionError(
                    "Agent module must have an 'execute' function"
                )
            
            # Execute with timeout
            result = await asyncio.wait_for(
                self._run_module_function(
                    module.execute,
                    context,
                    config,
                    stream,
                    debug_mode
                ),
                timeout=self.agent_def.timeout_seconds
            )
            
            # Convert result to response
            if isinstance(result, AgentResponse):
                response = result
            elif isinstance(result, dict):
                response = AgentResponse.model_validate(result)
            else:
                response.status = AgentStatus.COMPLETED
                response.results = {"output": str(result)}
            
        except Exception as e:
            response.status = AgentStatus.FAILED
            response.errors.append(f"Module execution error: {str(e)}")
            if debug_mode:
                import traceback
                response.errors.append(traceback.format_exc())
        
        return response
    
    async def _run_module_function(
        self,
        func: Any,
        context: AgentContext,
        config: Dict[str, Any],
        stream: bool,
        debug_mode: bool
    ) -> Any:
        """Run the agent module function.
        
        Args:
            func: Function to execute
            context: Execution context
            config: Agent configuration
            stream: Whether to stream responses
            debug_mode: Enable debug logging
            
        Returns:
            Function result
        """
        # Check if function is async
        if asyncio.iscoroutinefunction(func):
            return await func(context, config, stream=stream, debug=debug_mode)
        else:
            # Run sync function in executor
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                func,
                context,
                config,
                stream,
                debug_mode
            )
    
    def cancel(self) -> None:
        """Cancel the agent execution."""
        if self._process and self._process.poll() is None:
            self._process.terminate()
            info(f"Cancelled agent: {self.agent_def.name}")