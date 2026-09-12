"""Phase 10 kernel tests: path confinement, parsing, identity, context,
validation, mutation boundary, determinism.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from jarvis.context.builder import (AssembledContext, ContextBuilder,
                                    LAYER_PRIORITY)
from jarvis.core.identity import Identity, load_identity
from jarvis.errors import (AuthorizationError, BrokenRefError,
                           ContextError, CorruptStateError, DuplicateIdError,
                           EscapeError, IdentityError, InvalidStatusError,
                           MissingFieldError, MutationDeniedError,
                           NotFoundError, ParseError)
from jarvis.io.workspace import Authority, SafeIO, WorkspaceResolver
from jarvis.models.operation import OperationResult
from jarvis.runtime.kernel import Runtime, build_runtime
from jarvis.runtime.roots import resolve_root
from jarvis.validation.loader import (LoadedDocument, ValidationRules,
                                      load_all, load_document, validate_refs)


# --------------------------------------------------------------------------
# Fixtures: a realistic .jarvis tree with core/identity, vault, council
# --------------------------------------------------------------------------
def _make_tree(tmp_path: Path) -> Path:
    root = tmp_path / "ws"
    jarvis = root / ".jarvis"
    (jarvis / "core").mkdir(parents=True)
    (jarvis / "vault" / "episodic").mkdir(parents=True)
    (jarvis / "vault" / "decisions").mkdir(parents=True)
    (jarvis / "vault" / "semantic").mkdir(parents=True)
    (jarvis / "council").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "src").mkdir()
    (root / "tests").mkdir()

    (jarvis / "core" / "identity.json").write_text(
        json.dumps({
            "name": "JARVIS",
            "role": "personal-intelligence-os",
            "version": "0.2.0",
            "capabilities": ["memory", "skills", "context"],
        }),
        encoding="utf-8",
    )
    return root


@pytest.fixture
def tree(tmp_path):
    return _make_tree(tmp_path)


@pytest.fixture
def runtime(tree) -> Runtime:
    return build_runtime(tree)


# --------------------------------------------------------------------------
# 1. Path confinement
# --------------------------------------------------------------------------
def test_resolve_blocks_traversal(runtime):
    with pytest.raises(EscapeError):
        runtime.resolver.resolve("../../etc/passwd")
    with pytest.raises(EscapeError):
        runtime.resolver.resolve("../outside.txt")
    with pytest.raises(EscapeError):
        runtime.resolver.resolve("C:\\Windows\\system32")


@pytest.mark.parametrize("rel", ["vault/episodic/a.md", "docs/README.md", "nested/deep/file.md"])
def test_resolve_stays_inside_root(runtime, rel):
    target = runtime.resolver.resolve(rel)
    assert target.is_relative_to(runtime.root)


def test_resolve_absolute_rejected(runtime):
    with pytest.raises(EscapeError):
        runtime.resolver.resolve(str(runtime.root / "x.md"))


def test_resolve_missing_raises_not_found(runtime):
    with pytest.raises(NotFoundError):
        runtime.resolver.resolve_read("vault/episodic/does-not-exist.md")


# --------------------------------------------------------------------------
# 2. Parsing (frontmatter -> typed)
# --------------------------------------------------------------------------
def test_parse_and_validate_docstore_document(runtime):
    doc_path = runtime.resolver.resolve("vault/episodic/hello.md")
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text("---\nid: hello\nkind: episodic\ntitle: Hello\nphase: ACTIVE\n---\nHello body\n", encoding="utf-8")
    loaded = load_document(
        runtime.roots.vault,
        "episodic/hello.md",
    )
    assert loaded.metadata["id"] == "hello"
    assert loaded.body == "Hello body"


def test_parse_raises_on_missing_frontmatter(tree):
    from jarvis.docstore.store import DocumentStore
    target = tree / ".jarvis" / "vault" / "episodic" / "bad.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("no frontmatter anywhere\n", encoding="utf-8")
    store = DocumentStore(tree / ".jarvis")
    with pytest.raises(ParseError):
        load_document(store, "episodic/bad.md")


# --------------------------------------------------------------------------
# 3. YAML validation (MissingField, DuplicateId, InvalidStatus, BrokenRef)
# --------------------------------------------------------------------------
def _write(tree: Path, rel: str, meta: dict, body: str = ""):
    target = tree / ".jarvis" / "vault" / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, str):
            lines.append(f"{k}: {v}")
        elif isinstance(v, list):
            lines.append(f"{k}:")
            for item in v:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    lines.append(body)
    target.write_text("\n".join(lines), encoding="utf-8")


def test_missing_field_raises(tree):
    _write(tree, "episodic/a.md", {"id": "a", "kind": "episodic"})  # missing title
    store = _store_from(tree)
    with pytest.raises(MissingFieldError):
        load_document(store, "episodic/a.md")


def test_duplicate_id_raises(tree):
    _write(tree, "episodic/a.md", {"id": "dup", "kind": "episodic", "title": "A"})
    _write(tree, "episodic/b.md", {"id": "dup", "kind": "episodic", "title": "B"})
    store = _store_from(tree)
    with pytest.raises(DuplicateIdError):
        load_all(store)


def test_invalid_status_raises(tree):
    _write(tree, "decisions/d.md", {"id": "d1", "kind": "decisions", "title": "D",
                                    "status": "BOGUS"})
    store = _store_from(tree)
    rules = ValidationRules(required=("id", "kind", "title"),
                            statuses=("OBSERVED", "VERIFIED", "ACTIVE", "SUPERSEDED"))
    with pytest.raises(InvalidStatusError):
        load_document(store, "decisions/d.md", rules=rules)


def test_broken_ref_raises(tree):
    _write(tree, "episodic/a.md", {"id": "a", "kind": "episodic", "title": "A",
                                   "based_on": "episodic/missing.md"})
    store = _store_from(tree)
    loaded = load_document(store, "episodic/a.md")
    rules = ValidationRules(ref_fields=("based_on",))
    with pytest.raises(BrokenRefError):
        validate_refs(loaded, rules, known_paths={"episodic/a.md"})


# --------------------------------------------------------------------------
# 4. Context ordering (lower never overrides higher)
# --------------------------------------------------------------------------
def test_context_order_is_canonical():
    b = ContextBuilder()
    b.add("user", "user instruction")
    b.add("platform", "platform constraints")
    b.add("memory", "memory content")
    b.add("skills", "skill content")
    ctx = b.build()
    prios = [l.priority for l in ctx.layers]
    assert prios == sorted(prios)
    assert ctx.get("platform").priority < ctx.get("memory").priority
    assert ctx.get("user").priority > ctx.get("platform").priority


def test_context_apply_override_higher_layer_raises():
    b = ContextBuilder()
    b.add("memory", "old memory")
    b.add("platform", "platform constraints")
    # 'user' is a lower layer (higher index) than 'memory'
    with pytest.raises(ContextError):
        b.apply_override("memory", "user tries to override memory", caller="user")
    assert b.get("memory").content == "old memory"


def test_context_override_same_level_ok():
    b = ContextBuilder()
    b.add("memory", "old memory")
    b.apply_override("memory", "new memory", caller="memory")
    assert b.get("memory").content == "new memory"


def test_context_text_order_highest_first():
    b = ContextBuilder()
    b.add("user", "USER")
    b.add("platform", "PLATFORM")
    b.add("constitution", "CONSTITUTION")
    ctx = b.build()
    text = ctx.text
    assert text.index("PLATFORM") < text.index("CONSTITUTION") < text.index("USER")


# --------------------------------------------------------------------------
# 5. Identity loading (from .jarvis/core only)
# --------------------------------------------------------------------------
def test_identity_loaded_from_core(runtime):
    assert runtime.identity.name == "JARVIS"
    assert runtime.identity.role == "personal-intelligence-os"
    assert runtime.identity.version == "0.2.0"


def test_identity_missing_raises(tmp_path):
    root = tmp_path / "ws"
    (root / ".jarvis").mkdir(parents=True)
    with pytest.raises(IdentityError):
        build_runtime(root)


def test_identity_never_from_env():
    # identity only comes from .jarvis/core; env vars must not matter
    import os
    os.environ["JARVIS_IDENTITY_NAME"] = "HACKED"
    # build_runtime with a tree that has no core -> still IdentityError
    import tempfile
    root = Path(tempfile.mkdtemp())
    (root / ".jarvis").mkdir(parents=True)
    with pytest.raises(IdentityError):
        build_runtime(root)


# --------------------------------------------------------------------------
# 6. Read/write boundary (no mutation without authority)
# --------------------------------------------------------------------------
def test_write_without_authority_denied(runtime):
    with pytest.raises(MutationDeniedError):
        runtime.io.write_text("vault/episodic/new.md", "---\nid: n\n---\n")


def test_write_with_authority_allowed(runtime):
    auth = Authority(kind="identity", name=runtime.identity.name,
                     scope=str(runtime.root))
    target = runtime.io.write_text("vault/episodic/with-auth.md",
                                   "---\nid: auth\nkind: episodic\ntitle: T\n---\nbody",
                                   authority=auth)
    assert target.is_file()


def test_write_authority_outside_scope_denied(runtime):
    auth = Authority(kind="identity", name=runtime.identity.name,
                     scope=str(runtime.roots.jarvis))  # limited to .jarvis
    with pytest.raises(MutationDeniedError):
        runtime.io.write_text("docs/new.md", "x", authority=auth)


# --------------------------------------------------------------------------
# 7. OperationResult
# --------------------------------------------------------------------------
def test_operation_result_ok():
    r = OperationResult.ok("test-op", "op-1", data={"k": "v"}, warnings=["w1"])
    assert r.success is True
    assert r.operation_id == "op-1"
    assert r.data == {"k": "v"}
    assert r.errors == []


def test_operation_result_fail_typed():
    from jarvis.errors import EscapeError
    r = OperationResult.fail("read", "op-2", EscapeError("escaped", path="x"))
    assert r.success is False
    assert r.error_codes == ["PATH_ESCAPE"]


def test_operation_result_deterministic_serialization():
    r1 = OperationResult.ok("op", "id", data=[1, 2, 3])
    r2 = OperationResult.ok("op", "id", data=[1, 2, 3])
    assert r1.to_dict() == r2.to_dict()


# --------------------------------------------------------------------------
# 8. Determinism
# --------------------------------------------------------------------------
def test_context_builder_is_deterministic():
    b1 = ContextBuilder()
    b1.add("user", "u"); b1.add("platform", "p"); b1.add("memory", "m")
    b2 = ContextBuilder()
    b2.add("user", "u"); b2.add("platform", "p"); b2.add("memory", "m")
    assert b1.build().text == b2.build().text


def test_runtime_smoke(runtime):
    d = runtime.to_dict()
    assert d["identity"]["name"] == "JARVIS"
    assert d["root"] == str(runtime.root)


def _store_from(tree):
    from jarvis.docstore.store import DocumentStore
    return DocumentStore(tree / ".jarvis")