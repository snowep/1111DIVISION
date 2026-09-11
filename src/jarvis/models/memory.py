"""Memory record model — typed memory metadata per gate-protocol.md.

The memory schema used across the architecture:

    id, type, status, created, updated, source, confidence (0-1),
    authority, approval, scope, valid_from, valid_until,
    provenance (type + type-specific fields), actor, supersedes, related.

Confidence and authority are orthogonal — enforced by keeping them
independent fields (per Constitution Rule 6 / Rule 11).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class MemoryRecord:
    """A typed memory record parsed from canonical Markdown/YAML.

    ``metadata`` preserves the full original frontmatter so no information
    is lost; the dedicated fields are the ones the kernel reasons about.
    """

    id: str
    type: str
    status: str
    confidence: float
    authority: str
    approval: str
    source: str
    actor: str
    scope: str
    created: Optional[str] = None  # YYYY-MM-DD or ISO timestamp
    updated: Optional[str] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    supersedes: Optional[str] = None
    content: str = ""
    related: tuple[str, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    source_path: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "status": self.status,
            "confidence": self.confidence,
            "authority": self.authority,
            "approval": self.approval,
            "source": self.source,
            "actor": self.actor,
            "scope": self.scope,
            "created": self.created,
            "updated": self.updated,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "supersedes": self.supersedes,
            "content": self.content,
            "related": list(self.related),
            "provenance": dict(self.provenance),
            "source_path": self.source_path,
        }