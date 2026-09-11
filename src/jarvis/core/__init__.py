"""Core canonical loaders.

Two responsibilities:

1. ``MarkdownLoader``   — read a Markdown file with YAML frontmatter,
   returning a typed :class:`MarkdownDocument`.
2. ``IdentityLoader``   — load the canonical JARVIS identity, restricted
   to ``.jarvis/core/`` (never Open WebUI config).
"""

from jarvis.core.document import load_document
from jarvis.core.identity import load_identity
from jarvis.core.memory import load_memory_record

__all__ = ["load_document", "load_identity", "load_memory_record"]