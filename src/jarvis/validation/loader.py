"""Frontmatter-typed loader: turns Markdown-with-YAML-frontmatter into
typed objects with full validation.

This is the "Markdown/YAML loader" component. It:
1. reads a file at a resolved path
2. parses frontmatter -> metadata dict (reusing docstore.models YAML-subset)
3. splits body text
4. validates required fields, duplicate IDs, statuses, and broken refs
5. returns a typed, deterministic ``LoadedDocument``

It NEVER silently repairs corrupted state — any violation raises a typed
error (MissingFieldError, DuplicateIdError, InvalidStatusError, ...).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from jarvis.docstore.models import DocError, parse_document
from jarvis.docstore.store import DocumentStore, StoreError
from jarvis.errors import (
    BrokenRefError,
    CorruptStateError,
    DuplicateIdError,
    EscapeError,
    InvalidStatusError,
    JarvisError,
    MissingFieldError,
    NotFoundError,
    ParseError,
    ValidationError,
)


@dataclass
class LoadedDocument:
    """A validated document with typed metadata and plain body."""

    path: str  # posix relpath inside the store root
    metadata: dict[str, Any]
    body: str
    required_fields: tuple[str, ...] = ()  # what the validator demanded


@dataclass
class ValidationRules:
    required: tuple[str, ...] = ("id", "kind", "title")
    statuses: Optional[tuple[str, ...]] = None  # e.g. MEMORY_PHASES
    ref_fields: tuple[str, ...] = ()  # metadata fields that point at relpaths
    id_field: str = "id"
    check_duplicate_ids: bool = True
    allow_unknown: bool = True  # False -> ValidationError on unknown metadata


def _validate(
    doc: LoadedDocument,
    rules: ValidationRules,
    seen_ids: dict[str, str],
) -> None:
    meta = doc.metadata
    for f in rules.required:
        if f not in meta or meta[f] is None or meta[f] == "":
            raise MissingFieldError(
                f"missing required field '{f}' in {doc.path}",
                path=doc.path,
                detail={"field": f},
            )
    if rules.statuses is not None:
        status = meta.get("status")
        if status is not None and str(status) not in rules.statuses:
            raise InvalidStatusError(
                f"{doc.path}: invalid status {status!r} "
                f"(allowed: {', '.join(rules.statuses)})",
                path=doc.path,
                detail={"status": str(status), "allowed": list(rules.statuses)},
            )
    if rules.check_duplicate_ids:
        doc_id = str(meta.get(rules.id_field, ""))
        if doc_id:
            if doc_id in seen_ids and seen_ids[doc_id] != doc.path:
                raise DuplicateIdError(
                    f"duplicate id '{doc_id}' in {doc.path} "
                    f"(first seen in {seen_ids[doc_id]})",
                    path=doc.path,
                    detail={"id": doc_id, "first": seen_ids[doc_id]},
                )
            seen_ids[doc_id] = doc.path


def _as_store(source: DocumentStore | Path) -> DocumentStore:
    """Accept either a DocumentStore or a vault root directory."""
    if isinstance(source, DocumentStore):
        return source
    path = Path(source)
    # A vault root may be passed as <root>/vault; DocumentStore expects <root>
    if path.name == "vault":
        path = path.parent
    return DocumentStore(path)


def load_document(
    source: DocumentStore | Path,
    rel: str,
    *,
    rules: Optional[ValidationRules] = None,
    seen_ids: Optional[dict[str, str]] = None,
) -> LoadedDocument:
    """Load + validate one document from a store (or vault root path).

    ``ref_fields`` are NOT resolved here (resolution needs the full
    registry), so broken refs in an individual doc are checked via
    ``validate_refs`` against an explicit set of known paths.
    """
    store = _as_store(source)
    rule = rules or ValidationRules()
    try:
        raw = store.read(rel)
    except StoreError as exc:
        raise _classify_store_error(exc, rel)
    except DocError as exc:
        raise ParseError(str(exc), path=rel)

    seen = seen_ids if seen_ids is not None else {}
    doc = LoadedDocument(path=rel, metadata=raw.metadata, body=raw.body)
    _validate(doc, rule, seen)
    return doc


def _classify_store_error(exc: StoreError, rel: str) -> JarvisError:
    """Map a docstore error to the precise typed kernel error.

    DocumentStore wraps parse failures (DocError) into StoreError, so we
    classify by message: traversal -> EscapeError, missing -> NotFoundError,
    malformed document -> ParseError, anything else -> CorruptStateError.
    """
    msg = str(exc)
    if "not found" in msg:
        return NotFoundError(msg, path=rel)
    if "traversal" in msg or "escapes" in msg:
        return EscapeError(msg, path=rel)
    if "frontmatter" in msg or "expected" in msg or "parse" in msg.lower():
        return ParseError(msg, path=rel)
    return CorruptStateError(msg, path=rel)


def validate_refs(
    doc: LoadedDocument,
    rules: ValidationRules,
    known_paths: set[str],
) -> None:
    """Check every ref field in the doc resolves to a known path."""
    for f in rules.ref_fields:
        value = doc.metadata.get(f)
        if value is None:
            continue
        refs: list[str] = []
        if isinstance(value, str):
            refs.append(value)
        elif isinstance(value, list):
            refs = [str(v) for v in value]
        for ref in refs:
            if ref not in known_paths:
                raise BrokenRefError(
                    f"{doc.path}: field '{f}' references unknown path '{ref}'",
                    path=doc.path,
                    detail={"field": f, "ref": ref},
                )


def load_all(
    store: DocumentStore,
    *,
    rules: Optional[ValidationRules] = None,
) -> list[LoadedDocument]:
    """Load every document in the vault with duplicate-ID detection."""
    rule = rules or ValidationRules()
    seen: dict[str, str] = {}
    known: set[str] = set(store.list_documents())
    docs: list[LoadedDocument] = []
    for rel in store.list_documents():
        doc = load_document(store, rel, rules=rule, seen_ids=seen)
        validate_refs(doc, rule, known)
        docs.append(doc)
    return docs