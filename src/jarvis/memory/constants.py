"""Shared constants for the memory system (no circular imports)."""
from __future__ import annotations

from datetime import datetime, timezone


class MemoryError(Exception):
    """Raised when a memory operation violates a rule."""


# Lifecycle phases a canonical vault note can be in.
PHASES: tuple[str, ...] = (
    "OBSERVED", "INTERPRETED", "CANDIDATE",
    "VERIFIED", "ACTIVE", "SUPERSEDED", "REJECTED", "DEPRECATED",
)

# Routing matrix: memory type -> vault subdirectory (canonical).
# The value MUST be a valid store kind (lowercase, [a-z0-9_-]) — it is
# used directly as the subdirectory under vault/.
ROUTING: dict[str, str] = {
    "episodic": "episodic",
    "semantic": "semantic",
    "procedural": "procedural",
    "decisions": "decisions",
    "learned": "learned",
}

# Human descriptions of each memory type (display only, not routing).
ROUTING_DESCRIPTIONS: dict[str, str] = {
    "episodic": "what happened (events, sessions, terminal history)",
    "semantic": "facts and preferences that persist (world model)",
    "procedural": "how-to knowledge and standing procedures",
    "decisions": "architecture and project decisions + rationale",
    "learned": "lessons extracted from failures and successes",
}

# Valid phase transitions. Extensible as the state machine grows.
VALID_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "OBSERVED": ("INTERPRETED", "VERIFIED", "SUPERSEDED", "REJECTED"),
    "INTERPRETED": ("CANDIDATE", "VERIFIED", "REJECTED", "SUPERSEDED"),
    "CANDIDATE": ("VERIFIED", "REJECTED", "SUPERSEDED"),
    "VERIFIED": ("ACTIVE", "SUPERSEDED", "DEPRECATED"),
    "ACTIVE": ("SUPERSEDED", "DEPRECATED"),
    "SUPERSEDED": (),
    "REJECTED": (),
    "DEPRECATED": (),
}


def now() -> str:
    """UTC timestamp in ISO-8601 with second precision."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def phase_of(metadata: dict) -> str:
    """Read the lifecycle phase of a note, defaulting by kind."""
    phase = metadata.get("phase")
    if phase is not None:
        return str(phase).upper()
    return "OBSERVED"