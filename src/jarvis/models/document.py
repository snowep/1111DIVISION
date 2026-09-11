"""Markdown document model — typed result of the Markdown/YAML loader.

A :class:`MarkdownDocument` is one canonical file: its YAML frontmatter
(metadata) plus its markdown body, plus its resolved paths.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MarkdownDocument:
    """A Markdown file with (optional) YAML frontmatter, parsed and loaded.

    Attributes
    ----------
    source_path
        Absolute path of the file on disk.
    relative_path
        Path relative to the workspace root (POSIX-style, e.g. ``.jarvis/core/identity.md``).
    metadata
        Parsed YAML frontmatter as a mapping.  Empty when the file has no frontmatter.
    body
        Markdown body — everything after the frontmatter fence.  The leading
        blank line(s) after the closing ``---`` are stripped.
    has_frontmatter
        Whether the file actually contained a frontmatter block.
    """

    source_path: str
    relative_path: str
    metadata: dict[str, Any] = field(default_factory=dict)
    body: str = ""
    has_frontmatter: bool = False

    @property
    def name(self) -> str:
        """Basename of the source file."""
        return Path(self.source_path).name

    def metadata_get(self, key: str, default: Any = None) -> Any:
        """Typed accessor for a metadata field."""
        return self.metadata.get(key, default)

    def to_dict(self) -> dict:
        return {
            "source_path": self.source_path,
            "relative_path": self.relative_path,
            "metadata": dict(self.metadata),
            "body": self.body,
            "has_frontmatter": self.has_frontmatter,
        }