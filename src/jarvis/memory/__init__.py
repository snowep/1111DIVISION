"""memory: Obsidian-compatible long-term memory on top of the docstore.

The vault is a set of Markdown notes with YAML frontmatter that opens
directly in Obsidian (wikilinks, tag graph, `[[links]]`). Every note is
canonical and carries provenance + a lifecycle phase so we can answer:

    "why do I believe this?"    -> provenance chain
    "is this still true?"       -> valid_until / confidence / phase
"""
from jarvis.memory.constants import (
    MemoryError,
    PHASES,
    ROUTING,
    ROUTING_DESCRIPTIONS,
    VALID_TRANSITIONS,
    now,
    phase_of,
)
from jarvis.memory.engine import (
    MemoryNote,
    activate,
    forget_expired,
    list_active,
    parse_memory_note,
    provenance_chain,
    reject,
    remember,
    route,
    supersede,
    update_routing,
    verify,
)

__all__ = [
    "MemoryError", "MemoryNote", "PHASES", "ROUTING", "ROUTING_DESCRIPTIONS", "VALID_TRANSITIONS",
    "activate", "forget_expired", "list_active", "now", "parse_memory_note",
    "phase_of", "provenance_chain", "reject", "remember", "route",
    "supersede", "update_routing", "verify",
]