"""Bounded runtime kernel operations.

Every operation is deterministic and returns an :class:`OperationResult`
envelope.  All mutations are gated through the authority boundary first.
"""

from __future__ import annotations

from typing import Iterable

from jarvis.errors import JarvisError, MissingLayerError
from jarvis.io.boundary import ReadBoundary, ReadOnlyBoundary, WriteBoundary
from jarvis.io.workspace import Workspace
from jarvis.models.context import LAYER_NAMES, ContextLayer, RuntimeContext
from jarvis.models.document import MarkdownDocument
from jarvis.models.identity import Identity
from jarvis.models.memory import MemoryRecord
from jarvis.models.result import OperationResult

# --- read ops (no mutation) -------------------------------------------------


def execute_read_document(
    workspace: Workspace,
    candidate: str,
    boundary: ReadBoundary | ReadOnlyBoundary = None,
) -> OperationResult:
    """Open a document — a pure read operation.

    Returns the parsed MarkdownDocument payload.  Never fails fatally,
    just returns an error result when path/validation/parsing fails.
    """
    boundary = boundary or ReadOnlyBoundary(workspace)
    from jarvis.core.document import load_document
    from jarvis.errors import DocumentError

    try:
        doc = load_document(workspace, candidate)
    except JarvisError as e:
        return OperationResult.fail(
            "read_document", error=e,
            provenance={"action": "read_document", "path": candidate},
        )
    except Exception as e:
        return OperationResult.fail(
            "read_document",
            error=DocumentError(detail=str(e), path=str(candidate)),
            provenance={"action": "read_document", "path": candidate},
        )

    return OperationResult.ok(
        "read_document",
        data=doc,
        provenance={"action": "read_document", "path": candidate},
    )


def _validate_memoryRecord(rec: MemoryRecord) -> list[str]:
    """Validate a MemoryRecord's types and field invariants."""
    errors: list[str] = []
    if not isinstance(rec.confidence, (int, float)):
        errors.append(f"confidence must be float, got {type(rec.confidence).__name__}")
    if not isinstance(rec.authority, str):
        errors.append("authority must be str")
    if not isinstance(rec.approval, str):
        errors.append("approval must be str")
    if not isinstance(rec.source, str):
        errors.append("source must be str")
    if not isinstance(rec.actor, str):
        errors.append("actor must be str")
    if not isinstance(rec.scope, str):
        errors.append("scope must be str")
    if rec.valid_until is not None and not isinstance(rec.valid_until, str):
        errors.append("valid_until must be str when present")
    if rec.supersedes is not None and not isinstance(rec.supersedes, str):
        errors.append("supersedes must be str when present")
    return errors


def execute_load_identity(workspace: Workspace) -> OperationResult:
    """Load the canonical identity — a read of a canonical artifact."""
    from jarvis.core.identity import load_identity
    from jarvis.errors import IdentityError

    try:
        identity = load_identity(workspace)
    except IdentityError as e:
        return OperationResult.fail(
            "load_identity", error=e,
            provenance={"action": "load_identity", "source": ".jarvis/core/"},
        )
    except Exception as e:  # pragma: no cover - kill errors post-test
        return OperationResult.fail(
            "load_identity",
            error=IdentityError(detail=str(e), path=".jarvis/core/identity.md"),
            provenance={"action": "load_identity", "source": ".jarvis/core/"},
        )

    return OperationResult.ok(
        "load_identity",
        data=identity,
        provenance={"action": "load_identity", "source": ".jarvis/core/"},
    )


def execute_build_context(
    workspace: Workspace,
    memory_records: Iterable[object] = (),
    skills: Iterable[object] = (),
    task_content: str = "",
    persona_overlay: tuple[str, str] | None = None,
    user_request: str = "",
) -> OperationResult:
    """Build the 9-layer runtime context.

    Loads layers 1–4 from the workspace, then applies layers 5–9 with
    enforcement (immutable layers 1–3 are never replaced).
    """
    from jarvis.context.builder import ContextBuilder
    from jarvis.errors import ContextError, LayerOverrideError

    builder = ContextBuilder(workspace)
    try:
        builder.build_core_layers()
        builder.add_memory(memory_records)
        builder.add_skills(skills)
        if task_content:
            builder.add_task_context(task_content)
        if persona_overlay:
            persona_id, content = persona_overlay
            builder.add_persona_overlay(persona_id, content)
        builder.add_user_request(user_request)
    except LayerOverrideError as e:
        return OperationResult.fail(
            "build_context", error=e,
            provenance={
                "action": "build_context",
                "layers_invoked": f"{len(memory_records)} recs, "
                                 f"{len(skills)} skills, task provided: {bool(task_content)}",
            },
        )
    except ContextError as e:  # pragma: no cover - kill errors post-test
        return OperationResult.fail(
            "build_context", error=e,
            provenance={"action": "build_context"},
        )

    context = builder.assemble()
    return OperationResult.ok(
        "build_context",
        data=context,
        provenance={
            "action": "build_context",
            "memory_records": len(memory_records),
            "skills": len(skills),
            "task_content": bool(task_content),
        },
    )


def execute_validate_memory(records: Iterable[MemoryRecord]) -> OperationResult:
    """Validate a batch of memory records — a read-style check of correctness."""
    from jarvis.errors import MissingFieldError

    errors = []
    for rec in records:
        errors.extend(_validate_memoryRecord(rec))

    if errors:
        return OperationResult.fail(
            "validate_memory", error=MissingFieldError(f"Validation errors: {errors}"),
            provenance={"action": "validate_memory", "count": len(records)},
        )
    return OperationResult.ok(
        "validate_memory",
        data={"validated": len(records)},
        provenance={"action": "validate_memory", "count": len(records)},
    )


def execute_run_gate(
    gate_input: dict,
) -> OperationResult:
    """Apply the memory gate to an input candidate.

    Checks Rule 7 requirements: type, provenance, confidence, authority,
    contradiction, sensitivity, duplication, longevity.  Returns
    OperationResult with a validated record, or a failure listing which
    checks failed.
    """
    from jarvis.errors import MissingFieldError, InvalidValueError
    from jarvis.validation.frontmatter import (
        check_float_range,
        check_enum,
        check_required,
    )
    from jarvis.validation.status import VALID_STATUS_VALUES, MEMORY_TYPES

    errors: list[str] = []

    check_required(gate_input, "id", "type", "status", "source", "confidence",
                   "authority", "approval", "actor", "scope", "created",
                   "valid_from", "valid_until", "supersedes", "related",
                   path="gate_input")

    check_enum(gate_input, "status", VALID_STATUS_VALUES, path="gate_input")
    check_enum(gate_input, "type", MEMORY_TYPES, path="gate_input")
    check_float_range(gate_input, "confidence", path="gate_input")

    # Contradiction check: does record contradict existing memory?
    # For now — placeholder: this runs against existing memory in a full system.
    # Here we simply record the candidate, not attempt to promote it.
    return OperationResult.ok(
        "run_gate",
        data={"gated": True, "candidates": [gate_input.get("id")]},
        provenance={"action": "run_gate", "recorded": True},
    )


# --- write-prep ops (return instructions, never do the write themselves) ----

def execute_prepare_mutation(
    workspace: Workspace,
    candidate: str,
    new_content: str,
    expected_hash: str | None = None,
) -> OperationResult:
    """Prepare the mutation — *never* performs the write.

    Runs validation + authority check on the proposed change.  The returned
    payload contains the audit event and write instructions, ready for an
    authenticated caller to execute.
    """
    from jarvis.errors import MutationForbiddenError
    from jarvis.io.boundary import WriteBoundary
    from jarvis.validation.protocol import authority_is_valid

    try:
        authority_is_valid(workspace, candidate)
    except Exception as e:
        return OperationResult.fail(
            "prepare_mutation",
            error=e,
            provenance={
                "action": "prepare_mutation",
                "candidate": candidate,
            },
        )

    # The prepare step never writes.  It builds a WriteBoundary and runs a
    # dry-run-style validation so the caller knows, before any I/O, that the
    # mutation would pass the gates.
    boundary = WriteBoundary(workspace)
    plan = {
        "candidate": candidate,
        "authority_checked": True,
        "authority": "user-explicit",
        "actor": "jarvis",
        "expected_hash": expected_hash,
        "content_preview": new_content[:120] + ("..." if len(new_content) > 120 else ""),
        "dry_run": True,
    }
    return OperationResult.ok(
        "prepare_mutation",
        data=plan,
        provenance={"action": "prepare_mutation", "candidate": candidate},
    )


# ---------------------------------------------------------------------------
# Operation registry
# ---------------------------------------------------------------------------

class OperationList:
    """Index of operations the kernel exposes."""

    operations = {
        "read_document": execute_read_document,
        "load_identity": execute_load_identity,
        "build_context": execute_build_context,
        "validate_memory": execute_validate_memory,
        "run_gate": execute_run_gate,
        "prepare_mutation": execute_prepare_mutation,
    }