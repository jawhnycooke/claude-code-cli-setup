"""Custom exceptions for claude-code-setup."""


class ClaudeSetupError(Exception):
    """Base exception for claude-code-setup errors."""

    pass


class ConfigurationError(ClaudeSetupError):
    """Raised when there's an issue with configuration."""

    pass


class TemplateError(ClaudeSetupError):
    """Raised when there's an issue with template operations."""

    pass


class HookError(ClaudeSetupError):
    """Raised when there's an issue with hook operations."""

    pass


class HookLoadError(HookError):
    """Raised when hook loading fails."""

    pass


class HookNotFoundError(HookError):
    """Raised when a requested hook cannot be found."""

    pass


class ValidationError(ClaudeSetupError):
    """Raised when validation fails."""

    pass


class FileOperationError(ClaudeSetupError):
    """Raised when file operations fail."""

    pass


class InteractiveModeError(ClaudeSetupError):
    """Raised when interactive mode encounters an error."""

    pass
