"""Type definitions for claude-code-setup.

This module contains all the data models and type definitions used throughout
the application, converted from the original TypeScript interfaces.
"""

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# Template-related types
class TemplateCategory(str, Enum):
    """Template categories matching the TypeScript TemplateCategory type."""

    PYTHON = "python"
    NODE = "node"
    PROJECT = "project"
    GENERAL = "general"


class TemplateMetadata(BaseModel):
    """Template metadata corresponding to TypeScript TemplateMetadata interface."""

    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    category: TemplateCategory = Field(..., description="Template category")
    dependencies: Optional[list[str]] = Field(
        default=None, description="Template dependencies"
    )


class Template(TemplateMetadata):
    """Template with content, corresponding to TypeScript Template interface."""

    content: str = Field(..., description="Template content")


class TemplateRegistry(BaseModel):
    """Available templates registry, corresponding to TypeScript TemplateRegistry interface."""

    templates: dict[str, Template] = Field(
        default_factory=dict, description="Registry of available templates"
    )


# Hook-related types
class HookEvent(str, Enum):
    """Hook event types matching the TypeScript HookEvent type."""

    USER_PROMPT_SUBMIT = "UserPromptSubmit"
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"
    STOP = "Stop"
    TOOL_OUTPUT_FILTERED = "ToolOutputFiltered"
    TOOL_ERROR_THROWN = "ToolErrorThrown"


class HookConfig(BaseModel):
    """Hook configuration corresponding to TypeScript HookConfig interface."""

    type: Literal["command"] = Field(default="command", description="Hook type")
    command: str = Field(..., description="Command to execute")


class HookMetadata(BaseModel):
    """Hook metadata corresponding to TypeScript HookMetadata interface."""

    name: str = Field(..., description="Hook name")
    description: str = Field(..., description="Hook description")
    category: str = Field(..., description="Hook category")
    event: HookEvent = Field(..., description="Hook event")
    matcher: Optional[str] = Field(default=None, description="Tool matcher pattern")
    dependencies: Optional[list[str]] = Field(
        default=None, description="Hook dependencies"
    )


class Hook(HookMetadata):
    """Hook with full configuration, corresponding to TypeScript Hook interface."""

    config: HookConfig = Field(..., description="Hook configuration")
    scripts: dict[str, str] = Field(
        default_factory=dict, description="Hook scripts (filename -> content)"
    )


class HookRegistry(BaseModel):
    """Hook registry corresponding to TypeScript HookRegistry interface."""

    hooks: dict[str, Hook] = Field(
        default_factory=dict, description="Registry of available hooks"
    )


class HookSettings(BaseModel):
    """Hook settings configuration corresponding to TypeScript HookSettings interface."""

    matcher: str = Field(..., description="Tool matcher pattern")
    hooks: list[HookConfig] = Field(
        default_factory=list, description="Hook configurations"
    )


class SettingsHooks(BaseModel):
    """Settings hooks structure corresponding to TypeScript SettingsHooks interface."""

    UserPromptSubmit: Optional[list[HookSettings]] = Field(
        default=None, alias="UserPromptSubmit"
    )
    PreToolUse: Optional[list[HookSettings]] = Field(default=None, alias="PreToolUse")
    PostToolUse: Optional[list[HookSettings]] = Field(default=None, alias="PostToolUse")
    Stop: Optional[list[HookSettings]] = Field(default=None, alias="Stop")
    ToolOutputFiltered: Optional[list[HookSettings]] = Field(
        default=None, alias="ToolOutputFiltered"
    )
    ToolErrorThrown: Optional[list[HookSettings]] = Field(
        default=None, alias="ToolErrorThrown"
    )


# Settings-related types
class PermissionsSettings(BaseModel):
    """Permissions configuration."""

    allow: list[str] = Field(default_factory=list, description="Allowed permissions")
    deny: Optional[list[str]] = Field(default=None, description="Denied permissions")


class ClaudeSettings(BaseModel):
    """Main Claude Code settings configuration."""

    theme: Optional[str] = Field(default="default", description="UI theme")
    permissions: PermissionsSettings = Field(
        default_factory=PermissionsSettings, description="Permission settings"
    )
    env: Optional[dict[str, str]] = Field(
        default=None, description="Environment variables"
    )
    hooks: Optional[SettingsHooks] = Field(
        default=None, description="Hook configurations"
    )
    autoUpdaterStatus: Optional[bool] = Field(
        default=True, description="Auto updater status"
    )
    preferredNotifChannel: Optional[str] = Field(
        default="terminal", description="Notification channel"
    )
    verbose: Optional[bool] = Field(default=False, description="Verbose logging")
    ignorePatterns: Optional[list[str]] = Field(
        default=None, description="Ignore patterns"
    )

    model_config = ConfigDict(populate_by_name=True)
