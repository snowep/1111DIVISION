"""JARVIS runtime kernel — filesystem I/O.

Two modules:

- ``workspace``  — canonical repository-root resolution + path confinement.
- ``boundary``   — read/write boundary enforcing read-only vs mutation.

The boundary is *symmetric*: reads from any anchor inside the workspace,
writes only to declared workspace anchors under explicit, validated,
audited mutation operations.
"""

from jarvis.io.boundary import (
    ReadBoundary,
    WriteBoundary,
    FullyMutableBoundary,
    ReadOnlyBoundary,
)
from jarvis.io.workspace import MatchedAnchor, Workspace, detect_repository_root

__all__ = [
    "MatchedAnchor",
    "Workspace",
    "detect_repository_root",
    "ReadBoundary",
    "WriteBoundary",
    "FullyMutableBoundary",
    "ReadOnlyBoundary",
]