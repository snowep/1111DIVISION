"""Tests for jarvis.errors — typed error hierarchy.

Area 1: Every error class exists, carries kind/path/code, serializes correctly.
"""

import pytest

from jarvis.errors import (
    JarvisError,
    PathEscapeError,
    PathNotFoundError,
    UnknownAnchorError,
    FrontmatterError,
    MissingFieldError,
    InvalidValueError,
    DuplicateIdError,
    BrokenReferenceError,
    IdentitySourceError,
    IdentityIncompleteError,
    LayerOverrideError,
    MissingLayerError,
    AuthorityDeniedError,
    MutationForbiddenError,
)


# ---------- base class ----------


class TestJarvisError:
    def test_base_kind(self):
        e = JarvisError("something broke")
        assert e.kind == "jarvis.error"
        assert "something broke" in str(e)

    def test_to_dict(self):
        e = JarvisError("msg", path="foo.md", code="bad")
        d = e.to_dict()
        assert d["kind"] == "jarvis.error"
        assert "msg" in d["message"]
        assert d["path"] == "foo.md"
        assert d["code"] == "bad"

    def test_repr(self):
        e = JarvisError("x", path="y")
        r = repr(e)
        assert "JarvisError" in r
        assert "path=" in r


# ---------- path errors ----------


class TestPathErrors:
    def test_escape(self):
        e = PathEscapeError("traversal", path="../x")
        assert e.kind == "path.escape"
        assert e.path == "../x"

    def test_not_found(self):
        e = PathNotFoundError("missing", path="a/b")
        assert e.kind == "path.not_found"

    def test_unknown_anchor(self):
        e = UnknownAnchorError("bad anchor", path="nope")
        assert e.kind == "path.unknown_anchor"


# ---------- document errors ----------


class TestDocumentErrors:
    @pytest.mark.parametrize(
        "cls, expected_kind",
        [
            (FrontmatterError, "document.frontmatter"),
            (MissingFieldError, "document.missing_field"),
            (InvalidValueError, "document.invalid_value"),
            (DuplicateIdError, "document.duplicate_id"),
            (BrokenReferenceError, "document.broken_reference"),
        ],
    )
    def test_kinds(self, cls, expected_kind):
        e = cls("test error", path="test.md", code="c1")
        assert e.kind == expected_kind
        assert e.path == "test.md"
        assert e.code == "c1"


# ---------- identity errors ----------


class TestIdentityErrors:
    def test_source(self):
        e = IdentitySourceError("bad source", path="x.md")
        assert e.kind == "identity.non_canonical_source"

    def test_incomplete(self):
        e = IdentityIncompleteError("missing fields", path="identity.md")
        assert e.kind == "identity.incomplete"


# ---------- context errors ----------


class TestContextErrors:
    def test_layer_override(self):
        e = LayerOverrideError("override rejected", path="key", code="precedence")
        assert e.kind == "context.layer_override"
        assert e.path == "key"

    def test_missing_layer(self):
        e = MissingLayerError("layer 4 not loaded", path="world-model")
        assert e.kind == "context.missing_layer"


# ---------- operation errors ----------


class TestOperationErrors:
    def test_authority_denied(self):
        e = AuthorityDeniedError("refused", path="x.md", code="authority_gate")
        assert e.kind == "operation.authority_denied"

    def test_mutation_forbidden(self):
        e = MutationForbiddenError("read only", code="read_only")
        assert e.kind == "operation.mutation_forbidden"
