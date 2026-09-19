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

from .memory_gateway import MemoryGateway
from .persona_router import PersonaRouter
from .model import ModelConfig, ModelAdapterInterface, SimpleModelAdapter

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
    "ToolResult",
    "MemoryGateway",
    "PersonaRouter",
    "ModelConfig",
    "ModelAdapterInterface",
    "SimpleModelAdapter",
]

__version__ = "1.0.0"
