"""
ORION Package

ORION Core Pipeline with Permissions & Tools
"""

from .core import ORION, Task, TaskStatus
from .permissions import (
    PermissionsEngine, ToolRegistry, PermissionLevel,
    ToolCategory, OperationType, ApprovalRequest, PermissionRule
)
from .tools import WorkspaceTools, ExecutorWithTools, ToolResult

__all__ = [
    "ORION",
    "Task", 
    "TaskStatus",
    "PermissionsEngine",
    "ToolRegistry",
    "PermissionLevel",
    "ToolCategory",
    "OperationType",
    "ApprovalRequest",
    "PermissionRule",
    "WorkspaceTools",
    "ExecutorWithTools",
    "ToolResult"
]

__version__ = "1.0.0"