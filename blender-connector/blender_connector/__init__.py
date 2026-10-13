"""CodeBuddy MCP connector for Blender (official Blender MCP add-on bridge)."""

from .connection import (
    BlenderConnectionError,
    BlenderExecutionError,
    execute,
    get_connection_params,
)

__version__ = "0.1.0"
__all__ = (
    "BlenderConnectionError",
    "BlenderExecutionError",
    "execute",
    "get_connection_params",
    "__version__",
)
