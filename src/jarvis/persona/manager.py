"""Persona Manager — scan definitions, validate, build registry.

This is the FIRST executable primitive in JARVIS OS.

Responsibilities:
  1. Scan a directory for persona definition files (*.md)
  2. Parse YAML frontmatter from each file
  3. Validate required fields and constraints
  4. Build an in-memory PersonaRegistry

No I/O beyond filesystem reads.  No network.  No side effects beyond
file reads.  Deterministic for a given directory state.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import (
    ActivationMode,
    PersonaDefinition,
    PersonaRegistry,
    PersonaStatus,
    PersonaType,
)


# ---------------------------------------------------------------------------
# YAML frontmatter parser (stdlib only — no pyyaml dependency)
# ---------------------------------------------------------------------------

_FRONT_MATTER_RE = re.compile(
    r"^---\s*\n(.*?)\n---\s*\n",
    re.DOTALL,
)


def _parse_frontmatter(raw: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from a Markdown file.

    Returns (frontmatter_dict, body_text).

    This is a *minimal* YAML parser that handles the exact shapes our
    persona definitions use: simple key: value pairs and single-level
    lists.  It does NOT handle nested dicts, multi-line strings, or
    arbitrary YAML — those would require a real parser.
    """
    match = _FRONT_MATTER_RE.match(raw)
    if not match:
        return {}, raw

    yaml_block = match.group(1)
    body = raw[match.end():]

    result: dict = {}
    current_key: Optional[str] = None
    current_list: list[str] = []

    for line in yaml_block.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        # List item
        if stripped.startswith("- ") and current_key:
            current_list.append(stripped[2:].strip())
            continue

        # Flush previous list
        if current_list and current_key:
            result[current_key] = current_list
            current_list = []
            current_key = None

        # Key: value
        if ":" in stripped:
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            if value:
                result[key] = value
            else:
                # Expecting a list on subsequent lines
                current_key = key
                current_list = []

    # Flush trailing list (even if empty — an empty list is still a value)
    if current_key is not None:
        result[current_key] = current_list

    return result, body


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    """Raised when a persona definition fails validation."""

    def __init__(self, path: str, field: str, message: str):
        self.path = path
        self.field = field
        self.message = message
        super().__init__(f"{path}: {field} — {message}")


_REQUIRED_FIELDS = ("id", "name", "type", "status", "activation", "domains")

_VALID_STATUSES = {s.value for s in PersonaStatus}
_VALID_ACTIVATIONS = {a.value for a in ActivationMode}
_VALID_TYPES = {t.value for t in PersonaType}


def validate_definition(
    fm: dict,
    path: str,
) -> None:
    """Validate parsed frontmatter against the persona schema.

    Raises ValidationError on the first failure found.
    """
    # Required fields
    for field_name in _REQUIRED_FIELDS:
        if field_name not in fm or not fm[field_name]:
            raise ValidationError(path, field_name, "missing or empty")

    # Status
    if fm["status"] not in _VALID_STATUSES:
        raise ValidationError(
            path,
            "status",
            f"invalid value '{fm['status']}'; expected one of {_VALID_STATUSES}",
        )

    # Activation mode
    if fm["activation"] not in _VALID_ACTIVATIONS:
        raise ValidationError(
            path,
            "activation",
            f"invalid value '{fm['activation']}'; expected one of {_VALID_ACTIVATIONS}",
        )

    # Type
    if fm["type"] not in _VALID_TYPES:
        raise ValidationError(
            path,
            "type",
            f"invalid value '{fm['type']}'; expected one of {_VALID_TYPES}",
        )

    # Domains must be a non-empty list
    domains = fm["domains"]
    if not isinstance(domains, list) or len(domains) == 0:
        raise ValidationError(path, "domains", "must be a non-empty list")


# ---------------------------------------------------------------------------
# Build a PersonaDefinition from validated frontmatter
# ---------------------------------------------------------------------------

def _build_definition(fm: dict, body: str, path: str) -> PersonaDefinition:
    """Construct a PersonaDefinition from parsed + validated frontmatter."""
    return PersonaDefinition(
        id=fm["id"],
        name=fm["name"],
        type=PersonaType(fm["type"]),
        status=PersonaStatus(fm["status"]),
        activation=ActivationMode(fm["activation"]),
        domains=tuple(fm["domains"]),
        raw_body=body,
        source_path=path,
    )


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

def scan_definitions(definitions_dir: Path) -> tuple[PersonaRegistry, list[ValidationError]]:
    """Scan a directory of persona definition files.

    Returns:
        (registry, errors) — registry is built from valid definitions;
        errors contains any validation failures (file is skipped on error).

    The registry is always usable even if some definitions failed validation.
    """
    registry = PersonaRegistry()

    if not definitions_dir.is_dir():
        return registry, []

    md_files = sorted(definitions_dir.glob("*.md"))

    # Skip the README
    md_files = [f for f in md_files if f.name.upper() != "README.MD"]

    errors: list[ValidationError] = []

    for filepath in md_files:
        raw = filepath.read_text(encoding="utf-8")
        fm, body = _parse_frontmatter(raw)

        try:
            validate_definition(fm, str(filepath))
        except ValidationError as e:
            errors.append(e)
            continue

        definition = _build_definition(fm, body, str(filepath))
        registry.add(definition)

    registry.built_at = datetime.now(timezone.utc)
    return registry, errors


def build_registry(definitions_dir: Path) -> PersonaRegistry:
    """Build a registry, raising on the first validation error.

    Use this when you want a clean build with no partial state.
    For tolerant scanning (skip bad files), use scan_definitions().
    """
    registry, errors = scan_definitions(definitions_dir)
    if errors:
        raise errors[0]
    return registry
