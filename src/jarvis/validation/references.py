"""Reference and duplicate-ID validation.

Scans documents for reference patterns (``MEM-001``, ``DEC-002``,
``[[wikilink]]``, relative paths) and reports any that cannot be
resolved against the workspace — without mutating anything.
"""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Iterable

from jarvis.errors import (
    BrokenReferenceError,
    DuplicateIdError,
)


class _IdentityReference(PurePosixPath):
    """Marker class for ID references (MEM-001, DEC-002, etc.)."""

    __slots__ = ("id",)

    def __new__(cls, reference: str):
        obj = super().__new__(cls, reference)
        object.__setattr__(obj, "id", reference)
        return obj


# MEM-001, DEC-002, EVT-000003, EVD-0001, CM-...
_ID_REF_RE = re.compile(r"\b(MEM|DEC|EVT|EVD|CM|OBS|SKL)-[A-Z0-9]+\b")
_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")

_KNOWN_UNRESOLVABLE_PREFIXES = ("TODO", "TBD", "FIXME")

_WIKILINK_CONVENTIONAL = {"readme", "index", "seat-change-log", "dashboard"}


def _looks_unresolvable(token: str) -> bool:
    upper = token.upper()
    return any(upper.startswith(p) for p in _KNOWN_UNRESOLVABLE_PREFIXES)


def find_reference_targets(body: str, metadata: dict) -> list[str]:
    """Collect all reference strings mentioned in a document.

    Returns a flat, de-duplicated list of reference tokens.
    """
    refs: list[str] = []

    for match in _ID_REF_RE.finditer(body):
        refs.append(match.group(0))
    for match in _ID_REF_RE.finditer(str(metadata)):
        refs.append(match.group(0))

    for match in _WIKILINK_RE.finditer(body):
        target = match.group(1).strip()
        if target.lower() in _WIKILINK_CONVENTIONAL:
            continue
        refs.append(target)

    return list(dict.fromkeys(refs))


def _resolve(reference: str, known: set[str], root: Path | None) -> Path | None:
    """Try to resolve *reference* against known IDs or the workspace root."""
    if reference in known:
        return _IdentityReference(reference)
    if root is not None:
        candidate = (root / reference).with_suffix(".md")
        if candidate.is_file():
            return candidate
        candidate_noext = root / reference
        if candidate_noext.is_file():
            return candidate_noext
    return None


def resolve_reference_target(
    reference: str,
    known_ids: Iterable[str],
    workspace_root: Path | None = None,
) -> Path | None:
    """Resolve a reference token to an existing path/ID.

    Returns a Path when the reference is a path under *workspace_root*
    and the file exists.  Returns an ``_IdentityReference`` (a Path
    subclass with ``.id`` set) when the reference is a known ID.  Returns
    None when unresolvable.
    """
    return _resolve(reference, set(known_ids), workspace_root)


def find_duplicate_ids(documents: Iterable[object]) -> list[tuple[str, list[str]]]:
    """Return [(id, [paths...])] for IDs declared by more than one document."""
    seen: dict[str, list[str]] = {}
    for doc in documents:
        doc_id = getattr(doc, "metadata", {}).get("id")
        if not doc_id:
            continue
        seen.setdefault(str(doc_id), []).append(getattr(doc, "source_path", "?"))
    return [(id_, paths) for id_, paths in seen.items() if len(paths) > 1]


def validate_no_duplicate_ids(
    documents: Iterable[object],
    scope: str = "workspace",
) -> None:
    """Raise DuplicateIdError if any ID is declared by multiple documents."""
    duplicates = find_duplicate_ids(documents)
    if duplicates:
        id_, paths = duplicates[0]
        raise DuplicateIdError(
            f"Duplicate id {id_!r} declared by multiple documents in {scope}: "
            f"{paths}",
            path=paths[0],
            code="duplicate_id",
        )


def find_unresolved_references(
    documents: Iterable[object],
    known_ids: Iterable[str],
    workspace_root: Path | None = None,
) -> list[tuple[str, str, str]]:
    """Return [(source_path, reference, reason)] for broken references."""
    known = set(known_ids)
    broken: list[tuple[str, str, str]] = []
    for doc in documents:
        source_path = getattr(doc, "source_path", "?")
        refs = find_reference_targets(
            getattr(doc, "body", ""), getattr(doc, "metadata", {})
        )
        for ref in refs:
            if _looks_unresolvable(ref):
                continue
            if _resolve(ref, known, workspace_root) is not None:
                continue
            broken.append((source_path, ref, "unresolved"))
    return broken


def validate_references_resolve(
    documents: Iterable[object],
    known_ids: Iterable[str],
    workspace_root: Path | None = None,
) -> None:
    """Raise BrokenReferenceError on the first unresolvable reference."""
    broken = find_unresolved_references(documents, known_ids, workspace_root)
    if broken:
        source_path, ref, reason = broken[0]
        raise BrokenReferenceError(
            f"Reference {ref!r} in {source_path} cannot be resolved ({reason}).",
            path=source_path,
            code="broken_reference",
        )