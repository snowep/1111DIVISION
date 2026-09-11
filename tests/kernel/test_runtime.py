"""Tests for jarvis.runtime — bounded operation executor.

Area 7: every operation returns OperationResult; never raises; never mutates
outside authority.
"""

import pytest

from jarvis.models import OperationResult
from jarvis.runtime.operations import (
    execute_read_document,
    execute_load_identity,
    execute_build_context,
    execute_validate_memory,
    execute_run_gate,
    execute_prepare_mutation,
    OperationList,
)
from jarvis.models.memory import MemoryRecord


def _make_memory_rec(**overrides):
    base = dict(
        id="MEM-X",
        type="user-preference",
        status="active",
        confidence=0.9,
        authority="user-explicit",
        approval="explicit",
        source="user-statement",
        actor="user",
        scope="global",
        created="2026-01-01",
        valid_from="2026-01-01",
        valid_until="2027-01-01",
        supersedes=None,
        related=(),
        content="Body",
        provenance={},
        metadata={},
        source_path=".jarvis/memory/active/MEM-X.md",
    )
    base.update(overrides)
    return MemoryRecord(**base)


class TestReadDocument:
    def test_ok(self, workspace):
        r = execute_read_document(workspace, ".jarvis/personas/definitions/security-architect.md")
        assert r.success is True
        assert r.operation_id == "read_document"
        doc = r.data
        assert doc.metadata["id"] == "persona.security-architect"

    def test_ok_non_frontmatter(self, workspace):
        r = execute_read_document(workspace, ".jarvis/core/constitution.md")
        assert r.success is True
        doc = r.data
        assert doc.has_frontmatter is False

    def test_missing_returns_failure(self, workspace):
        r = execute_read_document(workspace, "not/here.md")
        assert r.success is False
        assert r.operation_id == "read_document"


class TestLoadIdentity:
    def test_ok(self, workspace):
        r = execute_load_identity(workspace)
        assert r.success is True
        assert r.data.name == "JARVIS"

    def test_provenance(self, workspace):
        r = execute_load_identity(workspace)
        assert r.provenance["action"] == "load_identity"


class TestBuildContext:
    def test_ok(self, workspace):
        r = execute_build_context(workspace, user_request="Do something")
        assert r.success is True
        ctx = r.data
        assert ctx.layer_count >= 4
        assert ctx.get_layer(1) is not None
        assert ctx.get_layer(9) is not None
        assert ctx.current_value("user_request.active") is True

    def test_with_memory_and_skills(self, workspace):
        rec = _make_memory_rec()
        skill = type("Skill", (), {"id": "SKL-1", "name": "Research"})()
        r = execute_build_context(
            workspace,
            memory_records=[rec],
            skills=[skill],
            task_content="Write a plan",
        )
        assert r.success is True
        ctx = r.data
        assert ctx.get_layer(5) is not None   # memory
        assert ctx.get_layer(6) is not None   # skills
        assert ctx.get_layer(7) is not None   # task context

    def test_persona_overlay(self, workspace):
        r = execute_build_context(
            workspace,
            persona_overlay=("persona.security-architect", "you are paranoid"),
            user_request="Review",
        )
        assert r.success is True
        ctx = r.data
        layer8 = ctx.get_layer(8)
        assert layer8 is not None
        assert layer8.metadata["persona_id"] == "persona.security-architect"

    def test_immutable_constitution_present(self, workspace):
        r = execute_build_context(workspace)
        ctx = r.data
        layer2 = ctx.get_layer(2)
        assert layer2.immutable is True
        assert "Constitution" in layer2.content


class TestValidateMemory:
    def test_valid_batch(self):
        r = execute_validate_memory([_make_memory_rec()])
        assert r.success is True
        assert r.data == {"validated": 1}

    def test_invalid_batch(self):
        bad = _make_memory_rec(confidence="high")  # wrong type
        r = execute_validate_memory([bad])
        assert r.success is False

    def test_invalid_multiple_errors(self):
        bad = _make_memory_rec(confidence="high", source=None)
        r = execute_validate_memory([bad])
        assert r.success is False
        assert len(r.errors) == 1  # MissingFieldError aggregates


class TestRunGate:
    def test_valid_candidate(self):
        candidate = {
            "id": "MEM-NEW",
            "type": "user-preference",
            "status": "candidate",
            "source": "user-statement",
            "confidence": 0.8,
            "authority": "user-explicit",
            "approval": "explicit",
            "actor": "user",
            "scope": "global",
            "created": "2026-01-01",
            "valid_from": "2026-01-01",
            "valid_until": "2027-01-01",
            "supersedes": "MEM-000",
            "related": ["MEM-001"],
        }
        r = execute_run_gate(candidate)
        assert r.success is True
        assert r.data["gated"] is True

    def test_missing_required_fails(self):
        with pytest.raises(Exception):
            execute_run_gate({"id": "MEM-NEW"})

    def test_invalid_status_fails(self):
        candidate = {
            "id": "MEM-NEW",
            "type": "user-preference",
            "status": "flying",
            "source": "user",
            "confidence": 0.8,
            "authority": "user-explicit",
            "approval": "explicit",
            "actor": "user",
            "scope": "global",
            "created": "2026-01-01",
            "valid_from": "2026-01-01",
            "valid_until": "2027-01-01",
            "supersedes": "",
            "related": [],
        }
        with pytest.raises(Exception):
            execute_run_gate(candidate)


class TestPrepareMutation:
    def test_ok(self, workspace):
        r = execute_prepare_mutation(
            workspace, "docs/plan.md", "# Plan\n\nBody.", expected_hash=None
        )
        assert r.success is True
        assert r.data["dry_run"] is True
        assert r.data["candidate"] == "docs/plan.md"

    def test_refused_non_canonical(self, workspace, tmp_path):
        outside = tmp_path / "outside.md"
        r = execute_prepare_mutation(workspace, str(outside), "evil")
        assert r.success is False
        assert "authority" in r.error_codes[0]


class TestOperationList:
    def test_registry(self):
        assert OperationList.operations["read_document"] is execute_read_document
        assert OperationList.operations["load_identity"] is execute_load_identity
        assert OperationList.operations["build_context"] is execute_build_context
        assert OperationList.operations["validate_memory"] is execute_validate_memory
        assert OperationList.operations["run_gate"] is execute_run_gate
        assert OperationList.operations["prepare_mutation"] is execute_prepare_mutation