"""Tests for the P1 memory system: routing, provenance, phases, temporal."""
import pytest

from jarvis.docstore.store import StoreError
from jarvis.memory import MemoryError, ROUTING
from jarvis.memory.engine import (
    activate,
    forget_expired,
    list_active,
    provenance_chain,
    reject,
    remember,
    route,
    supersede,
    verify,
)
from jarvis.memory.observe import extract_statements, observe


def test_route_known_kinds():
    assert route("episodic") == "episodic"
    assert route("semantic") == "semantic"
    assert route("procedural") == "procedural"
    assert route("decisions") == "decisions"
    assert route("unknown-kind") == "semantic"  # default fallback


def test_remember_writes_to_routed_subdir(store):
    note = remember(store, "JARVIS prefers Python", kind="semantic", tags=["pref"])
    assert note.document.path.startswith("semantic/")
    assert note.document.path.endswith(".md")
    reread = store.read(note.document.path)
    assert reread.metadata["type"] == "semantic"
    assert reread.metadata["phase"] == "OBSERVED"
    assert reread.metadata["tags"] == ["pref"]
    assert reread.body == "JARVIS prefers Python"


def test_remember_episodic_landing(store):
    note = remember(store, "Deployed at 3pm", kind="episodic")
    assert note.document.path.startswith("episodic/")


def test_phase_transitions_valid_and_invalid(store):
    note = remember(store, "fact", kind="semantic", doc_id="p1")
    rel = note.document.path
    assert verify(store, rel).phase == "VERIFIED"
    assert activate(store, rel).phase == "ACTIVE"
    assert supersede(store, rel).phase == "SUPERSEDED"
    # SUPERSEDED is terminal — no further activation
    with pytest.raises(MemoryError):
        activate(store, rel)


def test_reject_from_candidate(store):
    note = remember(store, "maybe true", kind="semantic", phase="CANDIDATE", doc_id="p2")
    assert reject(store, note.document.path).phase == "REJECTED"


def test_provenance_chain_resolves(store):
    a = remember(store, "base fact", kind="semantic", doc_id="fact-a")
    b = remember(
        store,
        "derived fact",
        kind="semantic",
        doc_id="fact-b",
        provenance={"type": "inference", "based_on": a.document.path},
    )
    chain = provenance_chain(store, b.document.path)
    assert [c["rel"] for c in chain] == [b.document.path, a.document.path]
    assert chain[0]["phase"] == "OBSERVED"


def test_list_active_excludes_nonactive_and_expired(store):
    remember(store, "active one", kind="semantic", phase="ACTIVE", doc_id="act1")
    remember(store, "verified one", kind="semantic", phase="VERIFIED", doc_id="ver1")
    remember(store, "observed one", kind="semantic", doc_id="obs1")

    past = "2000-01-01T00:00:00+00:00"
    remember(store, "expired active", kind="semantic", phase="ACTIVE",
             valid_until=past, doc_id="exp1")

    active = list_active(store)
    titles = [n.document.metadata["title"] for n in active]
    assert "active one" in titles
    assert "verified one" in titles
    assert "observed one" not in titles
    assert "expired active" not in titles


def test_forget_expired_archives_not_deletes(store):
    past = "2000-01-01T00:00:00+00:00"
    note = remember(store, "old news", kind="semantic", phase="ACTIVE",
                    valid_until=past, doc_id="old1")
    future = "2999-01-01T00:00:00+00:00"
    remember(store, "fresh", kind="semantic", phase="ACTIVE",
             valid_until=future, doc_id="new1")

    archived = forget_expired(store, dry_run=True)
    assert note.document.path in archived

    archived = forget_expired(store)
    assert note.document.path in archived
    # Retained (not deleted) but superseded
    doc = store.read(note.document.path)
    assert doc.metadata["phase"] == "SUPERSEDED"
    assert "new1" not in [p for p in archived]


def test_remember_duplicate_id_rejected(store):
    remember(store, "first", kind="semantic", doc_id="dupe")
    with pytest.raises(StoreError):
        remember(store, "second", kind="semantic", doc_id="dupe")


# ---------------------------------------------------------------------------
# observe() — transcript routing
# ---------------------------------------------------------------------------
def test_extract_statements_classify():
    transcript = [
        "I prefer concise answers.",
        "We decided to use PostgreSQL.",
        "Always verify before commit.",
        "I think this might work.",
        "Deployed the update yesterday.",
        "Plain factual statement.",
    ]
    exts = extract_statements("\n".join(transcript))
    by_text = {e.text: e for e in exts}
    assert by_text["I prefer concise answers."].kind == "semantic"
    assert by_text["We decided to use PostgreSQL."].kind == "decisions"
    assert by_text["Always verify before commit."].kind == "procedural"
    assert by_text["I think this might work."].kind == "semantic"
    assert by_text["I think this might work."].phase == "CANDIDATE"
    assert by_text["Deployed the update yesterday."].kind == "episodic"


def test_observe_writes_routed_notes(store):
    created = observe(
        store,
        "I prefer concise answers.\nWe decided to use SQLite.\n",
        session_id="sess-1",
    )
    assert len(created) == 2
    kinds = {p.split("/")[0] for p in created}
    assert "semantic" in kinds
    assert "decisions" in kinds
    # All notes carry provenance + actor
    for rel in created:
        doc = store.read(rel)
        assert doc.metadata["actor"] == "user"
        assert doc.metadata["provenance"]["session_id"] == "sess-1"