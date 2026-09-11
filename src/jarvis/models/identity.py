"""Identity model — canonical JARVIS identity.

Loads only from ``.jarvis/core/identity.md``.  Never from Open WebUI
configuration.  The identity is the "who" behind every operation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Identity:
    """The canonical JARVIS identity, parsed from ``.jarvis/core/identity.md``.

    ``source_path`` is always inside ``.jarvis/core/``.  A loader refusing
    any other source guards the "never from Open WebUI config" rule.
    """

    name: str
    role: str
    primary_user: str
    nature: str
    core_purpose: str
    philosophy: str
    personality: tuple[str, ...] = ()
    persona_constraints: tuple[str, ...] = ()
    source_path: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "role": self.role,
            "primary_user": self.primary_user,
            "nature": self.nature,
            "core_purpose": self.core_purpose,
            "philosophy": self.philosophy,
            "personality": list(self.personality),
            "persona_constraints": list(self.persona_constraints),
            "source_path": self.source_path,
        }


@dataclass(frozen=True)
class IdentitySource:
    """Where an identity *may* be loaded from.

    Canonical locations only — this is the explicit whitelist that keeps
    Open WebUI configuration (and any other platform config) out of the
    identity path.
    """

    kind: str  # e.g. "canonical-file"
    description: str
    path: Optional[str] = None