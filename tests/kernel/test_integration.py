"""Integration tests against the real repository.

Area 8: the kernel operations execute against the actual JARVIS repo —
reading real identity, constitution, memory, and building a context.
These tests must pass against the live project state, not just fixtures.

NOTE: These tests are guarded to be read-only; they never mutate the repo.
"""

import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def real_workspace():
    from jarvis.io.workspace import Workspace
    return Workspace(REPO_ROOT)


class TestRealRepository:
    def test_repo_has_git(self):
        assert (REPO_ROOT / ".git").exists()

    def test_workspace_detected(self, real_workspace):
        assert real_workspace.root == REPO_ROOT.resolve()

    def test_real_identity_loads(self, real_workspace):
        from jarvis.core.identity import load_identity
        ident = load_identity(real_workspace)
        assert ident.name == "JARVIS"
        assert ident.source_path.endswith("identity.md")

    def test_real_constitution_loadable(self, real_workspace):
        from jarvis.core.document import load_document
        doc = load_document(real_workspace, ".jarvis/core/constitution.md")
        assert len(doc.body) > 100

    def test_real_memory_loadable(self, real_workspace):
        from jarvis.core.document import load_documents
        docs, errors = load_documents(
            real_workspace, ".jarvis/memory/**/*.md", validate_schemas=False
        )
        assert len(docs) >= 1

    def test_real_persona_loadable(self, real_workspace):
        from jarvis.core.document import load_documents
        docs, errors = load_documents(real_workspace, ".jarvis/personas/definitions/*.md")
        assert len(docs) >= 1

    def test_real_context_build(self, real_workspace):
        from jarvis.runtime.operations import execute_build_context
        r = execute_build_context(real_workspace, user_request="Run self-diagnostics")
        assert r.success is True
        ctx = r.data
        assert ctx.layer_count >= 4
        # Constitution and identity should have real content
        assert len(ctx.get_layer(2).content) > 100

    def test_real_identity_operation(self, real_workspace):
        from jarvis.runtime.operations import execute_load_identity
        r = execute_load_identity(real_workspace)
        assert r.success is True
        assert r.data.name == "JARVIS"

    def test_real_read_document(self, real_workspace):
        from jarvis.runtime.operations import execute_read_document
        r = execute_read_document(real_workspace, ".jarvis/core/world-model.md")
        assert r.success is True
        assert len(r.data.body) > 0