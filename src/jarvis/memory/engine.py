"""Memory engine: routing, provenance, lifecycle, temporal pruning.

Everything here is deterministic and operates on canonical vault notes.
Derived artifacts (indexes, summaries) are NEVER written by this module —
they are always rebuilt by learn/ from the vault.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from jarvis.docstore.models import DocError, Document
from jarvis.docstore.store import DocumentStore, StoreError
from jarvis.memory.constants import (
    MemoryError,
    ROUTING,
    VALID_TRANSITIONS,
    now,
    phase_of,
)

_KIND_RE = re.compile(r"^[a-z0-9_-]+$")


@dataclass
class MemoryNote:
    """A parsed vault note plus its lifecycle metadata."""

    document: Document
    kind: str
    phase: str
    confidence: float
    importance: float
    valid_until: Optional[str]
    tags: list[str]
    provenance: dict[str, Any]


def parse_memory_note(doc: Document) -> MemoryNote:
    """Wrap a Document with memory-specific interpretation."""
    kind = doc.metadata.get("kind", "note")
    prov = doc.metadata.get("provenance")
    if prov is None:
        prov = {}
    elif not isinstance(prov, dict):
        prov = {"raw": prov}
    conf = doc.metadata.get("confidence", 0.5)
    try:
        conf = float(conf)
    except (TypeError, ValueError):
        conf = 0.5
        
    imp = doc.metadata.get("importance", 0.5)
    try:
        imp = float(imp)
    except (TypeError, ValueError):
        imp = 0.5
        
    valid_until = doc.metadata.get("valid_until")
    tags = doc.metadata.get("tags") or []
    if not isinstance(tags, list):
        tags = [tags]
    return MemoryNote(
        document=doc,
        kind=kind,
        phase=phase_of(doc.metadata),
        confidence=conf,
        importance=imp,
        valid_until=str(valid_until) if valid_until is not None else None,
        tags=[str(t) for t in tags],
        provenance=prov,
    )


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------
def route(kind: str) -> str:
    """Return the vault subdirectory a kind belongs in (default: 'semantic')."""
    return ROUTING.get(kind, ROUTING.get("semantic", "semantic"))


def update_routing(new_routing: dict[str, str]) -> None:
    """Extend the built-in routing matrix with user/project preferences.

    Entries map memory type -> short description. This mapping is canonical
    (lives in the vault), so it is stored as a decision note.
    """
    for k, v in new_routing.items():
        if not _KIND_RE.fullmatch(k):
            raise MemoryError(f"invalid memory type {k!r}: use [a-z0-9_-]")
        ROUTING[k] = v


def remember(
    store: DocumentStore,
    text: str,
    *,
    kind: str = "episodic",
    title: str | None = None,
    tags: list[str] | None = None,
    confidence: float | None = None,
    importance: float | None = None,
    valid_until: str | None = None,
    provenance: dict[str, Any] | None = None,
    phase: str = "OBSERVED",
    doc_id: str | None = None,
    created: str | None = None,
    actor: str = "jarvis",
) -> MemoryNote:
    """Create a memory note in the correct vault subdirectory (routing)."""
    meta: dict[str, Any] = {
        "type": kind,  # memory type (episodic/semantic/procedural/...)
        "phase": phase.upper(),
        "actor": actor,
    }
    if tags:
        meta["tags"] = tags
    if confidence is not None:
        meta["confidence"] = confidence
    if importance is not None:
        meta["importance"] = importance
    if valid_until:
        meta["valid_until"] = valid_until
    if provenance:
        meta["provenance"] = provenance
    if created:
        meta["created"] = created

    target_dir = route(kind)
    doc = store.create(
        kind=target_dir,  # store.create uses 'kind' as the subdir path
        title=title or (text[:60].strip() if text else "Memory"),
        body=text,
        metadata=meta,
        doc_id=doc_id,
    )
    return parse_memory_note(doc)


def _set_phase(store: DocumentStore, rel: str, new_phase: str, reason: str) -> MemoryNote:
    """Advance a note's lifecycle phase, enforcing valid transitions."""
    new_phase = new_phase.upper()
    doc = store.read(rel)
    current = phase_of(doc.metadata)
    if current == new_phase:
        return parse_memory_note(doc)
    if new_phase not in VALID_TRANSITIONS.get(current, ()):
        raise MemoryError(
            f"invalid transition {current} -> {new_phase} (allowed: "
            f"{VALID_TRANSITIONS.get(current, ())})"
        )
    meta = {"phase": new_phase}
    prov = doc.metadata.get("provenance") or {}
    if isinstance(prov, dict):
        prov = dict(prov)
        prov.setdefault("transitions", []).append(
            {
                "from": current,
                "to": new_phase,
                "at": now(),
                "reason": reason,
            }
        )
        meta["provenance"] = prov
    store.update(rel, metadata=meta)
    return parse_memory_note(store.read(rel))


def supersede(store: DocumentStore, rel: str, reason: str = "superseded") -> MemoryNote:
    return _set_phase(store, rel, "SUPERSEDED", reason)


def reject(store: DocumentStore, rel: str, reason: str = "rejected") -> MemoryNote:
    return _set_phase(store, rel, "REJECTED", reason)


def verify(store: DocumentStore, rel: str, reason: str = "verified") -> MemoryNote:
    return _set_phase(store, rel, "VERIFIED", reason)


def activate(store: DocumentStore, rel: str, reason: str = "activated") -> MemoryNote:
    return _set_phase(store, rel, "ACTIVE", reason)


def list_active(store: DocumentStore, kind: str | None = None) -> list[MemoryNote]:
    """Return notes whose phase is ACTIVE/VERIFIED and not expired (if dated),
    sorted by importance (highest first) then by update date.
    """
    out: list[MemoryNote] = []
    now_dt = datetime.now(timezone.utc)
    for rel in store.list_documents(kind):
        try:
            note = parse_memory_note(store.read(rel))
        except (StoreError, DocError):
            continue
        if note.phase not in ("ACTIVE", "VERIFIED"):
            continue
        if note.valid_until:
            try:
                v = datetime.fromisoformat(note.valid_until)
                if v < now_dt:
                    continue  # expired temporal knowledge
            except ValueError:
                pass  # malformed valid_until treated as no expiry
        out.append(note)
    out.sort(key=lambda n: (-n.importance, n.document.metadata.get("updated", "")))
    return out


# ---------------------------------------------------------------------------
# Temporal knowledge handling
# ---------------------------------------------------------------------------
def forget_expired(store: DocumentStore, dry_run: bool = False) -> list[str]:
    """Archive (not delete) notes whose valid_until has passed.

    Expired temporal knowledge is moved to SUPERSEDED so it is retained for
    audit but no longer counts as active. Returns list of archived rel paths.
    """
    now_dt = datetime.now(timezone.utc)
    archived: list[str] = []
    for rel in store.list_documents():
        try:
            doc = store.read(rel)
        except (StoreError, DocError):
            continue
        valid_until = doc.metadata.get("valid_until")
        if not valid_until:
            continue
        try:
            v = datetime.fromisoformat(str(valid_until))
        except ValueError:
            continue
        if v < now_dt:
            archived.append(rel)
            if not dry_run:
                try:
                    supersede(store, rel, reason=f"expired at {valid_until}")
                except (StoreError, MemoryError):
                    continue
    return archived


# ---------------------------------------------------------------------------
# Provenance helpers
# ---------------------------------------------------------------------------
def provenance_chain(store: DocumentStore, rel: str, depth: int = 3) -> list[dict[str, Any]]:
    """Resolve the provenance 'based_on' links of a note into a chain.

    Returns an ordered list of {rel, phase, confidence, title} from the note
    itself back through its ancestors, up to `depth` steps.
    """
    chain: list[dict[str, Any]] = []
    current = rel
    seen: set[str] = set()
    for _ in range(depth):
        if current in seen:
            break
        seen.add(current)
        try:
            doc = store.read(current)
        except (StoreError, DocError):
            break
        note = parse_memory_note(doc)
        chain.append(
            {
                "rel": current,
                "phase": note.phase,
                "confidence": note.confidence,
                "title": doc.metadata.get("title", current),
            }
        )
        prov = doc.metadata.get("provenance") or {}
        based_on = prov.get("based_on") if isinstance(prov, dict) else None
        if isinstance(based_on, str):
            current = based_on
        elif isinstance(based_on, list) and based_on:
            current = str(based_on[-1])
        else:
            break
    return chain