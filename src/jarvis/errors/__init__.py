"""Typed, inspectable errors for the JARVIS runtime kernel.

Every failure mode has a stable ``code`` (never a bare string message) so
callers can branch on machine-readable semantics. The kernel NEVER silently
repairs corrupted state — it raises a typed error with a full diagnostic.

Hierarchy::

    JarvisError
    ├── PathError           (path resolution failures)
    │   ├── EscapeError     (traversal / symlink escape attempts)
    │   └── NotFoundError   (target does not exist)
    ├── ParseError          (malformed frontmatter / YAML-subset)
    ├── ValidationError     (schema / integrity violations)
    │   ├── MissingFieldError
    │   ├── DuplicateIdError
    │   ├── InvalidStatusError
    │   └── BrokenRefError
    ├── AuthorizationError  (authority boundary violations)
    │   └── MutationDeniedError
    ├── CorruptStateError   (source is corrupt; will NOT be auto-repaired)
    ├── IdentityError       (identity load failures)
    └── ContextError        (context assembly failures)
"""
from __future__ import annotations

from typing import Any, Optional


class JarvisError(Exception):
    """Base class for all typed runtime-kernel errors."""

    code = "JARVIS_ERROR"

    def __init__(
        self,
        message: str,
        *,
        path: Optional[str] = None,
        detail: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.path = path
        self.detail = detail or {}

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.path is not None:
            out["path"] = self.path
        if self.detail:
            out["detail"] = self.detail
        return out


class PathError(JarvisError):
    code = "PATH_ERROR"


class EscapeError(PathError):
    """A path attempted to leave the allowed workspace roots."""

    code = "PATH_ESCAPE"


class NotFoundError(PathError):
    code = "NOT_FOUND"


class ParseError(JarvisError):
    """Frontmatter/YAML-subset text could not be parsed."""

    code = "PARSE_ERROR"


class ValidationError(JarvisError):
    code = "VALIDATION_ERROR"


class MissingFieldError(ValidationError):
    code = "MISSING_FIELD"


class DuplicateIdError(ValidationError):
    code = "DUPLICATE_ID"


class InvalidStatusError(ValidationError):
    code = "INVALID_STATUS"


class BrokenRefError(ValidationError):
    code = "BROKEN_REF"


class AuthorizationError(JarvisError):
    """The acting authority lacks permission for the operation."""

    code = "AUTHORIZATION_ERROR"


class MutationDeniedError(AuthorizationError):
    code = "MUTATION_DENIED"


class CorruptStateError(JarvisError):
    """Source of truth is corrupt. The kernel refuses to auto-repair."""

    code = "CORRUPT_STATE"


class IdentityError(JarvisError):
    code = "IDENTITY_ERROR"


class ContextError(JarvisError):
    code = "CONTEXT_ERROR"


__all__ = [
    "JarvisError",
    "PathError",
    "EscapeError",
    "NotFoundError",
    "ParseError",
    "ValidationError",
    "MissingFieldError",
    "DuplicateIdError",
    "InvalidStatusError",
    "BrokenRefError",
    "AuthorizationError",
    "MutationDeniedError",
    "CorruptStateError",
    "IdentityError",
    "ContextError",
]