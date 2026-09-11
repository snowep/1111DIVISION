"""Document model: frontmatter + body, parsed and rendered without external deps."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_FRONT = "---"
_INT = re.compile(r"-?\d+")
_NUM = re.compile(r"-?\d+(\.\d+)?")


class DocError(ValueError):
    """Raised when a document is malformed or cannot be parsed."""


@dataclass
class Document:
    """A single Markdown document with YAML-like frontmatter and a body."""

    path: str  # path relative to the store's notes directory (posix style)
    metadata: dict[str, Any] = field(default_factory=dict)
    body: str = ""


def parse_document(path: str, text: str) -> Document:
    """Parse frontmatter-delimited Markdown text into a Document."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != _FRONT:
        raise DocError(f"{path}: missing frontmatter delimiter at line 1")
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == _FRONT:
            end = i
            break
    if end is None:
        raise DocError(f"{path}: unterminated frontmatter")
    metadata = _parse_frontmatter(lines[1:end], path)
    body = "\n".join(lines[end + 1 :]).strip()
    return Document(path=path, metadata=metadata, body=body)


def render_document(doc: Document) -> str:
    """Render a Document back to frontmatter-delimited Markdown text."""
    lines = [_FRONT]
    for key, value in doc.metadata.items():
        lines.append(f"{key}: {_serialize_value(value)}")
    lines.append(_FRONT)
    if doc.body:
        lines.append("")
        lines.append(doc.body.strip())
    return "\n".join(lines) + "\n"


def _parse_frontmatter(lines: list[str], path: str) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    for lineno, line in enumerate(lines, start=2):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            raise DocError(f"{path}:{lineno}: expected 'key: value' but got {stripped!r}")
        key, raw = stripped.split(":", 1)
        key = key.strip()
        if not key:
            raise DocError(f"{path}:{lineno}: empty metadata key")
        metadata[key] = _parse_scalar(raw)
    return metadata


def _parse_scalar(raw: str) -> Any:
    raw = raw.strip()
    if _INT.fullmatch(raw):
        return int(raw)
    if _NUM.fullmatch(raw):
        return float(raw)
    low = raw.lower()
    if low in ("true", "false"):
        return low == "true"
    if low in ("null", "none"):
        return None
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(x) for x in inner.split(",")]
    return raw


def _serialize_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_serialize_value(v) for v in value) + "]"
    return str(value)