"""Tests for jarvis.models — data models.

Area 2: OperationResult, ContextLayer/RuntimeContext, MarkdownDocument,
Identity, MemoryRecord — construction + key invariants.
"""

import pytest

from jarvis.models import (
    OperationResult,
    ContextLayer,
    LayerAssertion,
    RuntimeContext,
    MarkdownDocument,
    Identity,
    MemoryRecord,
)
from jarvis.errors import JarvisError, LayerOverrideError


# ---------- OperationResult ----------


class TestOperationResult:
    def test_ok(self):
        r = OperationResult.ok("read_document", data={"x": 1})
        assert r.success is True
        assert r.is_ok is True
        assert r.operation_id == "read_document"
        assert r.data == {"x": 1}
        assert r.errors == ()
        assert r.error_codes == ()

    def test_fail(self):
        err = JarvisError("nope", path="a.md", code="bad")
        r = OperationResult.fail("read_document", error=err)
        assert r.success is False
        assert r.is_ok is False
        assert r.data is None
        assert r.error_codes == ("jarvis.error",)

    def test_fail_tuple(self):
        e1 = JarvisError("one")
        e2 = JarvisError("two")
        r = OperationResult.fail("op", error=(e1, e2))
        assert len(r.errors) == 2

    def test_to_dict(self):
        r = OperationResult.ok("op", data=5, provenance={"a": 1})
        d = r.to_dict()
        assert d["success"] is True
        assert d["operation_id"] == "op"
        assert d["data"] == 5
        assert d["errors"] == []
        assert d["provenance"] == {"a": 1}

    def test_merge(self):
        r1 = OperationResult.ok("op", data=1, warnings=("w1",))
        r2 = OperationResult.ok("op", data=2, warnings=("w2",))
        merged = r1.merge(r2)
        assert merged.success is True
        assert merged.warnings == ("w1", "w2")

    def test_merge_failure_poisons(self):
        r1 = OperationResult.ok("op")
        r2 = OperationResult.fail("op", error=JarvisError("x"))
        merged = r1.merge(r2)
        assert merged.success is False
        assert len(merged.errors) == 1


# ---------- ContextLayer / RuntimeContext ----------


class TestContextLayer:
    def test_valid_construction(self):
        layer = ContextLayer(number=4, name="world-model", content="# WM")
        assert layer.number == 4
        assert layer.immutable is False

    def test_immutable_layers_1_to_3(self):
        for n, name in [(1, "platform-constraints"), (2, "constitution"), (3, "system-prompt")]:
            layer = ContextLayer(number=n, name=name)
            assert layer.immutable is True

    def test_invalid_number(self):
        with pytest.raises(ValueError):
            ContextLayer(number=10, name="bogus")

    def test_invalid_name_mismatch(self):
        with pytest.raises(ValueError):
            ContextLayer(number=4, name="constitution")

    def test_outranks(self):
        high = ContextLayer(number=1, name="platform-constraints")
        low = ContextLayer(number=9, name="user-request")
        assert high.outranks(low)
        assert not low.outranks(high)

    def test_can_override(self):
        platform = ContextLayer(number=1, name="platform-constraints")
        world = ContextLayer(number=4, name="world-model")
        user = ContextLayer(number=9, name="user-request")
        assert not world.can_override(platform)   # 4 cannot override immutable 1
        assert user.can_override(world)           # 9 can override 4 (User Request rule)
        assert platform.can_override(user)        # 1 can override 9 (higher outranks)


class TestRuntimeContext:
    def test_add_layer_and_ordered(self):
        ctx = RuntimeContext()
        ctx.add_layer(ContextLayer(number=4, name="world-model", content="wm"))
        ctx.add_layer(ContextLayer(number=1, name="platform-constraints", content="pf"))
        assert ctx.layer_count == 2
        ordered = ctx.ordered_layers()
        assert [l.number for l in ordered] == [1, 4]

    def test_add_layer_name_conflict(self):
        ctx = RuntimeContext()
        ctx.add_layer(ContextLayer(number=4, name="world-model"))
        with pytest.raises(ValueError):
            ctx.add_layer(ContextLayer(number=4, name="memory"))

    def test_assert_value_identical_keeps_higher(self):
        ctx = RuntimeContext()
        ctx.assert_value("phase", "10", layer_number=4)
        ctx.assert_value("phase", "10", layer_number=9)  # same value, no conflict
        assert ctx.assertion_of("phase").layer_number == 4

    def test_assert_value_override_refused(self):
        ctx = RuntimeContext()
        ctx.assert_value("phase", "10", layer_number=4)
        with pytest.raises(LayerOverrideError):
            ctx.assert_value("phase", "11", layer_number=8)  # lower trying override

    def test_user_request_can_override_layer_4(self):
        ctx = RuntimeContext()
        ctx.assert_value("phase", "10", layer_number=4)
        ctx.assert_value("phase", "11", layer_number=9)  # legal override
        assert ctx.current_value("phase") == "11"

    def test_user_request_cannot_override_constitution(self):
        ctx = RuntimeContext()
        ctx.assert_value("truth", "a", layer_number=2)
        with pytest.raises(LayerOverrideError):
            ctx.assert_value("truth", "b", layer_number=9)

    def test_assemble_text_order(self):
        ctx = RuntimeContext()
        ctx.add_layer(ContextLayer(number=4, name="world-model", content="WM"))
        ctx.add_layer(ContextLayer(number=1, name="platform-constraints", content="PF"))
        text = ctx.assemble_text()
        assert text.index("LAYER 1") < text.index("LAYER 4")
        assert "[immutable]" in text


# ---------- MarkdownDocument ----------


class TestMarkdownDocument:
    def test_fields(self):
        doc = MarkdownDocument(
            source_path="a/b.md",
            relative_path="a/b.md",
            metadata={"id": "X-1"},
            body="# Hello",
            has_frontmatter=True,
        )
        assert doc.source_path == "a/b.md"
        assert doc.metadata["id"] == "X-1"
        assert doc.has_frontmatter is True


# ---------- Identity ----------


class TestIdentity:
    def test_fields(self):
        ident = Identity(
            name="JARVIS",
            role="PIOS",
            primary_user="operator",
            nature="kernel",
            core_purpose="assist",
            philosophy="truth",
            personality=("calm", "precise"),
            persona_constraints=("no fabrication",),
            source_path=".jarvis/core/identity.md",
        )
        assert ident.name == "JARVIS"
        assert ident.personality == ("calm", "precise")
        assert ident.persona_constraints == ("no fabrication",)


# ---------- MemoryRecord ----------


class TestMemoryRecord:
    def test_fields(self):
        rec = MemoryRecord(
            id="MEM-TEST-001",
            type="user-preference",
            status="active",
            confidence=0.9,
            authority="user-explicit",
            approval="explicit",
            source="user-statement",
            actor="user",
            scope="global",
            created="2026-09-11",
            valid_from="2026-09-11",
            valid_until="2027-09-11",
            supersedes=None,
            related=("MEM-OLD-1",),
            content="Body",
            provenance={"origin": "chat"},
            metadata={"id": "MEM-TEST-001"},
            source_path=".jarvis/memory/active/MEM-TEST-001.md",
        )
        assert rec.id == "MEM-TEST-001"
        assert rec.related == ("MEM-OLD-1",)
        assert rec.confidence == 0.9