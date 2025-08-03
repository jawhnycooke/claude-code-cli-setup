"""Type definitions for the plugin system.

This module defines all data models and types used by the plugin architecture,
including plugin manifests, capabilities, dependencies, and bundles.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class PluginStatus(str, Enum):
    """Plugin installation status."""
    
    AVAILABLE = "available"
    INSTALLED = "installed"
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"


class PluginVersion(BaseModel):
    """Plugin version information."""
    
    major: int = Field(..., ge=0, description="Major version number")
    minor: int = Field(..., ge=0, description="Minor version number") 
    patch: int = Field(..., ge=0, description="Patch version number")
    prerelease: Optional[str] = Field(None, description="Prerelease identifier")
    
    def __str__(self) -> str:
        """Return version string."""
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            base += f"-{self.prerelease}"
        return base
    
    @classmethod
    def from_string(cls, version_str: str) -> "PluginVersion":
        """Parse version from string like '1.2.3' or '1.2.3-beta'."""
        parts = version_str.split("-", 1)
        version_parts = parts[0].split(".")
        
        if len(version_parts) != 3:
            raise ValueError(f"Invalid version format: {version_str}")
        
        try:
            major, minor, patch = map(int, version_parts)
        except ValueError:
            raise ValueError(f"Invalid version numbers: {version_str}")
        
        prerelease = parts[1] if len(parts) > 1 else None
        
        return cls(major=major, minor=minor, patch=patch, prerelease=prerelease)
    
    def satisfies(self, requirement: str) -> bool:
        """Check if version satisfies a requirement like '^1.0.0' or '~1.2.0'."""
        if requirement.startswith("^"):
            # Caret: compatible with version
            req_version = self.from_string(requirement[1:])
            return (self.major == req_version.major and 
                    (self.minor > req_version.minor or
                     (self.minor == req_version.minor and self.patch >= req_version.patch)))
        elif requirement.startswith("~"):
            # Tilde: approximately equivalent
            req_version = self.from_string(requirement[1:])
            return (self.major == req_version.major and
                    self.minor == req_version.minor and
                    self.patch >= req_version.patch)
        else:
            # Exact match
            req_version = self.from_string(requirement)
            return (self.major == req_version.major and
                    self.minor == req_version.minor and
                    self.patch == req_version.patch and
                    self.prerelease == req_version.prerelease)


class PluginDependency(BaseModel):
    """Plugin dependency specification."""
    
    name: str = Field(..., description="Plugin name")
    version: str = Field(..., description="Version requirement (e.g., '^1.0.0')")
    optional: bool = Field(False, description="Whether dependency is optional")


class PluginCapabilities(BaseModel):
    """Capabilities provided by a plugin."""
    
    templates: List[str] = Field(
        default_factory=list, 
        description="Template names provided"
    )
    hooks: List[str] = Field(
        default_factory=list,
        description="Hook names provided"
    )
    agents: List[str] = Field(
        default_factory=list,
        description="Agent names provided"
    )
    workflows: List[str] = Field(
        default_factory=list,
        description="Workflow names provided"
    )
    commands: List[str] = Field(
        default_factory=list,
        description="CLI command names provided"
    )
    
    def is_empty(self) -> bool:
        """Check if plugin provides no capabilities."""
        return not any([
            self.templates,
            self.hooks,
            self.agents,
            self.workflows,
            self.commands
        ])


class PluginMetadata(BaseModel):
    """Plugin metadata information."""
    
    name: str = Field(..., description="Plugin unique identifier")
    display_name: str = Field(..., description="Human-readable plugin name")
    version: str = Field(..., description="Plugin version string")
    description: str = Field(..., description="Plugin description")
    author: str = Field(..., description="Plugin author")
    license: str = Field("MIT", description="Plugin license")
    homepage: Optional[str] = Field(None, description="Plugin homepage URL")
    repository: Optional[str] = Field(None, description="Plugin repository URL")
    keywords: List[str] = Field(
        default_factory=list,
        description="Plugin keywords for discovery"
    )
    category: str = Field(..., description="Plugin category")
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate plugin name format."""
        import re
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "Plugin name must contain only lowercase letters, numbers, and hyphens"
            )
        return v
    
    def get_version(self) -> PluginVersion:
        """Get parsed version object."""
        return PluginVersion.from_string(self.version)


class PluginManifest(BaseModel):
    """Plugin manifest (plugin.yaml) structure."""
    
    metadata: PluginMetadata = Field(..., description="Plugin metadata")
    dependencies: List[PluginDependency] = Field(
        default_factory=list,
        description="Plugin dependencies"
    )
    provides: PluginCapabilities = Field(
        default_factory=PluginCapabilities,
        description="Capabilities provided by plugin"
    )
    requires_python: Optional[str] = Field(
        None,
        description="Required Python version"
    )
    config_schema: Optional[Dict] = Field(
        None,
        description="Configuration schema for plugin settings"
    )
    
    def validate_dependencies(self, installed_plugins: Dict[str, "Plugin"]) -> List[str]:
        """Validate all dependencies are satisfied.
        
        Returns:
            List of error messages if validation fails
        """
        errors = []
        
        for dep in self.dependencies:
            if dep.name not in installed_plugins:
                if not dep.optional:
                    errors.append(f"Missing required dependency: {dep.name}")
            else:
                installed_version = installed_plugins[dep.name].manifest.metadata.get_version()
                if not installed_version.satisfies(dep.version):
                    errors.append(
                        f"Dependency {dep.name} version {installed_version} "
                        f"does not satisfy requirement {dep.version}"
                    )
        
        return errors


class Plugin(BaseModel):
    """Complete plugin information."""
    
    manifest: PluginManifest = Field(..., description="Plugin manifest")
    status: PluginStatus = Field(
        PluginStatus.AVAILABLE,
        description="Plugin status"
    )
    install_path: Optional[str] = Field(
        None,
        description="Path where plugin is installed"
    )
    install_date: Optional[datetime] = Field(
        None,
        description="When plugin was installed"
    )
    config: Dict = Field(
        default_factory=dict,
        description="Plugin configuration"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Any errors with the plugin"
    )
    
    @property
    def name(self) -> str:
        """Get plugin name."""
        return self.manifest.metadata.name
    
    @property
    def version(self) -> str:
        """Get plugin version string."""
        return self.manifest.metadata.version
    
    @property
    def is_installed(self) -> bool:
        """Check if plugin is installed."""
        return self.status in [PluginStatus.INSTALLED, PluginStatus.ACTIVE, PluginStatus.DISABLED]
    
    @property
    def is_active(self) -> bool:
        """Check if plugin is active."""
        return self.status == PluginStatus.ACTIVE


class PluginBundle(BaseModel):
    """Plugin bundle definition."""
    
    name: str = Field(..., description="Bundle name")
    display_name: str = Field(..., description="Human-readable bundle name")
    description: str = Field(..., description="Bundle description")
    plugins: Dict[str, str] = Field(
        ...,
        description="Plugin name to version requirement mapping"
    )
    category: str = Field("bundle", description="Bundle category")
    
    def get_plugin_list(self) -> List[PluginDependency]:
        """Convert to list of dependencies."""
        return [
            PluginDependency(name=name, version=version)
            for name, version in self.plugins.items()
        ]