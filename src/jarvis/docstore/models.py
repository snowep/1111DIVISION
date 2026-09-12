"""Document model: frontmatter + body, parsed and rendered without external deps.

Implements a small YAML-subset: scalars, lists, and nested dictionaries via
indentation. This is enough for Obsidian-compatible frontmatter (tags, lists,
provenance maps, permission maps) without pulling in a YAML dependency.
"""
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

    path: str  # path relative to the store's vault directory (posix style)
    metadata: dict[str, Any] = field(default_factory=dict)
    body: str = ""


# ---------------------------------------------------------------------------
# Parsing (YAML-subset)
# ---------------------------------------------------------------------------
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


def _parse_frontmatter(lines: list[str], path: str) -> dict[str, Any]:
    """Parse indentation-based frontmatter lines into nested dicts/lists."""
    # Pre-tokenize: (indent, key, raw_value, is_list_item)
    tokens: list[tuple[int, str, str, bool]] = []
    for lineno, raw in enumerate(lines, start=2):
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if line.startswith("-"):
            tokens.append((indent, "-", line[1:].strip(), True))
        elif ":" in line:
            key, value = line.split(":", 1)
            tokens.append((indent, key.strip(), value.strip(), False))
        else:
            raise DocError(f"{path}:{lineno}: expected 'key: value' or list item but got {line!r}")

    # Build nested structure via stack of (indent, container, is_list)
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any, bool]] = []  # (indent, container, is_list)

    for i, (indent, key, value, is_list_item) in enumerate(tokens):
        while stack and indent <= stack[-1][0]:
            stack.pop()

        if is_list_item:
            if stack and stack[-1][2]:
                parent = stack[-1][1]
                # An empty '- ' followed by deeper keys becomes a nested dict.
                if value == "" and _next_child_is_map(tokens, i):
                    item: Any = {}
                else:
                    item = _parse_scalar(value)
                parent.append(item)
                if isinstance(item, dict):
                    stack.append((indent, item, False))
                continue
            raise DocError(f"{path}: list item without a parent key")

        # map key
        if not stack:
            container = root
        elif stack[-1][2]:
            # parent is a list; the current key belongs to the last dict item
            last_item = stack[-1][1][-1]
            if not isinstance(last_item, dict):
                raise DocError(f"{path}: cannot add key under non-dict list item")
            container = last_item
        else:
            container = stack[-1][1]

        parsed = _parse_scalar(value)
        if value in ("{}", ""):
            # Determine whether child block is a map or list by lookahead
            child_is_map = _next_child_is_map(tokens, i)
            container[key] = {} if child_is_map else []
            stack.append((indent, container[key], not child_is_map))
        else:
            container[key] = parsed
            if isinstance(parsed, dict):
                stack.append((indent, parsed, False))
            elif isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                stack.append((indent, parsed, True))

    return root


def _next_child_is_map(tokens: list[tuple[int, str, str, bool]], idx: int) -> bool:
    """Look at tokens after idx (with greater indent): map (key: value) or list (- item)."""
    for j in range(idx + 1, len(tokens)):
        if tokens[j][0] <= tokens[idx][0]:
            break
        return not tokens[j][3]  # first deeper token decides: key -> map, '-' -> list
    return True  # empty block defaults to map


def _parse_scalar(raw: str) -> Any:
    raw = raw.strip()
    if raw in ("{}",):
        return {}
    if raw in ("[]",):
        return []
    if len(raw) >= 2 and raw[0] == raw[-1] == '"':
        return raw[1:-1]
    if len(raw) >= 2 and raw[0] == raw[-1] == "'":
        return raw[1:-1]
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
        # simple comma-split; nested lists would need a real parser
        items: list[str] = []
        depth = 0
        cur = ""
        for ch in inner:
            if ch in "[{":
                depth += 1
            elif ch in "]}":
                depth -= 1
            if ch == "," and depth == 0:
                items.append(cur)
                cur = ""
            else:
                cur += ch
        if cur.strip():
            items.append(cur)
        return [_parse_scalar(x) for x in items]
    return raw


# ---------------------------------------------------------------------------
# Rendering (YAML-subset)
# ---------------------------------------------------------------------------
def render_document(doc: Document) -> str:
    """Render a Document back to frontmatter-delimited Markdown text."""
    lines = [_FRONT]
    for key, value in doc.metadata.items():
        _render_value(lines, 0, key, value)
    lines.append(_FRONT)
    if doc.body:
        lines.append("")
        lines.append(doc.body.strip())
    return "\n".join(lines) + "\n"


def _render_value(lines: list[str], indent: int, key: str, value: Any) -> None:
    pad = " " * indent
    if isinstance(value, dict):
        if not value:
            lines.append(f"{pad}{key}: {{}}")
            return
        lines.append(f"{pad}{key}:")
        for k, v in value.items():
            _render_value(lines, indent + 2, k, v)
    elif isinstance(value, (list, tuple)):
        if not value:
            lines.append(f"{pad}{key}: []")
            return
        lines.append(f"{pad}{key}:")
        for item in value:
            if isinstance(item, dict):
                if not item:
                    lines.append(f"{pad}  - {{}}")
                    continue
                lines.append(f"{pad}  -")
                for k, v in item.items():
                    _render_value(lines, indent + 4, k, v)
            else:
                lines.append(f"{pad}  - {_serialize_scalar(item)}")
    else:
        lines.append(f"{pad}{key}: {_serialize_scalar(value)}")


def _serialize_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        s = str(value)
        if ":" in s or s.startswith(("-", "#", "[", "{")) or '"' in s or s.strip() != s:
            return '"' + s.replace('"', '\\"') + '"'
        return s
    return str(value)