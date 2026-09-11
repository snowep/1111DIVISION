"""File-backed store with CRUD, path confinement, and atomic writes."""
from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .models import Document, DocError, parse_document, render_document

_KIND_RE = re.compile(r"^[a-z0-9_-]+$")
_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class StoreError(Exception):
    """Operation-level store error (missing, duplicate, invalid path...)."""


class DocumentStore:
    """CRUD over Markdown documents inside an isolated root directory.

    Layout:
        <root>/notes/<kind>/<id>.md   -- the documents (canonical)
        <root>/learn/                 -- derived artifacts (rebuildable)
    """

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.notes_dir = self.root / "notes"
        self.learn_dir = self.root / "learn"
        self.ensure_dirs()

    # ------------------------------------------------------------------ dirs
    def ensure_dirs(self) -> None:
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.learn_dir.mkdir(parents=True, exist_ok=True)

    # ----------------------------------------------------------------- paths
    def _resolve(self, rel: str) -> Path:
        p = Path(rel)
        if p.is_absolute() or ".." in p.parts:
            raise StoreError(f"invalid path (traversal blocked): {rel!r}")
        target = (self.notes_dir / p).resolve()
        if not str(target).startswith(str(self.notes_dir.resolve())):
            raise StoreError(f"path escapes store root: {rel!r}")
        return target

    def _validate_kind(self, kind: str) -> None:
        if not _KIND_RE.fullmatch(kind):
            raise StoreError(f"invalid kind {kind!r}: use [a-z0-9_-]")

    def _validate_id(self, doc_id: str) -> None:
        if not _ID_RE.fullmatch(doc_id):
            raise StoreError(f"invalid id {doc_id!r}: use [A-Za-z0-9._-]")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    @staticmethod
    def _new_id() -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        return f"{stamp}-{uuid.uuid4().hex[:6]}"

    # ------------------------------------------------------------------ CRUD
    def create(
        self,
        kind: str,
        title: str,
        body: str = "",
        metadata: Optional[dict[str, Any]] = None,
        doc_id: Optional[str] = None,
    ) -> Document:
        """Create a document at notes/<kind>/<id>.md and return it."""
        self._validate_kind(kind)
        doc_id = doc_id or self._new_id()
        self._validate_id(doc_id)
        rel = f"{kind}/{doc_id}.md"
        target = self._resolve(rel)
        if target.exists():
            raise StoreError(f"document already exists: {rel}")
        meta: dict[str, Any] = {
            "id": doc_id,
            "kind": kind,
            "title": title,
            "created": self._now(),
            "updated": self._now(),
        }
        for key, value in (metadata or {}).items():
            if key not in ("id", "kind", "title", "created", "updated"):
                meta[key] = value
        doc = Document(path=rel, metadata=meta, body=body)
        target.parent.mkdir(parents=True, exist_ok=True)
        self._write(target, render_document(doc))
        return doc

    def read(self, rel: str) -> Document:
        """Read and parse a document by its relative path."""
        target = self._resolve(rel)
        if not target.is_file():
            raise StoreError(f"document not found: {rel}")
        try:
            return parse_document(rel, target.read_text(encoding="utf-8"))
        except DocError as exc:
            raise StoreError(str(exc)) from exc

    def update(
        self,
        rel: str,
        *,
        body: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        title: Optional[str] = None,
    ) -> Document:
        """Update body/metadata/title in place (atomic)."""
        target = self._resolve(rel)
        if not target.is_file():
            raise StoreError(f"document not found: {rel}")
        try:
            doc = parse_document(rel, target.read_text(encoding="utf-8"))
        except DocError as exc:
            raise StoreError(str(exc)) from exc
        if body is not None:
            doc.body = body
        if title is not None:
            doc.metadata["title"] = title
        for key, value in (metadata or {}).items():
            if key in ("id", "kind", "created"):
                continue
            doc.metadata[key] = value
        doc.metadata["updated"] = self._now()
        self._write(target, render_document(doc))
        return doc

    def delete(self, rel: str) -> None:
        """Delete a document by its relative path."""
        target = self._resolve(rel)
        if not target.is_file():
            raise StoreError(f"document not found: {rel}")
        target.unlink()

    def list_documents(self, kind: Optional[str] = None) -> list[str]:
        """Return relative paths of all Markdown documents (sorted)."""
        if kind is not None:
            self._validate_kind(kind)
        base = self.notes_dir / kind if kind else self.notes_dir
        out: list[str] = []
        if base.is_dir():
            for p in sorted(base.rglob("*.md")):
                if p.is_file():
                    out.append(p.relative_to(self.notes_dir).as_posix())
        return out

    # --------------------------------------------------------------- helpers
    def _write(self, target: Path, text: str) -> None:
        tmp = target.with_name(target.name + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, target)