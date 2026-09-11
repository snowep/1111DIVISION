"""Load memory records from ``.jarvis/memory/``.

Memory records are frontmatter-validated Markdown files with the full
metadata schema from gate-protocol.md.
"""

from __future__ import annotations

from pathlib import Path

from jarvis.errors import DocumentError
from jarvis.io.workspace import Workspace
from jarvis.models.memory import MemoryRecord
from jarvis.models.document import MarkdownDocument
from jarvis.validation.frontmatter import (
    check_enum,
    check_float_range,
    check_required,
)
from jarvis.validation.pyaml import extract_frontmatter
from jarvis.validation.status import (
    ACTOR_VALUES,
    APPROVAL_VALUES,
    AUTHORITY_VALUES,
    MEMORY_TYPES,
    VALID_STATUS_VALUES,
)


def load_memory_record(workspace: Workspace, candidate: str) -> MemoryRecord:
    """Load a memory record from the workspace, validating all fields.

    The candidate must be inside ``.jarvis/memory/``.  The function
    performs the full frontmatter schema check — any missing required
    field or invalid value raises a typed error.
    """
    source_path = workspace.resolve(candidate)
    rel = source_path.relative_to(workspace.root)

    if ".jarvis/memory" not in str(source_path).replace("\\", "/"):
        raise DocumentError(
            f"Memory record must live under .jarvis/memory/, got {str(source_path)!r}.",
            path=str(source_path),
            code="memory_wrong_location",
        )

    raw = source_path.read_text(encoding="utf-8")
    metadata, body, has_fm = extract_frontmatter(raw)

    # Full schema enforcement for memory records
    check_required(
        metadata,
        "id", "type", "status", "source", "confidence", "authority",
        "approval", "actor", "scope", "created", "valid_from", "valid_until",
        "supersedes", "related",
        path=str(source_path),
    )
    check_enum(metadata, "status", VALID_STATUS_VALUES, path=str(source_path))
    check_enum(metadata, "type", MEMORY_TYPES, path=str(source_path))
    check_enum(metadata, "authority", AUTHORITY_VALUES, path=str(source_path))
    check_enum(metadata, "approval", APPROVAL_VALUES, path=str(source_path))
    check_enum(metadata, "actor", ACTOR_VALUES, path=str(source_path))
    check_float_range(metadata, "confidence", low=0.0, high=1.0, path=str(source_path))

    # Related references must be a list
    related = metadata.get("related", [])
    if not isinstance(related, list):
        raise DocumentError(
            f"Memory record 'related' field must be a list, got {type(related).__name__!r}.",
            path=str(source_path),
            code="related_not_list",
        )

    return MemoryRecord(
        id=metadata["id"],
        type=metadata["type"],
        status=metadata["status"],
        confidence=float(metadata["confidence"]),
        authority=metadata["authority"],
        approval=metadata["approval"],
        source=metadata["source"],
        actor=metadata["actor"],
        scope=metadata["scope"],
        created=metadata.get("created"),
        updated=metadata.get("updated"),
        valid_from=metadata.get("valid_from"),
        valid_until=metadata.get("valid_until"),
        supersedes=metadata.get("supersedes"),
        content=body,
        related=tuple(str(r) for r in related),
        provenance=metadata.get("provenance") or {},
        metadata=metadata,
        source_path=str(source_path),
    )