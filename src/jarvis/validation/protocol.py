"""Authority-boundary check for mutations.

Constitution Rule 4 requires the authority model to be checked; this
module enforces it deterministically: no mutation passes unless the
corresponding authority check passes.
"""

from __future__ import annotations

from typing import Any

from jarvis.errors import AuthorityDeniedError, PathEscapeError
from jarvis.io.workspace import Workspace


def authority_is_valid(workspace: Workspace, candidate: str | Path) -> bool:
    """Constitution-level check: can the workspace mutate *candidate*?

    *candidate* is in the *read* namespace, so this is only the *low-level*
    check: the candidate must resolve inside the canonical workspace and
    (most importantly) inside a protected anchor when it should not be
    mutated without explicit authority.

    This is the runtime's hard gate on mutation; any mutation that fails
    must raise :class:`AuthorityDeniedError`.
    """
    try:
        resolved = workspace.resolve(candidate)
    except (ValueError, PathEscapeError):
        raise AuthorityDeniedError(
            f"Path {str(candidate)!r} is outside the workspace and therefore "
            f"cannot be mutated.",
            path=str(candidate),
            code="authority_denied",
        ) from None

    # Hard rule: never mutate the canonical constitution or identity
    protected = workspace.anchor(".jarvis") / "core"
    if resolved == protected or str(resolved).startswith(str(protected)):
        # Only allow explicitly whitelisted files inside core/ to be safe.
        protected_file = resolved.name.lower()
        if protected_file not in {
            "world-model.md",
            "self-model.md",
            "runtime-spec.md",
            "operating-modes.md",
            "prompt-composition.md",
            "constitution.md",
            "identity.md",
        }:
            raise AuthorityDeniedError(
                f"Mutating {str(resolved)!r} under .jarvis/core requires "
                f"explicit authority (it is not on the whitelisted set).",
                path=str(resolved),
                code="authority_denied",
            )
    return True


def constitution_check(workspace: Workspace, candidate: str | Path) -> bool:
    """Alias for authority_is_valid — the public name used by runtime."""
    return authority_is_valid(workspace, candidate)