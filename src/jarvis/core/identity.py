"""Load the canonical JARVIS identity.

Identity information lives *only* in ``.jarvis/core/identity.md`` plus
``.jarvis/core/system-prompt.md``.  This module enforces that location;
it will refuse any other source.
"""

from __future__ import annotations

from pathlib import Path

from jarvis.errors import IdentityIncompleteError, IdentitySourceError, PathEscapeError
from jarvis.io.workspace import Workspace
from jarvis.models.identity import Identity

# Canonical identity location — never loaded from anywhere else.
CANONICAL_IDENTITY_DIR = ".jarvis/core"
CANONICAL_IDENTITY_FILE = "identity.md"
CANONICAL_SYSTEM_PROMPT = "system-prompt.md"


def _parse_identity_lines(raw: str) -> dict[str, str]:
    """Parse identity fields from identity.md.

    The real identity.md mixes two formats:
    1. ``Key: Value`` lines between the ``#`` title and the first ``##`` heading.
    2. ``## Heading`` sections whose non-empty body text is the field value
       (e.g. ``## Core Purpose\nBe intelligent.`` → ``core purpose``).

    Fields parsed by both methods are merged; key-value lines take priority.
    """
    fields: dict[str, str] = {}
    in_key_value_region = False
    in_code_block = False
    current_section_key: str | None = None
    section_lines: list[str] = []

    def _flush_section() -> None:
        if current_section_key and section_lines:
            fields.setdefault(
                current_section_key, " ".join(section_lines).strip()
            )

    for line in raw.splitlines():
        stripped = line.strip()
        # Toggle code blocks — content inside is never parsed.
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if not stripped:
            continue

        # ``## Heading`` — a section whose body text is the field value
        # (e.g. ``## Core Purpose\nBe intelligent.`` → ``core purpose``).
        if stripped.startswith("## "):
            _flush_section()
            heading = stripped[3:].strip()
            # Map multi-word headings to dotted fields.
            key = heading.lower()
            current_section_key = key
            section_lines = []
            in_key_value_region = False
            continue

        # ``# Title`` — marks the start of the Key: Value region.
        if stripped.startswith("# ") and not in_key_value_region:
            _flush_section()
            current_section_key = None
            section_lines = []
            in_key_value_region = True
            continue

        # If we are in a ``##`` section, accumulate body lines.
        if current_section_key and not in_key_value_region:
            # Stop on the next ``##`` — already handled above.
            # Skip list items (``- ...``), blockquotes, and non-text lines.
            if (
                stripped.startswith("- ")
                or stripped.startswith("> ")
                or stripped.startswith("> ")
            ):
                continue
            section_lines.append(stripped)
            continue

        # Key: Value region.
        if in_key_value_region and ": " in stripped:
            key, _, value = stripped.partition(":")
            fields[key.strip().lower()] = value.strip()

    _flush_section()
    return fields


def load_identity(workspace: Workspace) -> Identity:
    """Load the canonical JARVIS identity.

    Source is restricted to ``.jarvis/core/identity.md``.  If the file
    is missing or the parsed fields don't meet the minimum shape, raises
    :class:`IdentityIncompleteError`.
    """
    identity_path = workspace.resolve_read(
        f"{CANONICAL_IDENTITY_DIR}/{CANONICAL_IDENTITY_FILE}"
    )
    body = identity_path.read_text(encoding="utf-8")
    fields = _parse_identity_lines(body)

    required = ("name", "role", "primary user", "nature", "core purpose")
    for field in required:
        if field not in fields:
            raise IdentityIncompleteError(
                f"Canonical identity file {str(identity_path)!r} is missing "
                f"required field {field!r}.",
                path=str(identity_path),
                code="identity_missing_field",
            )

    personality: tuple[str, ...] = ()
    persona_constraints: tuple[str, ...] = ()

    # Parse list items under ## Personality / ## Persona Constraints if present
    current_section = None
    for line in body.splitlines():
        stripped = line.strip()
        if line.startswith("## Personality"):
            current_section = "personality"
        elif line.startswith("## Persona Constraints"):
            current_section = "persona_constraints"
        elif line.startswith("##"):
            current_section = None
        elif stripped and stripped.startswith("- ") and current_section:
            value = stripped[2:].strip()
            if current_section == "personality":
                personality = (*personality, value)
            elif current_section == "persona_constraints":
                persona_constraints = (*persona_constraints, value)

    return Identity(
        name=fields["name"],
        role=fields["role"],
        primary_user=fields["primary user"],
        nature=fields["nature"],
        core_purpose=fields["core purpose"],
        philosophy=fields.get("philosophy", ""),
        personality=personality,
        persona_constraints=persona_constraints,
        source_path=str(identity_path),
    )


def refuse_non_canonical_identity(workspace: Workspace, candidate: str) -> None:
    """Raise IdentitySourceError when *candidate* is outside the canonical
    identity location.  Used by the loader to guard against Open WebUI
    config being loaded as identity.
    """
    canonical = workspace.resolve(
        f"{CANONICAL_IDENTITY_DIR}/{CANONICAL_IDENTITY_FILE}"
    )
    try:
        proposed = workspace.resolve(candidate)
    except PathEscapeError:
        raise IdentitySourceError(
            f"Identity must be loaded only from {str(canonical)!r}. "
            f"Refusing non-canonical path {str(candidate)!r} (outside workspace).",
            path=str(candidate),
            code="non_canonical_identity",
        ) from None
    if proposed != canonical:
        raise IdentitySourceError(
            f"Identity must be loaded only from {str(canonical)!r}. "
            f"Refusing non-canonical path {str(proposed)!r}.",
            path=str(proposed),
            code="non_canonical_identity",
        )