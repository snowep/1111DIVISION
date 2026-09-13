"""P8 — Self-adaptation preference-learning tests (deterministic, temp vault).

Exercises: signal validation, new preference creation, conflict supersede
(new preference supersedes old on same subject, old is phase SUPERSEDED and
provenance-linked, not ghost), reinforcement of identical statement
(unchanged), and the DERIVED preferences summary rebuild.
"""
from __future__ import annotations

import pytest

from jarvis.docstore.store import DocumentStore
from jarvis.memory.adapt import (
    AdaptationResult,
    Signal,
    apply_signal,
    normalize_subject,
)


@pytest.fixture()
def store(tmp_path):
    return DocumentStore(tmp_path)


def test_normalize_subject():
    assert normalize_subject("  Response-Length  ") == "response_length"
    assert normalize_subject("!!!") == "topic"


def test_apply_new_preference(store):
    result = apply_signal(store, Signal(kind="preference", subject="response-length", statement="prefer concise answers"))
    assert result.created == 1
    assert result.superseded == 0
    prefs = [r for r in store.list_documents(kind="semantic") if "preferences.md" not in r]
    assert len(prefs) == 1
    # Derived summary rebuilt.
    summary = store.read("semantic/preferences.md")
    assert "DERIVED" in summary.body
    assert "response_length" in summary.body


def test_apply_conflict_supersedes(store):
    apply_signal(store, Signal(kind="preference", subject="response-length", statement="prefer concise answers"))
    result = apply_signal(store, Signal(kind="correction", subject="response-length", statement="prefer verbose detail for architecture"))

    assert result.created == 1
    assert result.superseded == 1
    # Exactly one ACTIVE preference remains; the old one is SUPERSEDED.
    active = []
    superseded = []
    for rel in store.list_documents(kind="semantic"):
        if "preferences.md" in rel:
            continue
        note = store.read(rel)
        phase = note.metadata.get("phase")
        (active if phase == "ACTIVE" else superseded).append(rel)
    assert len(active) == 1
    assert len(superseded) == 1
    # New preference provenance links to the old.
    new_note = store.read(active[0])
    assert new_note.metadata["provenance"]["based_on"] == superseded
    # Summary reflects the new (ACTIVE) statement only.
    summary = store.read("semantic/preferences.md")
    assert "verbose detail" in summary.body
    assert "concise" not in summary.body.split("|")[1]  # old column gone


def test_apply_reinforcement_unchanged(store):
    apply_signal(store, Signal(kind="preference", subject="tone", statement="be direct and honest"))
    result = apply_signal(store, Signal(kind="reinforcement", subject="tone", statement="be direct and honest"))
    assert result.unchanged == 1
    assert result.created == 0
    assert result.superseded == 0


def test_apply_unknown_kind_ignored(store):
    result = apply_signal(store, Signal(kind="banana", subject="x", statement="y"))
    assert result.warnings
    assert result.created == 0
    assert len(store.list_documents(kind="semantic")) == 0  # nothing written