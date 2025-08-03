"""Plugin Agent Framework.

This module provides the agent framework for Claude Code Setup plugins,
allowing plugins to define AI-powered agents that can perform complex tasks.
"""

from .types import (
    AgentCapability,
    AgentContext,
    AgentDefinition,
    AgentExecutor,
    AgentMessage,
    AgentResponse,
    AgentStatus,
)
from .registry import AgentRegistry
from .executor import AgentExecutor as AgentExecutorImpl

__all__ = [
    "AgentCapability",
    "AgentContext",
    "AgentDefinition",
    "AgentExecutor",
    "AgentExecutorImpl",
    "AgentMessage",
    "AgentResponse",
    "AgentStatus",
    "AgentRegistry",
]