"""Data models for the persona system.

No external dependencies. Pure stdlib dataclasses.
Everything here is a plain data structure — no I/O, no file access.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PersonaStatus(str, enum.Enum):
    ACTIVE = "active"
    CANDIDATE = "candidate"
    DEPRECATED = "deprecated"


class ActivationMode(str, enum.Enum):
    EXPLICIT = "explicit"
    IMPLICIT = "implicit"
    BOTH = "both"


class ActivationType(str, enum.Enum):
    EXPLICIT = "explicit"
    IMPLICIT = "implicit"
    COUNCIL = "council"


class PersonaType(str, enum.Enum):
    HISTORICAL = "historical-persona"
    SPECIALIST = "specialist-persona"


class AuditActor(str, enum.Enum):
    USER = "user"
    JARVIS = "jarvis"
    TOOL = "tool"
    SYSTEM = "system"
    COUNCIL = "council"
    EXTERNAL = "external"
    AUTOMATION = "automation"


class AuditAction(str, enum.Enum):
    PERSONA_ACTIVATE = "persona.activate"
    PERSONA_DEACTIVATE = "persona.deactivate"


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PersonaDefinition:
    """A single persona parsed from a definition file.

    Immutable once created.  The ``raw_body`` holds everything after the
    YAML frontmatter fence so downstream consumers (e.g. prompt assembly)
    can use it without re-reading the file.
    """

    id: str
    name: str
    type: PersonaType
    status: PersonaStatus
    activation: ActivationMode
    domains: tuple[str, ...]
    raw_body: str = ""
    source_path: str = ""

    # -- derived helpers ----------------------------------------------------

    @property
    def activatable(self) -> bool:
        """Can this persona be activated right now?"""
        return self.status == PersonaStatus.ACTIVE

    def matches_domains(self, query_domains: set[str]) -> float:
        """Return overlap ratio between this persona's domains and *query_domains*.

        0.0 = no overlap, 1.0 = perfect overlap (all query domains present).
        Used for implicit activation ranking.
        """
        if not query_domains or not self.domains:
            return 0.0
        persona_set = set(self.domains)
        overlap = query_domains & persona_set
        return len(overlap) / len(query_domains)


@dataclass
class PersonaRegistry:
    """In-memory registry built by scanning definition files.

    NOT the on-disk ``registry.md`` — this is the live, code-level source
    of truth.  ``registry.md`` is a derived/convenience snapshot.
    """

    personas: dict[str, PersonaDefinition] = field(default_factory=dict)
    built_at: Optional[datetime] = None

    def add(self, persona: PersonaDefinition) -> None:
        self.personas[persona.id] = persona

    def get(self, persona_id: str) -> Optional[PersonaDefinition]:
        return self.personas.get(persona_id)

    def activatable(self) -> list[PersonaDefinition]:
        """Return all personas that can currently be activated."""
        return [p for p in self.personas.values() if p.activatable]

    def find_by_name(self, name: str) -> Optional[PersonaDefinition]:
        """Case-insensitive name lookup."""
        lower = name.lower()
        for p in self.personas.values():
            if p.name.lower() == lower:
                return p
        return None

    def find_by_domain(self, query_domains: set[str]) -> list[tuple[PersonaDefinition, float]]:
        """Rank activatable personas by domain overlap.

        Returns list of (persona, score) sorted descending by score.
        """
        scored = []
        for p in self.activatable():
            score = p.matches_domains(query_domains)
            if score > 0:
                scored.append((p, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    @property
    def count(self) -> int:
        return len(self.personas)


# ---------------------------------------------------------------------------
# Runtime state
# ---------------------------------------------------------------------------

@dataclass
class RuntimeState:
    """Tracks the currently active persona overlay.

    This maps to ``.jarvis/personas/runtime.md`` on disk but lives in
    memory during execution.  One overlay at a time (except council mode
    which is strictly sequential).
    """

    active: bool = False
    persona_id: Optional[str] = None
    activated_at: Optional[datetime] = None
    activation_type: Optional[ActivationType] = None
    scope: str = ""

    @property
    def has_overlay(self) -> bool:
        return self.active and self.persona_id is not None

    def clear(self) -> None:
        """Return to baseline JARVIS identity."""
        self.active = False
        self.persona_id = None
        self.activated_at = None
        self.activation_type = None
        self.scope = ""


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AuditEvent:
    """An immutable audit record for a persona state transition."""

    event_id: str
    timestamp: datetime
    actor: AuditActor
    action: AuditAction
    target: str  # persona_id
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor.value,
            "action": self.action.value,
            "target": self.target,
            "details": self.details,
        }
