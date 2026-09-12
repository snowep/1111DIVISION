"""Normalized, typed result payload returned by every kernel operation.

Unlike a bare ``dict``, ``OperationResult`` is structured and inspectable:
- success:      did the operation complete?
- operation_id: stable identifier for audit linkage
- data:         the payload (dict/list/scalar), never a raw exception string
- warnings:     non-fatal conditions observed during the run
- errors:       typed error records (dicts via .to_dict()) — empty on success
- provenance:   evidence/provenance carried by the operation

Callers SHOULD NOT put arbitrary exception text into ``data``. Errors belong
in the ``errors`` list, machine-readable.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional

from jarvis.errors import JarvisError


@dataclass
class OperationResult:
    success: bool
    operation: str
    operation_id: str
    data: Any = None
    warnings: list[str] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------ ctor
    @classmethod
    def ok(
        cls,
        operation: str,
        operation_id: str,
        data: Any = None,
        *,
        warnings: Optional[list[str]] = None,
        provenance: Optional[dict[str, Any]] = None,
    ) -> "OperationResult":
        return cls(
            success=True,
            operation=operation,
            operation_id=operation_id,
            data=data,
            warnings=list(warnings or []),
            provenance=dict(provenance or {}),
        )

    @classmethod
    def fail(
        cls,
        operation: str,
        operation_id: str,
        error: Optional[JarvisError | Exception] = None,
        *,
        data: Any = None,
        warnings: Optional[list[str]] = None,
        provenance: Optional[dict[str, Any]] = None,
    ) -> "OperationResult":
        errors: list[dict[str, Any]] = []
        if error is not None:
            if isinstance(error, JarvisError):
                errors.append(error.to_dict())
            else:
                errors.append(
                    {"code": "UNEXPECTED_ERROR", "message": str(error)}
                )
        return cls(
            success=False,
            operation=operation,
            operation_id=operation_id,
            data=data,
            warnings=list(warnings or []),
            errors=errors,
            provenance=dict(provenance or {}),
        )

    # ------------------------------------------------------------------ api
    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def fail_with(self, error: JarvisError) -> "OperationResult":
        """Return a failed copy carrying this error (keeps op metadata)."""
        return OperationResult.fail(
            self.operation,
            self.operation_id,
            error,
            data=self.data,
            warnings=self.warnings,
            provenance=self.provenance,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def error_codes(self) -> list[str]:
        return [e.get("code", "?") for e in self.errors]

    def __bool__(self) -> bool:
        return self.success