"""P8 — Self-adaptation: preference/correction learning.

Detects durable preference + correction signals and folds them into the
semantic memory (`vault/semantic/`, kind `preference`). Rules:

- A signal is a structured `(kind, subject, statement, source, importance)`
  from the user or a self-review; it is the INTELLIGENCE LAYER's job to
  detect it, this module records it deterministically.
- New preferences supersede old ones on the same subject (same normalized
  subject key) instead of ghosting — the lifecycle phase is advanced via
  the memory engine and the old note stays linked through provenance.
- A DERIVED `vault/semantic/preferences.md` summary is rebuilt each run
  (never authoritative, never hand-edited).

Everything is deterministic: same signals → same preferences, same summary.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from jarvis.docstore.store import DocumentStore
from jarvis.memory.engine import MemoryNote, parse_memory_note, supersede
from jarvis.memory.constants import now

_PREF_KIND = "semantic"
_PREF_SUMMARY_REL = "semantic/preferences.md"
_SUBJECT_RE = re.compile(r"[^a-z0-9]+")


@dataclass
class Signal:
    """A detected correction/reference signal (structured, from the layer)."""

    kind: str  # "correction" | "preference" | "reinforcement"
    subject: str  # canonical topic, e.g. "response-length"
    statement: str  # the durable rule/preference, e.g. "prefer concise"
    source: str = "user"  # provenance: user | self-review | task
    importance: float = 0.6


@dataclass
class AdaptationResult:
    created: int = 0
    superseded: int = 0
    unchanged: int = 0
    summary_rebuilt: bool = False
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "created": self.created,
            "superseded": self.superseded,
            "unchanged": self.unchanged,
            "summary_rebuilt": self.summary_rebuilt,
            "warnings": self.warnings,
        }


def normalize_subject(subject: str) -> str:
    return _SUBJECT_RE.sub("_", subject.strip().lower()).strip("_") or "topic"


def _existing_preference(store: DocumentStore) -> list[tuple[str, MemoryNote]]:
    """Return (rel, note) for every ACTIVE semantic preference note."""
    out: list[tuple[str, MemoryNote]] = []
    for rel in store.list_documents(kind=_PREF_KIND):
        if rel == _PREF_SUMMARY_REL:
            continue
        try:
            doc = store.read(rel)
        except Exception:
            continue
        note = parse_memory_note(doc)
        # DocumentStore.create() sets metadata['kind'] to the DIR name
        # ('semantic'), so the real marker is metadata.subject.
        if not note.document.metadata.get("subject"):
            continue
        if note.phase != "ACTIVE":
            continue  # superseded prefs are excluded from the active set
        out.append((rel, note))
    return out


def _signal_matches(subject: str, note: MemoryNote) -> bool:
    existing = str(note.document.metadata.get("subject", "") or "")
    return normalize_subject(existing) == normalize_subject(subject)


def _build_summary(store: DocumentStore, prefs: list[tuple[str, MemoryNote]]) -> None:
    lines = [
        "# Preferences",
        "",
        "> **DERIVED** — rebuilt deterministically by `apply_signal()`.",
        "> Do not hand-edit; contents are derived from `vault/semantic/` (kind=preference).",
        "",
        "| Subject | Statement | Source | Updated |",
        "|---|---|---|---|",
    ]
    for rel, note in sorted(prefs, key=lambda rn: (str(rn[1].document.metadata.get("subject", "")), rn[0])):
        meta = note.document.metadata
        lines.append(
            f"| {meta.get('subject', '')} | "
            f"{str(note.document.body or '').strip().replace(chr(10), ' ')} | "
            f"{meta.get('source', '')} | {meta.get('updated', '')} |"
        )
    body = "\n".join(lines)
    if _PREF_SUMMARY_REL in store.list_documents(kind=_PREF_KIND):
        store.update(_PREF_SUMMARY_REL, body=body)
    else:
        store.create(
            kind=_PREF_KIND,
            title="Preferences",
            body=body,
            metadata={
                "id": "preferences",
                "type": "index",
                "kind": "derived-index",
                "tags": ["derived", "index", "preference"],
                "source": "self-adapt",
                "phase": "ACTIVE",
            },
            doc_id="preferences",
        )


def apply_signal(store: DocumentStore, signal: Signal) -> AdaptationResult:
    """Record a preference/correction signal, superseding conflicts."""
    result = AdaptationResult()
    if signal.kind not in ("correction", "preference", "reinforcement"):
        result.warnings.append(f"unknown signal kind {signal.kind!r}; ignored")
        return result

    subject = normalize_subject(signal.subject)
    prefs = _existing_preference(store)
    matching = [rn for rn in prefs if _signal_matches(subject, rn[1])]

    if matching:
        # Supersede existing note(s), keep the newest for provenance.
        old_rel, old_note = matching[0]
        old_stmt = str(old_note.document.body or "").strip()
        new_stmt = signal.statement.strip()
        if normalize_subject(old_stmt) == normalize_subject(new_stmt):
            # Identical preference: reinforce (no change).
            result.unchanged += 1
        else:
            supersede(store, old_rel, reason="superseded by updated preference")
            result.superseded += 1
            create_preference(store, signal, subject, based_on=[old_rel])
            result.created += 1
    else:
        create_preference(store, signal, subject, based_on=[])
        result.created += 1

    _build_summary(store, _existing_preference(store))
    result.summary_rebuilt = True
    return result


def create_preference(
    store: DocumentStore,
    signal: Signal,
    subject: str,
    *,
    based_on: list[str],
) -> MemoryNote:
    """Create one preference note (deterministic id from subject + source)."""
    import hashlib

    stamp = now()
    stmt_fp = hashlib.sha256(signal.statement.strip().encode("utf-8")).hexdigest()[:8]
    doc_id = f"pref-{subject}-{stmt_fp}"
    meta = {
        "id": doc_id,
        "type": "note",
        "kind": "preference",
        "tags": ["preference", signal.kind],
        "created": stamp,
        "updated": stamp,
        "source": signal.source,
        "confidence": 0.8,
        "importance": signal.importance,
        "subject": subject,
        "provenance": {"based_on": based_on} if based_on else {},
        "phase": "ACTIVE",
    }
    doc = store.create(
        kind=_PREF_KIND,
        title=f"Preference: {subject}",
        body=signal.statement.strip(),
        metadata=meta,
        doc_id=doc_id,
    )
    return parse_memory_note(doc)