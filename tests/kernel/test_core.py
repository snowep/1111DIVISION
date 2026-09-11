"""Tests for jarvis.core — canonical loaders.

Area 5: Markdown/YAML loader, identity loader (canonical-only),
memory records full schema enforcement.
"""

import pytest

from jarvis.core.document import load_document, load_documents
from jarvis.core.identity import load_identity, refuse_non_canonical_identity
from jarvis.core.memory import load_memory_record
from jarvis.errors import (
    DocumentError,
    FrontmatterError,
    IdentityIncompleteError,
    IdentitySourceError,
    MissingFieldError,
    InvalidValueError,
    PathNotFoundError,
)


# ---------- document loader ----------


class TestDocumentLoader:
    def test_load_document_ok(self, workspace):
        doc = load_document(workspace, ".jarvis/personas/definitions/security-architect.md")
        assert doc.metadata["id"] == "persona.security-architect"
        assert doc.metadata["status"] == "active"
        assert "security architect" in doc.body.lower()
        assert doc.has_frontmatter is True

    def test_load_document_missing(self, workspace):
        with pytest.raises(PathNotFoundError):
            load_document(workspace, "no/such/file.md")

    def test_load_document_relative_path(self, workspace):
        doc = load_document(workspace, ".jarvis/core/identity.md")
        assert doc.relative_path == ".jarvis/core/identity.md"

    def test_load_documents_batch(self, workspace):
        docs, errors = load_documents(workspace, ".jarvis/personas/definitions/*.md")
        assert len(docs) == 1
        assert errors == []

    def test_load_documents_missing_pattern(self, workspace):
        docs, errors = load_documents(workspace, "no/such/*.md")
        assert docs == []
        assert errors == []


# ---------- identity loader ----------


class TestIdentityLoader:
    def test_load_identity(self, workspace):
        ident = load_identity(workspace)
        assert ident.name == "JARVIS"
        assert ident.role == "Personal Intelligence Operating System"
        assert ident.primary_user == "the operator"
        assert len(ident.personality) == 3
        assert len(ident.persona_constraints) == 2
        assert ident.source_path.endswith("identity.md")

    def test_load_identity_missing_file(self, workspace, tmp_root):
        (tmp_root / ".jarvis" / "core" / "identity.md").unlink()
        with pytest.raises(PathNotFoundError):
            load_identity(workspace)

    def test_load_identity_incomplete(self, workspace, tmp_root):
        (tmp_root / ".jarvis" / "core" / "identity.md").write_text(
            "# Identity\n\nName: Robot\n", encoding="utf-8"
        )
        with pytest.raises(IdentityIncompleteError):
            load_identity(workspace)

    def test_refuse_non_canonical(self, workspace, tmp_path):
        outside = tmp_path / "identity.md"
        outside.write_text("# Identity", encoding="utf-8")
        with pytest.raises(IdentitySourceError):
            refuse_non_canonical_identity(workspace, str(outside))

    def test_refuse_accepts_canonical(self, workspace):
        # Should not raise
        refuse_non_canonical_identity(workspace, ".jarvis/core/identity.md")


# ---------- memory loader ----------


class TestMemoryLoader:
    def test_load_memory_ok(self, workspace):
        rec = load_memory_record(workspace, ".jarvis/memory/active/MEM-TEST-001.md")
        assert rec.id == "MEM-TEST-001"
        assert rec.type == "user-preference"
        assert rec.status == "active"
        assert rec.confidence == 0.9
        assert rec.actor == "user"
        assert "concise" in rec.content

    def test_load_memory_wrong_location(self, workspace):
        with pytest.raises(DocumentError):
            load_memory_record(workspace, ".jarvis/personas/definitions/security-architect.md")

    def test_load_memory_invalid_status(self, workspace, tmp_root):
        path = tmp_root / ".jarvis" / "memory" / "active" / "MEM-BAD.md"
        path.write_text(
            "---\n"
            "id: MEM-BAD\n"
            "type: user-preference\n"
            "status: flying\n"  # invalid enum
            "source: user\n"
            "confidence: 0.5\n"
            "authority: user-explicit\n"
            "approval: explicit\n"
            "actor: user\n"
            "scope: global\n"
            "created: '2026-01-01'\n"
            "valid_from: '2026-01-01'\n"
            "valid_until: '2027-01-01'\n"
            "supersedes: ''\n"
            "related:\n"
            "  - MEM-OTHER\n"
            "---\n"
            "Body",
            encoding="utf-8",
        )
        with pytest.raises(InvalidValueError):
            load_memory_record(workspace, ".jarvis/memory/active/MEM-BAD.md")

    def test_load_memory_missing_field(self, workspace, tmp_root):
        path = tmp_root / ".jarvis" / "memory" / "active" / "MEM-BAD2.md"
        path.write_text(
            "---\n"
            "id: MEM-BAD2\n"
            "type: user-preference\n"
            # missing status & others
            "source: user\n"
            "---\n"
            "Body",
            encoding="utf-8",
        )
        with pytest.raises(MissingFieldError):
            load_memory_record(workspace, ".jarvis/memory/active/MEM-BAD2.md")

    def test_load_memory_related_must_be_list(self, workspace, tmp_root):
        path = tmp_root / ".jarvis" / "memory" / "active" / "MEM-BAD3.md"
        path.write_text(
            "---\n"
            "id: MEM-BAD3\n"
            "type: user-preference\n"
            "status: active\n"
            "source: user\n"
            "confidence: 0.5\n"
            "authority: user-explicit\n"
            "approval: explicit\n"
            "actor: user\n"
            "scope: global\n"
            "created: '2026-01-01'\n"
            "valid_from: '2026-01-01'\n"
            "valid_until: '2027-01-01'\n"
            "supersedes: ''\n"
            "related: not-a-list\n"
            "---\n"
            "Body",
            encoding="utf-8",
        )
        with pytest.raises(DocumentError):
            load_memory_record(workspace, ".jarvis/memory/active/MEM-BAD3.md")