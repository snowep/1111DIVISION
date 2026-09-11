"""Tests for the deterministic learning pass."""
import json

from jarvis.learn.engine import build_index, learn


def test_learn_builds_index_and_lessons(store):
    store.create("note", "Alpha", body="## Lessons\n- Always verify.", metadata={"tags": ["a"]})
    store.create("proj", "Beta", body="no lessons here")
    index = learn(store)

    assert index["document_count"] == 2
    assert index["kinds"] == {"note": 1, "proj": 1}
    assert index["tags"] == {"a": 1}

    index_json = (store.learn_dir / "index.json").read_text(encoding="utf-8")
    assert json.loads(index_json) == index

    lessons_md = (store.learn_dir / "lessons.md").read_text(encoding="utf-8")
    assert "Always verify." in lessons_md
    assert "a: 1" in lessons_md


def test_learn_is_rebuildable_and_deterministic(store):
    for i in range(3):
        store.create("note", f"N{i}", doc_id=f"n{i}")
    first = learn(store)
    second = learn(store)
    assert first == second


def test_lessons_ignored_outside_lessons_section(store):
    store.create("note", "C", body="- not a lesson\n## Lessons\n- real lesson")
    index = learn(store)
    md = (store.learn_dir / "lessons.md").read_text(encoding="utf-8")
    assert "real lesson" in md
    assert "not a lesson" not in md