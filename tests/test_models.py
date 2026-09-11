"""Tests for frontmatter parsing/rendering and the Document model."""
import pytest

from jarvis.docstore.models import Document, DocError, parse_document, render_document


def test_parse_roundtrip():
    text = [
        "---",
        "id: abc-123",
        "kind: note",
        "count: 3",
        "ratio: 0.5",
        "ok: true",
        "tags: [alpha, beta]",
        "empty: null",
        "---",
        "",
        "Body line one.",
        "",
        "Body line two.",
    ]
    doc = parse_document("note/a.md", "\n".join(text) + "\n")
    assert doc.path == "note/a.md"
    assert doc.metadata["id"] == "abc-123"
    assert doc.metadata["count"] == 3
    assert doc.metadata["ratio"] == 0.5
    assert doc.metadata["ok"] is True
    assert doc.metadata["tags"] == ["alpha", "beta"]
    assert doc.metadata["empty"] is None
    assert doc.body == "Body line one.\n\nBody line two."


def test_parse_missing_frontmatter():
    with pytest.raises(DocError):
        parse_document("note/a.md", "no frontmatter here\n")


def test_parse_unterminated_frontmatter():
    with pytest.raises(DocError):
        parse_document("note/a.md", "---\nid: abc\n")


def test_parse_bad_line():
    with pytest.raises(DocError):
        parse_document("note/a.md", "---\nthis line has no colon\n---\n")


def test_render_roundtrip_preserves_content():
    doc = Document(
        path="note/a.md",
        metadata={"id": "a", "kind": "note", "tags": ["x", "y"]},
        body="Hello **world**.",
    )
    text = render_document(doc)
    reparsed = parse_document("note/a.md", text)
    assert reparsed.metadata == doc.metadata
    assert reparsed.body == doc.body