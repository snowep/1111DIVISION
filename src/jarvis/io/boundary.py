"""Read/write boundary — separates read operations from mutation.

Two boundaries:

- ``ReadBoundary``     — pure read KVM: open/read/list, never writes.
- ``WriteBoundary``    — a defensive shell that *allows* a mutation only
                         when both validation and authority gates pass
                         *and* the target is inside the workspace.

``_apply()`` is only reached after gates pass; a failed gate raises the
relevant error and the filesystem is untouched.  ``ReadOnlyBoundary``
can never mutate — used by the runtime executor's default read path.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from jarvis.errors import (
    AuthorityDeniedError,
    MutationForbiddenError,
    PathEscapeError,
    PathNotFoundError,
    UnknownAnchorError,
)
from jarvis.io.workspace import Workspace
from jarvis.models import OperationResult


class BoundaryClosedError(Exception):
    """Programming error: attempting to write through a boundary that is
    declared read-only."""


# ---------------------------------------------------------------------------
# Operation context (immutable descriptor of *what* is being attempted)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OperationContext:
    """The context accompanying a mutation attempt."""

    operation_id: str
    actor: str                # user / jarvis / tool / council / ...
    authority: str            # authority class claimed
    target: str               # description of the target (inside workspace)
    validation_errors: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Validator / gate types
# ---------------------------------------------------------------------------


ValidatorType = Callable[[OperationContext, Path], tuple[bool, str]]
AuthorityGateType = Callable[[OperationContext, Path], tuple[bool, str]]


# ---------------------------------------------------------------------------
# ReadBoundary — the read side
# ---------------------------------------------------------------------------


class ReadBoundary:
    """Read-only access to the workspace.

    Never mutates.  All reads are confined to the workspace root.
    """

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def read_file(self, relative_path: str | Path) -> str:
        path = self.workspace.resolve_read(relative_path, must_exist=True)
        if not path.is_file():
            raise MutationForbiddenError(
                f"Read attempted on non-file {str(path)!r}.",
                path=relative_path,
                code="not_a_file",
            )
        return path.read_text(encoding="utf-8")

    def list_files(self, relative_path: str | Path = ".") -> list[Path]:
        path = self.workspace.resolve_read(relative_path, must_exist=False)
        if not path.is_dir():
            return []
        return sorted(p for p in path.iterdir())

    def glob(self, pattern: str) -> list[Path]:
        root = self.workspace.resolve_read(".", must_exist=True)
        return sorted(root.glob(pattern))

    def read(self, candidate: str | Path) -> str:
        return self.read_file(candidate)

    def is_valid_target(self, candidate: str | Path) -> bool:
        """True if the path is confined to the workspace (no I/O check)."""
        try:
            self.workspace.resolve(candidate)
        except Exception:
            return False
        return True


# ---------------------------------------------------------------------------
# WriteBoundary — mutation with gates
# ---------------------------------------------------------------------------


class WriteBoundary(ReadBoundary):
    """A boundary that *can* mutate, but only behind validation and
    authority gates.

    ``_validate()`` must pass, then ``_check_authority()``, then the
    write happens.  A failed gate raises before any filesystem touch.

    Subclasses override :meth:`_allowed_authority` to scope down.
    """

    def __init__(self, workspace: Workspace) -> None:
        super().__init__(workspace)

    # -- gates -------------------------------------------------------------

    def _allowed_authority(self, context: OperationContext) -> bool:
        """Return True if *context* has sufficient authority to write.

        Default implementation: only ``user-explicit`` authority allows
        mutation.  Higher layers (e.g. Jenkins / test fixtures) override.
        """
        return context.authority == "user-explicit"

    def _validate(self, context: OperationContext, path: Path) -> tuple[bool, str]:
        """Run the mutation's validation gate.

        Default: path confinement is the validation gate.
        Subclasses can extend.
        """
        try:
            self.workspace.resolve(path)
        except Exception as exc:
            return False, str(exc)
        return True, ""

    def _check_authority(self, context: OperationContext) -> tuple[bool, str]:
        """Run the authority gate."""
        if not self._allowed_authority(context):
            return (
                False,
                f"Actor {context.actor!r} with authority {context.authority!r} "
                f"is not allowed to mutate {context.target!r}. "
                f"Mutation requires explicit user authority.",
            )
        return True, ""

    # -- write -------------------------------------------------------------

    def write(
        self,
        template: str,
        candidate: str | Path,
        *validators: ValidatorType,
        authority: str = "user-explicit",
        actor: str = "jarvis",
        operation_id: str = "write",
        data: Any = None,
    ) -> OperationResult:
        """Attempt a mutation with gates.

        Parameters
        ----------
        template
            The content to write (bytes/text passed straight through).
        candidate
            The path to write to — must resolve inside the workspace and
            match an anchor.
        authority
            The authority class claimed for this mutation.
        actor
            The actor performing the mutation (user/jarvis/tool/...).
        """
        # Path resolution — must stay inside the workspace.
        try:
            path = self.workspace.resolve(candidate)
        except (PathEscapeError, PathNotFoundError, UnknownAnchorError) as exc:
            return OperationResult.fail(
                operation_id=operation_id,
                error=AuthorityDeniedError(
                    f"Cannot mutate {candidate!r}: {exc}",
                    path=str(candidate),
                    code="authority_denied",
                ),
            )

        context = OperationContext(
            operation_id=operation_id,
            actor=actor,
            authority=authority,
            target=str(candidate),
        )

        # Validation gate
        ok, reason = self._validate(context, path)
        if not ok:
            return OperationResult.fail(
                operation_id=operation_id,
                error=AuthorityDeniedError(
                    f"Validation gate refused the mutation of {candidate!r}: {reason}",
                    path=str(candidate),
                    code="validation_gate",
                ),
            )

        # Authority gate
        ok, reason = self._check_authority(context)
        if not ok:
            return OperationResult.fail(
                operation_id=operation_id,
                error=AuthorityDeniedError(reason, path=str(candidate), code="authority_gate"),
            )

        # Extra validators from the caller
        for validator in validators:
            ok, reason = validator(context, path)
            if not ok:
                return OperationResult.fail(
                    operation_id=operation_id,
                    error=AuthorityDeniedError(
                        f"Validator refused the mutation of {candidate!r}: {reason}",
                        path=str(candidate),
                        code="validator_gate",
                    ),
                    provenance={"validator": getattr(validator, "__name__", str(validator))},
                )

        # All gates passed — perform the write
        try:
            path.write_text(template, encoding="utf-8")
        except OSError as exc:
            return OperationResult.fail(
                operation_id=operation_id,
                error=MutationForbiddenError(
                    f"Filesystem write failed for {candidate!r}: {exc}",
                    path=str(candidate),
                    code="write_failed",
                ),
            )

        return OperationResult.ok(
            operation_id=operation_id,
            data={"path": str(path)},
            provenance={"authority": authority, "actor": actor, "target": candidate},
        )

    def apply(self, template: str, candidate: str | Path, **kwargs: Any) -> OperationResult:
        """Alias for :meth:`write` — exists so executors can call a single
        entry point."""
        return self.write(template, candidate, **kwargs)


# ---------------------------------------------------------------------------
# ReadOnlyBoundary — a boundary that can never mutate (default for reads)
# ---------------------------------------------------------------------------


class ReadOnlyBoundary(ReadBoundary):
    """A read-only boundary.  All mutation attempts are refused."""

    def write(self, *_args: Any, **_kwargs: Any) -> OperationResult:
        return OperationResult.fail(
            operation_id="write",
            error=MutationForbiddenError(
                "This boundary is read-only. Mutations are forbidden.",
                code="read_only",
            ),
        )


# ---------------------------------------------------------------------------
# FullyMutableBoundary — default write boundary (user authority required)
# ---------------------------------------------------------------------------


class FullyMutableBoundary(WriteBoundary):
    """The default write boundary: requires user-explicit authority but
    performs the write when granted.  Subclass to add validation gates."""

    # Default validator: refuse writes to .git/**
    def _validate(self, context: OperationContext, path: Path) -> tuple[bool, str]:
        ok, reason = super()._validate(context, path)
        if not ok:
            return ok, reason

        # Reject writes inside .git (the repository metadata)
        git_root = self.workspace.anchor(".git")
        try:
            if path.is_relative_to(git_root):
                return False, "Write target is inside .git/ — protected repository metadata."
        except ValueError:
            pass
        return True, ""