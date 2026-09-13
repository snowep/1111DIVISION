"""P7 — Self-learn: lesson consolidation engine.

Post-task review produces lessons in `vault/learned/` (from critique) and
failures in `vault/failures/`. This module consolidates them into a
maintainable knowledge base:

- Scans `vault/learned/` + `vault/failures/` for lesson notes.
- Deduplicates by a normalized lesson-text hash: duplicates collapse to the
  newest (higher `updated`), older duplicates are superseded (phase
  `SUPERSEDED`) and linked via `provenance.based_on`.
- Extracts reusable procedural guidance into `vault/procedural/` (one note
  per distinct lesson fingerprint, kind: `procedure`) with provenance to
  the source lesson(s).
- Builds a DERIVED `vault/learned/_index.md` (always rebuildable, never
  authoritative, never hand-edited).

Everything is deterministic: same vault → same index, same dedupe choice.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from jarvis.docstore.store import DocumentStore
from jarvis.memory.engine import MemoryNote, parse_memory_note, supersede

_LEARNED_KIND = "learned"
_FAILURES_KIND = "failures"
_PROCEDURAL_KIND = "procedural"
_INDEX_REL = "learned/_index.md"

_SRC_KINDS = (_LEARNED_KIND, _FAILURES_KIND)


@dataclass
class Consolidation:
    """Deterministic result of a consolidation pass."""

    scanned_notes: int = 0
    distinct_fingerprints: int = 0
    duplicates_superseded: int = 0
    procedures_written: int = 0
    index_rebuilt: bool = False
    obsolete: list[str] = field(default_factory=list)  # rels superseded
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scanned_notes": self.scanned_notes,
            "distinct_fingerprints": self.distinct_fingerprints,
            "duplicates_superseded": self.duplicates_superseded,
            "procedures_written": self.procedures_written,
            "index_rebuilt": self.index_rebuilt,
            "obsolete": self.obsolete,
            "warnings": self.warnings,
        }


def _normalize(text: str) -> str:
    t = text.lower().strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^a-z0-9 _-]", "", t)
    return t


def _fingerprint(text: str) -> str:
    return hashlib.sha256(_normalize(text).encode("utf-8")).hexdigest()[:16]


def _lesson_text(note: MemoryNote) -> str:
    body = (note.document.body or "").strip()
    if body:
        return body
    return str(note.document.metadata.get("lesson", ""))


def _updated_ts(note: MemoryNote) -> str:
    return str(note.document.metadata.get("updated", "") or "")


def _write_procedure(
    store: DocumentStore,
    fingerprint: str,
    lesson_text: str,
    source_paths: list[str],
    existing: set[str],
) -> tuple[bool, str]:
    """Write one procedural note; returns (created, path). idempotent."""
    doc_id = f"proc-{fingerprint}"
    rel = f"{_PROCEDURAL_KIND}/{doc_id}.md"
    if rel in existing:
        return False, rel
    meta = {
        "id": doc_id,
        "type": "note",
        "kind": "procedure",
        "tags": ["procedure", "learned"],
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "self-learn",
        "confidence": 0.7,
        "importance": 0.6,
        "provenance": {"based_on": source_paths},
        "phase": "ACTIVE",
    }
    store.create(
        kind=_PROCEDURAL_KIND,
        title=f"Procedure {fingerprint}",
        body=f"# Procedure\n\n{lesson_text}\n\nSources: {', '.join(source_paths)}",
        metadata=meta,
        doc_id=doc_id,
    )
    return True, rel


def consolidate_lessons(store: DocumentStore) -> Consolidation:
    """Run the consolidation pass over learned + failure notes."""
    result = Consolidation()

    # 1. Scan source dirs for notes (kind in {learned, failure, lesson}).
    notes: list[tuple[str, MemoryNote]] = []
    for src_kind in _SRC_KINDS:
        for rel in store.list_documents(kind=src_kind):
            # Skip the derived index itself (never a lesson).
            if rel == _INDEX_REL:
                continue
            try:
                doc = store.read(rel)
            except Exception as exc:  # StoreError
                result.warnings.append(f"unreadable {rel}: {exc}")
                continue
            note = parse_memory_note(doc)
            # Accept lesson-like kinds. Note: DocumentStore.create() sets
            # metadata['kind'] to the DIR name (learned/failures), so both
            # the dir kind and the semantic kind must be accepted.
            if note.kind not in ("learned", "failures", "failure", "lesson"):
                continue
            notes.append((rel, note))
    result.scanned_notes = len(notes)

    # 2. Deterministic dedupe: newest timestamp wins per fingerprint.
    by_fp: dict[str, list[tuple[str, MemoryNote]]] = {}
    for rel, note in notes:
        fp = _fingerprint(_lesson_text(note))
        by_fp.setdefault(fp, []).append((rel, note))

    result.distinct_fingerprints = len(by_fp)

    # 3. For each fingerprint: keep newest, supersede older duplicates.
    for fp, group in by_fp.items():
        if len(group) == 1:
            continue
        # Deterministic: sort by (updated_ts, rel), newest last.
        group.sort(key=lambda rn: (_updated_ts(rn[1]), rn[0]))
        newest_rel = group[-1][0]
        for old_rel, _old_note in group[:-1]:
            try:
                supersede(store, old_rel, reason="duplicate lesson (consolidated)")
                # Link the new one's provenance to the superseded source.
                doc = store.read(newest_rel)
                prov = doc.metadata.get("provenance") or {}
                if isinstance(prov, dict):
                    prov = dict(prov)
                    based = prov.get("based_on")
                    if isinstance(based, str):
                        based = [based]
                    based = list(based or [])
                    if old_rel not in based:
                        based.append(old_rel)
                    prov["based_on"] = based
                    store.update(newest_rel, metadata={"provenance": prov})
                result.duplicates_superseded += 1
                result.obsolete.append(old_rel)
            except Exception as exc:
                result.warnings.append(f"supersede failed for {old_rel}: {exc}")

    # 4. Write one procedure per distinct fingerprint (idempotent).
    existing = set(store.list_documents(kind=_PROCEDURAL_KIND))
    for fp, group in by_fp.items():
        newest_rel, newest_note = group[-1]
        created, _path = _write_procedure(
            store, fp, _lesson_text(newest_note),
            [r for r, _n in group],
            existing=existing,
        )
        if created:
            result.procedures_written += 1

    # 5. Rebuild derived index (overwrite).
    lines = [
        "# Learned Lessons Index",
        "",
        "> **DERIVED** — rebuilt deterministically by `consolidate_lessons()`.",
        "> Do not hand-edit; contents are derived from `vault/learned/` + `vault/failures/`.",
        "",
        f"Scanned: {result.scanned_notes} notes, {result.distinct_fingerprints} distinct lessons.",
        "",
        "| Fingerprint | Newest source | Superseded |",
        "|---|---|---|",
    ]
    for fp in sorted(by_fp):
        group = by_fp[fp]
        newest = group[-1][0]
        superseded = ", ".join(r for r, _n in group[:-1]) or "—"
        lines.append(f"| `{fp}` | {newest} | {superseded} |")
    body = "\n".join(lines)
    index_meta = {
        "id": "learned-index",
        "type": "index",
        "kind": "derived-index",
        "tags": ["derived", "index", "learned"],
        "source": "self-learn",
        "phase": "ACTIVE",
    }
    if _INDEX_REL in store.list_documents(kind=_LEARNED_KIND):
        # update() never raises on existing; derived artifact is overwritten.
        store.update(_INDEX_REL, body=body, metadata=index_meta)
    else:
        store.create(
            kind=_LEARNED_KIND,
            title="Learned Lessons Index",
            body=body,
            metadata=index_meta,
            doc_id="_index",
        )
    result.index_rebuilt = True
    return result