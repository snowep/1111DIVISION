"""Deterministic YAML-subset parser (stdlib only).

This is NOT a general YAML parser.  It deliberately handles the exact
subset the JARVIS canonical layer uses — flat scalars, lists, and inline
maps — with strict, deterministic rules:

Supported::

    key: scalar
    key: "quoted scalar"
    key: [a, b, c]
    key:
      - item
      - item
    key:
      a: 1
      b: two

Numbers, booleans, and ``null`` are coerced deterministically.
Anything more complex (nested lists-of-maps, flow maps inside lists,
anchors/aliases, multi-line strings) raises :class:`YamlSyntaxError`
instead of silently mis-parsing.

The parser raises on malformed YAML — it never guesses.  This satisfies
the kernel rule: corrupted state surfaces as an error, never silent repair.
"""

from __future__ import annotations

import re
from typing import Any

from jarvis.errors import FrontmatterError


class YamlSyntaxError(FrontmatterError):
    """Malformed YAML-subset input."""

    kind = "validation.yaml_syntax"


# ---------------------------------------------------------------------------
# Scalar coercion — deterministic subset of YAML 1.2 core scalars
# ---------------------------------------------------------------------------

_BOOL_TRUE = {"true", "yes", "on"}
_BOOL_FALSE = {"false", "no", "off"}
_NULL_VALUES = {"null", "~", ""}

_FLOAT_RE = re.compile(
    r"^[+-]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?$"
)
_INT_RE = re.compile(r"^[+-]?\d+$")


def _coerce_scalar(raw: str) -> Any:
    """Coerce a plain scalar string to its value type deterministically."""
    value = raw.strip()

    if value in _NULL_VALUES:
        return None
    if value.lower() in _BOOL_TRUE:
        return True
    if value.lower() in _BOOL_FALSE:
        return False

    if _INT_RE.match(value):
        try:
            return int(value)
        except ValueError:  # pragma: no cover - defensive
            pass
    if _FLOAT_RE.match(value):
        try:
            return float(value)
        except ValueError:  # pragma: no cover - defensive
            pass

    # Strip inline comment that is separated by whitespace
    #  key: value # comment  ->  "value"
    if " #" in value:
        value = value.split(" #", 1)[0].rstrip()
        return _coerce_scalar(value)

    return value


def _strip_inline_comment(line: str) -> str:
    """Remove a trailing YAML comment when preceded by whitespace."""
    for idx, ch in enumerate(line):
        if ch == "#" and idx > 0 and line[idx - 1] in " \t":
            return line[:idx].rstrip()
    return line


def _split_scalar(line: str, key: str) -> str:
    """Return the scalar after 'key:' (minus inline comment)."""
    value = line.split(":", 1)[1].strip()
    return _strip_inline_comment(value).strip()


# ---------------------------------------------------------------------------
# Flow sequences: [a, b, c]
# ---------------------------------------------------------------------------

def _parse_flow_list(raw: str) -> list[Any]:
    """Parse a flow-style list ``[a, b, c]`` (scalars only)."""
    inner = raw.strip()
    if not (inner.startswith("[") and inner.endswith("]")):
        raise YamlSyntaxError(f"Invalid flow list: {raw!r}")
    core = inner[1:-1].strip()
    if not core:
        return []
    items: list[Any] = []
    for token in _split_flow_items(core):
        token = token.strip()
        if not token:
            continue
        if token[0] in "[{":
            raise YamlSyntaxError(
                f"Nested flow collections are not supported: {token!r}"
            )
        items.append(_coerce_scalar(_unquote(token)))
    return items


def _unquote(token: str) -> str:
    """Strip surrounding single/double quotes."""
    token = token.strip()
    if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'":
        return token[1:-1]
    return token


def _split_flow_items(core: str) -> list[str]:
    """Split a flow list's core on commas not inside quoted strings."""
    items: list[str] = []
    current: list[str] = []
    in_quote: str | None = None
    for ch in core:
        if in_quote:
            current.append(ch)
            if ch == in_quote:
                in_quote = None
        elif ch in "\"'":
            in_quote = ch
            current.append(ch)
        elif ch == ",":
            items.append("".join(current))
            current = []
        else:
            current.append(ch)
    items.append("".join(current))
    return items


# ---------------------------------------------------------------------------
# Main parse
# ---------------------------------------------------------------------------

_BLOCK_SEQ_ITEM_RE = re.compile(r"^-\s+(.*)$")
_KEY_RE = re.compile(r"^([A-Za-z0-9_.\-]+):(.*)$")


def parse_yaml_subset(text: str) -> dict[str, Any]:
    """Parse a YAML-subset block into a flat mapping.

    Raises
    ------
    YamlSyntaxError
        If the block contains constructs outside the supported subset or
        is otherwise malformed.
    """
    if not isinstance(text, str):
        raise YamlSyntaxError(f"YAML block must be text, got {type(text).__name__}")

    result: dict[str, Any] = {}

    # Track block structures: after "key:" with no value, we expect
    # either a list (block sequence) or a nested map (block mapping).
    active_key: str | None = None
    active_list: list[Any] | None = None
    active_map: dict[str, Any] | None = None

    lines = text.split("\n")

    for line_number, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))

        # Nested mapping values (indented key: value under an active key)
        if (
            active_key is not None
            and active_map is not None
            and indent > 0
            and _KEY_RE.match(stripped)
            and not stripped.startswith("-")
        ):
            match = _KEY_RE.match(stripped)
            assert match is not None
            sub_key = match.group(1).strip()
            rest = match.group(2).strip()
            # Only allow scalar or flow-list values in nested maps
            if rest.startswith("["):
                active_map[sub_key] = _parse_flow_list(rest)
            else:
                active_map[sub_key] = _coerce_scalar(_strip_inline_comment(rest))
            continue

        # Block sequence item ( "- item" ) under an active key
        if (
            active_key is not None
            and active_list is not None
            and indent > 0
            and _BLOCK_SEQ_ITEM_RE.match(stripped)
        ):
            match = _BLOCK_SEQ_ITEM_RE.match(stripped)
            assert match is not None
            item_raw = match.group(1).strip()
            if item_raw.startswith("["):
                active_list.append(_parse_flow_list(item_raw))
            else:
                active_list.append(_coerce_scalar(_strip_inline_comment(item_raw)))
            continue

        # If we encounter a top-level key while a nested block was active,
        # flush the nested structure into its owning key.
        if (
            active_key is not None
            and (active_list is not None or active_map is not None)
            and indent == 0
            and _KEY_RE.match(stripped)
        ):
            _flush_active(result, active_key, active_list, active_map)
            active_key = None
            active_list = None
            active_map = None

        # Top-level key: value (or value-less key opening a block)
        match = _KEY_RE.match(stripped)
        if match:
            key = match.group(1).strip()
            rest = match.group(2).strip()

            # Flush any previously-open block before a new key
            if active_key is not None and (
                active_list is not None or active_map is not None
            ):
                _flush_active(result, active_key, active_list, active_map)
                active_key = None
                active_list = None
                active_map = None

            if rest == "":
                # Value-less key: a nested block follows.
                active_key = key
                active_list = []
                active_map = {}
                continue
            if rest.startswith("["):
                result[key] = _parse_flow_list(rest)
            elif "#" in rest and not (rest.startswith(("\"", "'"))):
                result[key] = _coerce_scalar(_strip_inline_comment(rest))
            else:
                result[key] = _coerce_scalar(rest)
            continue

        raise YamlSyntaxError(
            f"Unsupported YAML-subset construct at line {line_number}: {stripped!r}"
        )

    # Flush trailing block
    if active_key is not None and (active_list is not None or active_map is not None):
        _flush_active(result, active_key, active_list, active_map)

    return result


def _flush_active(
    result: dict[str, Any],
    key: str,
    active_list: list[Any] | None,
    active_map: dict[str, Any] | None,
) -> None:
    """Flush an opened nested block into *result* under *key*."""
    if active_list is not None and active_list:
        result[key] = active_list
    elif active_map is not None and active_map:
        result[key] = active_map
    else:
        result[key] = [] if active_list is not None else {}


# ---------------------------------------------------------------------------
# Frontmatter extraction / parsing
# ---------------------------------------------------------------------------

_FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)


def extract_frontmatter(raw: str) -> tuple[dict[str, Any], str, bool]:
    """Split Markdown into (metadata, body, has_frontmatter).

    Raises
    ------
    FrontmatterError
        If the file starts with ``---`` but the block is never closed, or
        the YAML block fails to parse.
    """
    if not raw.startswith("---"):
        return {}, raw, False

    match = _FRONT_MATTER_RE.match(raw)
    if not match:
        raise FrontmatterError(
            "File starts with a frontmatter fence but the block is never "
            "closed (unterminated ---).",
            path=None,
            code="unterminated_fence",
        )

    yaml_block = match.group(1)
    body = raw[match.end():]
    # Strip one leading blank line from the body for cleanliness
    if body.startswith("\n"):
        body = body[1:]

    try:
        metadata = parse_yaml_subset(yaml_block)
    except YamlSyntaxError as exc:
        raise FrontmatterError(
            f"Malformed YAML frontmatter: {exc.detail}",
            path=None,
            code="malformed_yaml",
        ) from exc

    return metadata, body, True