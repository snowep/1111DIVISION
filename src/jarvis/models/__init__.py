"""JARVIS runtime kernel — data models.

Pure stdlib dataclasses, no I/O.  These are the typed objects the kernel
loads into, builds, and returns.
"""

from __future__ import annotations

from .context import (
    ContextLayer,
    LayerAssertion,
    RuntimeContext,
    USER_REQUEST_OVERRIDABLE_MIN,
    USER_REQUEST_OVERRIDABLE_MAX,
)
from .document import MarkdownDocument
from .identity import Identity
from .memory import MemoryRecord
from .result import OperationResult

__all__ = [
    "ContextLayer",
    "LayerAssertion",
    "RuntimeContext",
    "MarkdownDocument",
    "Identity",
    "MemoryRecord",
    "OperationResult",
    "USER_REQUEST_OVERRIDABLE_MIN",
    "USER_REQUEST_OVERRIDABLE_MAX",
]