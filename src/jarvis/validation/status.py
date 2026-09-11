"""Status vocabulary — the canonical state-machine values.

Derived from ``.jarvis/memory/index.md`` (state machine + metadata fields)
and ``.jarvis/memory/gate-protocol.md``.
"""

from __future__ import annotations

# Lifecycle statuses from the memory state machine
STATE_STATUS_VALUES: frozenset[str] = frozenset({
    "observed",
    "interpreted",
    "candidate",
    "verified",
    "active",
    "superseded",
    "deprecated",
    "rejected",
})

# Persona document statuses (Rule 30 / persona definitions)
PERSONA_STATUS_VALUES: frozenset[str] = frozenset({
    "active",
    "candidate",
    "deprecated",
})

# Full vocabulary used by the kernel validators
VALID_STATUS_VALUES: frozenset[str] = (
    STATE_STATUS_VALUES | PERSONA_STATUS_VALUES
)

ACTOR_VALUES: frozenset[str] = frozenset({
    "user",
    "jarvis",
    "tool",
    "system",
    "council",
    "external",
    "automation",
})

MEMORY_TYPES: frozenset[str] = frozenset({
    "user-preference",
    "project-decision",
    "episodic",
    "knowledge",
    "project-observation",
    "candidate",
    "lesson",
    "research",
})

AUTHORITY_VALUES: frozenset[str] = frozenset({
    "user-explicit",
    "user-implicit",
    "external-information",
    "inference",
    "system",
    "project-observation",
})

APPROVAL_VALUES: frozenset[str] = frozenset({
    "explicit",
    "implicit",
    "none",
})


class StatusVocabulary:
    """Convenience accessor for the canonical status vocabulary."""

    @staticmethod
    def is_state_status(value: str) -> bool:
        return value in STATE_STATUS_VALUES

    @staticmethod
    def is_valid_status(value: str) -> bool:
        return value in VALID_STATUS_VALUES

    @staticmethod
    def valid_actors() -> frozenset[str]:
        return ACTOR_VALUES

    @staticmethod
    def is_valid_actor(value: str) -> bool:
        return value in ACTOR_VALUES