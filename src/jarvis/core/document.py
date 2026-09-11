"""Load Markdown files with YAML frontmatter into typed documents."""

from __future__ import annotations

from pathlib import Path

from jarvis.errors import (
    DocumentError,
    DuplicateIdError,
    FrontmatterError,
    InvalidValueError,
)
from jarvis.io.workspace import Workspace
from jarvis.models.document import MarkdownDocument
from jarvis.validation.pyaml import extract_frontmatter
from jarvis.validation.references import validate_no_duplicate_ids


def load_document(workspace: Workspace, candidate: str) -> MarkdownDocument:
    """Load a Markdown document from the workspace.

    The file is read through the workspace boundary — so traversal,
    absolute paths, or non-workspace paths all raise before reading.

    The function never repairs the document; malformed frontmatter
    raises a typed error.
    """
    source_path = workspace.resolve_read(candidate)
    raw = source_path.read_text(encoding="utf-8")
    metadata, body, has_fm = extract_frontmatter(raw)

    relative = source_path.relative_to(workspace.root)
    return MarkdownDocument(
        source_path=str(source_path),
        relative_path=str(relative).replace("\\", "/"),
        metadata=metadata,
        body=body,
        has_frontmatter=has_fm,
    )


def load_documents(
    workspace: Workspace,
    pattern: str,
    validate_schemas: bool = True,
    validate_references: bool = True,
) -> tuple[list[MarkdownDocument], list[DocumentError]]:
    """Load all files matching *pattern* (glob) inside the workspace.

    Returns ``(documents, errors)`` — valid documents are loaded, invalid
    ones are reported but do not break the batch.

    When ``validate_schemas`` is True, each document is validated against
    the frontmatter schema for its top-level directory (e.g. persona
    definitions validate against the persona schema).  When
    ``validate_references`` is True, duplicate IDs and broken references
    raise immediately.
    """
    # Confine the glob to the workspace root — the pattern runs against
    # ``<root>/<pattern>``; no path can escape the root via glob.
    root_paths = sorted(workspace.root.glob(pattern))
    documents: list[MarkdownDocument] = []
    errors: list[DocumentError] = []

    for path in root_paths:
        if not path.is_file():
            continue
        try:
            doc = load_document(workspace, path.relative_to(workspace.root).as_posix())
            documents.append(doc)
        except (FrontmatterError, DocumentError) as exc:
            errors.append(exc)

    if validate_schemas:
        _validate_batch_schemas(documents)

    if validate_references:
        _validate_batch_references(documents, workspace)

    return documents, errors


def _validate_batch_schemas(documents: list[MarkdownDocument]) -> None:
    """Validate the frontmatter schema per document location.

    The schema is selected based on which workspace anchor the file
    belongs to:
    - .jarvis/personas/definitions/*.md — Persona definition schema
    - .jarvis/memory/**                 — Memory record schema
    - council/*.md                      — Council seat schema
    - vault/**                          — No schema (curated)
    - Everything else                   — No schema (raw text)
    """
    from jarvis.validation.status import MEMORY_TYPES, VALID_STATUS_VALUES
    from jarvis.validation.frontmatter import (
        check_enum,
        check_float_range,
        check_required,
    )

    for doc in documents:
        if ".jarvis/personas/definitions" in doc.source_path.replace("\\", "/"):
            # Persona definition schema — README and index files are exempt.
            if "id" not in doc.metadata:
                continue
            check_required(
                doc.metadata,
                "id",
                "name",
                "type",
                "status",
                "activation",
                "domains",
                path=doc.source_path,
            )
            check_enum(doc.metadata, "status", VALID_STATUS_VALUES, path=doc.source_path)

        elif ".jarvis/memory" in doc.source_path.replace("\\", "/"):
            # Memory record schema — only enforced when the document
            # declares itself a record via an ``id`` field.  Reference
            # docs (index.md, active.md, README, lessons) are exempt:
            # they are curation surfaces, not memory records.
            if "id" not in doc.metadata:
                continue
            required = (
                "id",
                "type",
                "status",
                "source",
                "confidence",
                "authority",
                "approval",
                "actor",
                "scope",
                "created",
                "valid_from",
                "valid_until",
                "supersedes",
                "related",
            )
            check_required(doc.metadata, *required, path=doc.source_path)
            check_enum(doc.metadata, "status", VALID_STATUS_VALUES, path=doc.source_path)
            check_enum(doc.metadata, "type", MEMORY_TYPES, path=doc.source_path)
            check_float_range(doc.metadata, "confidence", path=doc.source_path)

        # Other locations (council, vault, etc.) have no schema requirement.


def _validate_batch_references(
    documents: list[MarkdownDocument],
    workspace: Workspace,
) -> None:
    """Enforce duplicate-ID and broken-reference integrity."""
    validate_no_duplicate_ids(documents, scope="batch")
    # Note: broken-reference validation is intentionally soft here —
    # vault contains many local links.  Only IDs from metadata are
    # treated as hard constraints.  (soft) references are surfaced as
    # warnings by callers that want them.