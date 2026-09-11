"""JARVIS runtime kernel — typed, inspectable error hierarchy.

Every failure the kernel can produce is a subclass of :class:`JarvisError`
with structured attributes.  Callers inspect ``kind`` / ``path`` / ``code``
instead of pattern-matching strings.

Design rules
------------
- Never silently repair corrupted state: a corrupted canonical file must
  surface as an error, not be auto-corrected.
- Errors carry enough context to be actionable: which file, which field,
  which operation.
- Error ``kind`` is stable and machine-readable.
"""

from __future__ import annotations

from typing import Optional


class JarvisError(Exception):
    """Base class for all JARVIS runtime kernel errors.

    Attributes
    ----------
    kind
        Stable machine-readable category, e.g. ``"path.escape"``.
    path
        Filesystem path involved, if any (relative to the workspace).
    code
        Free-form detail code for programmatic discrimination.
    detail
        Human-readable explanation.
    """

    kind = "jarvis.error"

    def __init__(
        self,
        message: str = "",
        *,
        path: Optional[str] = None,
        code: Optional[str] = None,
    ) -> None:
        self.path = path
        self.code = code
        self.detail = message
        super().__init__(message)

    def to_dict(self) -> dict:
        """Serialize to an inspectable mapping."""
        return {
            "kind": self.kind,
            "message": str(self),
            "path": self.path,
            "code": self.code,
        }

    def __str__(self) -> str:  # pragma: no cover - trivial formatting
        prefix = self.kind
        if self.path:
            prefix = f"{prefix} @ {self.path}"
        if self.code:
            prefix = f"{prefix} [{self.code}]"
        return f"{prefix}: {self.detail or 'unspecified error'}"

    def __repr__(self) -> str:  # pragma: no cover - trivial formatting
        return f"<{type(self).__name__} kind={self.kind!r} path={self.path!r}>"


# ---------------------------------------------------------------------------
# Path / workspace
# ---------------------------------------------------------------------------

class WorkspaceError(JarvisError):
    """Base error for workspace resolution."""


class PathEscapeError(WorkspaceError):
    """A resolved path escaped the workspace root (traversal / absolute)."""

    kind = "path.escape"


class PathNotFoundError(WorkspaceError):
    """A required canonical location does not exist."""

    kind = "path.not_found"


class UnknownAnchorError(WorkspaceError):
    """An anchor name is not a registered workspace anchor."""

    kind = "path.unknown_anchor"


# ---------------------------------------------------------------------------
# Document loading / frontmatter
# ---------------------------------------------------------------------------

class DocumentError(JarvisError):
    """Base error for Markdown/YAML document handling."""


class FrontmatterError(DocumentError):
    """Malformed YAML frontmatter (unterminated fence, bad YAML)."""

    kind = "document.frontmatter"


class MissingFieldError(DocumentError):
    """A required frontmatter field is missing or empty."""

    kind = "document.missing_field"


class InvalidValueError(DocumentError):
    """A field has an invalid value (bad status, bad enum, etc.)."""

    kind = "document.invalid_value"


class DuplicateIdError(DocumentError):
    """Two documents in the same scope declare the same ID."""

    kind = "document.duplicate_id"


class BrokenReferenceError(DocumentError):
    """A document references an ID/path that does not exist."""

    kind = "document.broken_reference"


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------

class IdentityError(JarvisError):
    """Base error for identity loading."""


class IdentitySourceError(IdentityError):
    """Identity was requested from a non-canonical source."""

    kind = "identity.non_canonical_source"


class IdentityIncompleteError(IdentityError):
    """Canonical identity file is missing required fields."""

    kind = "identity.incomplete"


# ---------------------------------------------------------------------------
# Context building
# ---------------------------------------------------------------------------

class ContextError(JarvisError):
    """Base error for runtime context construction."""


class LayerOverrideError(ContextError):
    """A lower layer attempted to override a higher-priority layer."""

    kind = "context.layer_override"


class MissingLayerError(ContextError):
    """A mandatory context layer could not be loaded."""

    kind = "context.missing_layer"


class ConflictingLayersError(ContextError):
    """Two adjacent layers disagree on a value that must match."""

    kind = "context.conflicting_layers"


# ---------------------------------------------------------------------------
# Operations / mutation boundary
# ---------------------------------------------------------------------------

class OperationError(JarvisError):
    """Base error for runtime operations."""


class ValidationFailedError(OperationError):
    """A mutation failed its validation gate."""

    kind = "operation.validation_failed"


class AuthorityDeniedError(OperationError):
    """A mutation was refused by the authority boundary."""

    kind = "operation.authority_denied"


class MutationForbiddenError(OperationError):
    """A mutation was attempted through a read-only boundary."""

    kind = "operation.mutation_forbidden"


class UnsupportedOperationError(OperationError):
    """The operation is not implemented / not bounded."""

    kind = "operation.unsupported"