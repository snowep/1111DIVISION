"""Tests for CRUD operations and path confinement."""
import pytest

from jarvis.docstore.store import DocumentStore, StoreError


def test_create_and_read(store):
    doc = store.create("note", "Hello", body="world", metadata={"tags": ["greet"]})
    assert doc.path == "note/hello.md" or doc.path.endswith(".md")
    reread = store.read(doc.path)
    assert reread.metadata["title"] == "Hello"
    assert reread.metadata["kind"] == "note"
    assert reread.metadata["tags"] == ["greet"]
    assert reread.body == "world"


def test_duplicate_create_rejected(store):
    rel = store.create("note", "A", doc_id="dup").path
    with pytest.raises(StoreError):
        store.create("note", "B", doc_id="dup")
    assert store.read(rel).metadata["title"] == "A"


def test_read_missing(store):
    with pytest.raises(StoreError):
        store.read("note/does-not-exist.md")


def test_update_body_and_title(store):
    rel = store.create("note", "Old", body="old body", doc_id="upd").path
    store.update(rel, body="new body", title="New")
    doc = store.read(rel)
    assert doc.metadata["title"] == "New"
    assert doc.body == "new body"


def test_update_preserves_id_and_kind(store):
    rel = store.create("note", "A", doc_id="keep").path
    store.update(rel, metadata={"id": "hacked", "kind": "evil", "extra": 1})
    doc = store.read(rel)
    assert doc.metadata["id"] == "keep"
    assert doc.metadata["kind"] == "note"
    assert doc.metadata["extra"] == 1


def test_delete(store):
    rel = store.create("note", "Bye", doc_id="del").path
    store.delete(rel)
    assert rel not in store.list_documents()
    with pytest.raises(StoreError):
        store.read(rel)


def test_list_filters_by_kind(store):
    store.create("note", "N1")
    store.create("note", "N2")
    store.create("proj", "P1")
    assert len(store.list_documents("note")) == 2
    assert len(store.list_documents("proj")) == 1
    assert len(store.list_documents()) == 3


@pytest.mark.parametrize("bad", ["../escape.md", "a/../../x.md", "/abs.md"])
def test_path_traversal_blocked(store, bad):
    store.create("note", "safe")
    with pytest.raises(StoreError):
        store.read(bad)
    with pytest.raises(StoreError):
        store.delete(bad)


def test_windows_style_traversal_blocked(store):
    store.create("note", "safe")
    with pytest.raises(StoreError):
        store.read("..\\escape.md")


def test_invalid_kind_rejected(store):
    with pytest.raises(StoreError):
        store.create("../evil", "X")


def test_invalid_id_rejected(store):
    with pytest.raises(StoreError):
        store.create("note", "X", doc_id="../evil")