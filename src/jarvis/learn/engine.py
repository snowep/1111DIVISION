"""Deterministic learning: rebuild derived artifacts from canonical documents.

Derived artifacts live under <root>/learn/ and are ALWAYS recomputed from the
canonical vault notes. Nothing is stored here that cannot be regenerated:

  index.json   -- machine-readable inventory (counts, tags, titles, updated at)
  lessons.md   -- human-readable summary, including extracted lesson bullets
  state.md     -- derived JARVIS state summary (world model, active skills)
"""
from __future__ import annotations

import json
from collections import Counter
from typing import Any

from jarvis.docstore.models import DocError
from jarvis.docstore.store import DocumentStore, StoreError
from jarvis.memory.engine import list_active


def learn(store: DocumentStore) -> dict[str, Any]:
    """Scan all documents and rebuild learn/index.json + learn/lessons.md.

    Returns the resulting index dict.
    """
    index = build_index(store)
    (store.learn_dir / "index.json").write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (store.learn_dir / "lessons.md").write_text(
        render_lessons(store, index), encoding="utf-8"
    )
    _write_state_summary(store, index)
    return index


def _write_state_summary(store: DocumentStore, index: dict[str, Any]) -> None:
    """Write the derived 'current state' world-model summary (never authoritative)."""
    active = list_active(store)
    skills: list[str] = []
    try:
        from jarvis.skills.skill import load_skills

        skills = [s.name for s in load_skills(store.root) if s.status == "active"]
    except Exception:
        skills = []
    target = store.learn_dir / "state.md"
    lines = [
        "# Derived JARVIS State",
        "",
        "> **DERIVED** — rebuilt from canonical vault + skills. Never edit by hand.",
        "",
        f"Documents: {index.get('document_count', 0)}",
        f"Active memories: {len(active)}",
        f"Skills: {', '.join(skills) if skills else '(none)'}",
        "",
        "## Active Memories",
        "",
    ]
    if active:
        for note in active:
            lines.append(f"- [{note.kind}] {note.document.metadata.get('title', note.document.path)}")
    else:
        lines.append("(none)")
    lines.append("")
    target.write_text("\n".join(lines), encoding="utf-8")


def build_index(store: DocumentStore) -> dict[str, Any]:
    """Summative, deterministic index over every document."""
    tag_counter: Counter[str] = Counter()
    kinds: Counter[str] = Counter()
    docs = []
    for rel in store.list_documents():
        try:
            doc = store.read(rel)
        except StoreError:
            continue
        meta = doc.metadata
        kinds[meta.get("kind", "unknown")] += 1
        tags = _as_list(meta.get("tags"))
        for tag in tags:
            tag_counter[tag] += 1
        docs.append(
            {
                "path": rel,
                "id": meta.get("id", ""),
                "kind": meta.get("kind", "unknown"),
                "title": meta.get("title", ""),
                "tags": tags,
                "updated": meta.get("updated", meta.get("created", "")),
                "words": len(doc.body.split()),
                "phase": meta.get("phase", "OBSERVED"),
            }
        )
    docs.sort(key=lambda d: d["path"])
    return {
        "document_count": len(docs),
        "kinds": dict(sorted(kinds.items())),
        "tags": dict(sorted(tag_counter.items())),
        "documents": docs,
    }


def render_lessons(store: DocumentStore, index: dict[str, Any]) -> str:
    """Human-readable lessons summary derived only from canonical notes."""
    lessons: list[str] = []
    for doc in index["documents"]:
        try:
            parsed = store.read(doc["path"])
        except StoreError:
            continue
        extracted = _extract_lessons(parsed.body)
        if extracted:
            lessons.extend(f"- [{doc['id']}] {text}" for text in extracted)

    lines = ["# Lessons", ""]
    lines.append(f"Generated from {index['document_count']} documents.")
    lines.append("")
    lines.append("## Tags")
    lines.append("")
    if index["tags"]:
        for tag, count in index["tags"].items():
            lines.append(f"- {tag}: {count}")
    else:
        lines.append("(none)")
    lines.append("")
    lines.append("## Extracted Lessons")
    lines.append("")
    if lessons:
        lines.extend(lessons)
    else:
        lines.append("(none)")
    lines.append("")
    return "\n".join(lines)


def _extract_lessons(body: str) -> list[str]:
    """Grab lines under a '## Lessons' heading, skipping nested headings."""
    out: list[str] = []
    in_lessons = False
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_lessons = stripped.lower().lstrip("# ").startswith("lesson")
            continue
        if in_lessons and stripped.startswith("- "):
            out.append(stripped[2:].strip())
    return out


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]