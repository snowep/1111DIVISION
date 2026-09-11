"""Frontmatter field validators.

These raise :class:`jarvis.errors` typed errors — they never auto-repair
corrupted metadata.  The caller decides whether a failing document is
skipped (scan) or fatal (strict load).
"""

from __future__ import annotations

from typing import Any, Iterable

from jarvis.errors import (
    InvalidValueError,
    MissingFieldError,
)
from jarvis.validation.status import VALID_STATUS_VALUES


def check_required(
    metadata: dict[str, Any],
    *fields: str,
    path: str | None = None,
) -> None:
    """Raise MissingFieldError if any required field is absent or empty."""
    for field_name in fields:
        value = metadata.get(field_name)
        if value is None or value == "" or value == {} or value == []:
            raise MissingFieldError(
                f"Required field {field_name!r} is missing or empty.",
                path=path,
                code=f"missing:{field_name}",
            )


def check_type(
    metadata: dict[str, Any],
    field_name: str,
    expected: type,
    path: str | None = None,
) -> Any:
    """Return the field value if it matches *expected*, else raise.

    Returns the value so callers can chain checks without re-reading the map.
    """
    value = metadata.get(field_name)
    if value is None or not isinstance(value, expected):
        raise InvalidValueError(
            f"Field {field_name!r} must be of type {expected.__name__}, "
            f"got {type(value).__name__ if value is not None else 'missing'}.",
            path=path,
            code=f"type:{field_name}",
        )
    return value


def check_enum(
    metadata: dict[str, Any],
    field_name: str,
    allowed: Iterable[str],
    path: str | None = None,
) -> str:
    """Return the field value if it is one of *allowed*, else raise."""
    value = metadata.get(field_name)
    if value is None:
        raise InvalidValueError(
            f"Field {field_name!r} is required for enum check.",
            path=path,
            code=f"missing:{field_name}",
        )
    if not isinstance(value, str) or value not in allowed:
        allowed_str = ", ".join(sorted(allowed))
        raise InvalidValueError(
            f"Field {field_name!r} has invalid value {value!r}; "
            f"expected one of: {allowed_str}.",
            path=path,
            code=f"enum:{field_name}",
        )
    return value


def check_float_range(
    metadata: dict[str, Any],
    field_name: str,
    low: float = 0.0,
    high: float = 1.0,
    path: str | None = None,
) -> float:
    """Return the field value if it is a number in [low, high], else raise."""
    value = metadata.get(field_name)
    if value is None:
        raise InvalidValueError(
            f"Field {field_name!r} is required for range check.",
            path=path,
            code=f"missing:{field_name}",
        )
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise InvalidValueError(
            f"Field {field_name!r} must be numeric, got {value!r}.",
            path=path,
            code=f"type:{field_name}",
        )
    if not (low <= value <= high):
        raise InvalidValueError(
            f"Field {field_name!r} must be in [{low}, {high}], got {value}.",
            path=path,
            code=f"range:{field_name}",
        )
    return float(value)


def validate_status(
    metadata: dict[str, Any],
    path: str | None = None,
) -> str:
    """Validate the ``status`` field is a known lifecycle status."""
    return check_enum(metadata, "status", VALID_STATUS_VALUES, path=path)


def validate_frontmatter(
    metadata: dict[str, Any],
    required: Iterable[str],
    enum_fields: dict[str, Iterable[str]] | None = None,
    path: str | None = None,
) -> None:
    """Composite validation: required fields + enum-valued fields.

    Raises the first failure encountered.
    """
    check_required(metadata, *tuple(required), path=path)
    if enum_fields:
        for field_name, allowed in enum_fields.items():
            check_enum(metadata, field_name, allowed, path=path)