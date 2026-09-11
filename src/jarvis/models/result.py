"""Operation result model — the structured envelope every bounded runtime
operation returns.

Fields (per Phase 10 spec):
- success      — did the operation complete?
- operation_id — stable identifier of the operation executed
- data         — the operation's payload (None on failure)
- warnings     — recoverable concerns, never fatal
- errors       — typed error records (never silently swallowed)
- evidence     — evidence/provenance records the operation produced or cited
- provenance   — provenance chain describing where the operation's effects
                 (and its inputs) came from
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from jarvis.errors import JarvisError


@dataclass(frozen=True)
class OperationResult:
    """Immutable result envelope for a runtime operation."""

    success: bool
    operation_id: str
    data: Any = None
    warnings: tuple[str, ...] = ()
    errors: tuple[JarvisError, ...] = ()
    evidence: tuple[dict, ...] = ()
    provenance: dict = field(default_factory=dict)

    # -- constructors -----------------------------------------------------

    @classmethod
    def ok(
        cls,
        operation_id: str,
        data: Any = None,
        warnings: tuple[str, ...] = (),
        evidence: tuple[dict, ...] = (),
        provenance: Optional[dict] = None,
    ) -> "OperationResult":
        return cls(
            success=True,
            operation_id=operation_id,
            data=data,
            warnings=tuple(warnings),
            evidence=tuple(evidence),
            provenance=dict(provenance or {}),
        )

    @classmethod
    def fail(
        cls,
        operation_id: str,
        error: JarvisError | tuple[JarvisError, ...],
        data: Any = None,
        warnings: tuple[str, ...] = (),
        evidence: tuple[dict, ...] = (),
        provenance: Optional[dict] = None,
    ) -> "OperationResult":
        errors = error if isinstance(error, tuple) else (error,)
        return cls(
            success=False,
            operation_id=operation_id,
            data=data,
            warnings=tuple(warnings),
            errors=tuple(errors),
            evidence=tuple(evidence),
            provenance=dict(provenance or {}),
        )

    # -- inspection helpers ------------------------------------------------

    @property
    def is_ok(self) -> bool:
        """Convenience mirror of ``success`` — avoids the classmethod/property
        name collision that would otherwise break ``OperationResult.ok(...)``.
        """
        return self.success

    @property
    def error_codes(self) -> tuple[str, ...]:
        """Stable machine-readable error kinds (empty when successful)."""
        return tuple(e.kind for e in self.errors)

    def merge(self, *others: "OperationResult") -> "OperationResult":
        """Combine this result with others (all must share operation prefix)."""
        return OperationResult(
            success=self.success and all(o.success for o in others),
            operation_id=self.operation_id,
            data=self.data if self.success else None,
            warnings=self.warnings + tuple(
                w for o in others for w in o.warnings
            ),
            errors=self.errors + tuple(e for o in others for e in o.errors),
            evidence=self.evidence + tuple(e for o in others for e in o.evidence),
        )

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "operation_id": self.operation_id,
            "data": self.data,
            "warnings": list(self.warnings),
            "errors": [e.to_dict() for e in self.errors],
            "evidence": list(self.evidence),
            "provenance": dict(self.provenance),
        }