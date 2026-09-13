"""P7 — Self-learn consolidation tests (deterministic, temp vault).

Exercises: scan learned+failure dirs, dedupe by fingerprint (newest wins,
older superseded), procedural guidance extraction per fingerprint, and the
derived index rebuild. Runs against an isolated temp DocumentStore.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.docstore.store import DocumentStore
from jarvis.memory.learn import (
    _fingerprint,
    _normalize,
    consolidate_lessons,
)

LESSON_A = "The crawl depth cap must be checked before enqueueing links."
LESSON_A_DUP = "  The CRAWL DEPTH cap must be checked   before enqueueing links!  "
LESSON_B = "Robots.txt fetch must never consume the page budget."


@pytest.fixture()
def store(tmp_path):
    return DocumentStore(tmp_path)


def _lesson_meta(kind: str, updated: str, lesson: str, doc_id: str) -> dict:
    return {
        "id": doc_id,
        "type": "note",
        "kind": kind,
        "tags": ["lesson"],
        "created": "2026-01-01T00:00:00+00:00",
        "updated": updated,
        "source": "test",
        "confidence": 0.8,
        "importance": 0.8,
        "phase": "ACTIVE",
    }


def test_normalize_and_fingerprint():
    assert _fingerprint(LESSON_A) == _fingerprint(LESSON_A_DUP)
    assert _fingerprint(LESSON_A) != _fingerprint(LESSON_B)


def test_consolidation_dedupes_and_indexes(store):
    # Two duplicate lessons (same fingerprint) + one distinct.
    store.create(
        kind="learned", title="A1", body=LESSON_A,
        metadata=_lesson_meta("learned", "2026-01-02T00:00:00+00:00", LESSON_A, "a1"),
        doc_id="a1",
    )
    store.create(
        kind="learned", title="A2", body=LESSON_A_DUP,
        metadata=_lesson_meta("learned", "2026-01-03T00:00:00+00:00", LESSON_A_DUP, "a2"),
        doc_id="a2",
    )
    store.create(
        kind="failures", title="B", body=LESSON_B,
        metadata=_lesson_meta("failure", "2026-01-01T00:00:00+00:00", LESSON_B, "b1"),
        doc_id="b1",
    )

    result = consolidate_lessons(store)

    assert result.scanned_notes == 3
    assert result.distinct_fingerprints == 2
    assert result.duplicates_superseded == 1
    assert result.procedures_written == 2
    assert result.index_rebuilt is True
    assert "learned/a1.md" in result.obsolete  # older dup superseded
    # Newest (a2) kept ACTIVE.
    assert store.read("learned/a2.md").metadata.get("phase") == "ACTIVE"

    # Procedures extracted for both distinct fingerprints.
    procs = store.list_documents(kind="procedural")
    assert len(procs) == 2

    # Index rebuilt + derived.
    index = store.read("learned/_index.md")
    assert "DERIVED" in index.body
    assert "2 distinct lessons" in index.body


def test_consolidation_idempotent(store):
    # Running twice must not duplicate procedures or re-supersede.
    store.create(
        kind="learned", title="A", body=LESSON_A,
        metadata=_lesson_meta("learned", "2026-01-02T00:00:00+00:00", LESSON_A, "a1"),
        doc_id="a1",
    )
    first = consolidate_lessons(store)
    assert first.procedures_written == 1

    second = consolidate_lessons(store)
    assert second.procedures_written == 0  # already exists
    assert second.duplicates_superseded == 0
    assert len(store.list_documents(kind="procedural")) == 1


def test_consolidation_empty_vault(store):
    result = consolidate_lessons(store)
    assert result.scanned_notes == 0
    assert result.distinct_fingerprints == 0
    assert result.index_rebuilt is True  # always rebuilds (even if empty)