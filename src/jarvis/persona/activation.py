"""Persona activation — activate, deactivate, domain-match, audit.

This module consumes a PersonaRegistry and a RuntimeState and performs
the state transitions defined in activation-protocol.md.

No file I/O.  Audit events are returned, not written — the caller
decides where to persist them.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Optional

from .models import (
    AuditAction,
    AuditActor,
    AuditEvent,
    PersonaDefinition,
    PersonaRegistry,
    PersonaStatus,
    RuntimeState,
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class ActivationError(Exception):
    """Raised when activation or deactivation fails."""

    def __init__(self, message: str, persona_id: Optional[str] = None):
        self.persona_id = persona_id
        super().__init__(message)


# ---------------------------------------------------------------------------
# Audit event factory
# ---------------------------------------------------------------------------

def _make_event_id() -> str:
    """Generate a unique event ID: EVT-<timestamp>-<random>."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    rand = secrets.token_hex(4)
    return f"EVT-{ts}-{rand}"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _audit_event(
    action: AuditAction,
    target: str,
    actor: AuditActor = AuditActor.JARVIS,
    **details: object,
) -> AuditEvent:
    return AuditEvent(
        event_id=_make_event_id(),
        timestamp=_now_utc(),
        actor=actor,
        action=action,
        target=target,
        details=dict(details),
    )


# ---------------------------------------------------------------------------
# Resolve
# ---------------------------------------------------------------------------

def resolve_persona(
    registry: PersonaRegistry,
    request: str,
) -> Optional[PersonaDefinition]:
    """Resolve a user request to a persona definition.

    Tries, in order:
      1. Exact ID match (e.g. "persona.steve_jobs")
      2. Exact name match (case-insensitive, e.g. "Steve Jobs")
      3. Substring: persona name appears in the request (e.g. "act as jobs" → Steve Jobs)
      4. Substring: request words appear in persona name (e.g. "bob the builder" → Bob)

    Returns None if no match found.
    """
    if not request or not request.strip():
        return None

    # 1. Exact ID
    by_id = registry.get(request)
    if by_id:
        return by_id

    # 2. Exact name
    by_name = registry.find_by_name(request)
    if by_name:
        return by_name

    request_lower = request.lower()
    name_lower_map = {p: p.name.lower() for p in registry.personas.values()}

    # 3. Persona name appears in the request
    for persona, name_l in name_lower_map.items():
        if name_l in request_lower:
            return persona

    # 4. Any request word matches persona name
    request_words = set(request_lower.split())
    for persona, name_l in name_lower_map.items():
        name_words = set(name_l.split())
        if request_words & name_words:
            return persona

    return None


# ---------------------------------------------------------------------------
# Domain matching (for implicit activation)
# ---------------------------------------------------------------------------

def match_by_domains(
    registry: PersonaRegistry,
    query_domains: set[str],
    threshold: float = 0.5,
) -> list[tuple[PersonaDefinition, float]]:
    """Find personas matching the given domains above *threshold*.

    Returns ranked list of (persona, score).  Empty if nothing qualifies.
    """
    if not query_domains:
        return []

    ranked = registry.find_by_domain(query_domains)
    return [(p, s) for p, s in ranked if s >= threshold]


# ---------------------------------------------------------------------------
# Activate
# ---------------------------------------------------------------------------

def activate(
    registry: PersonaRegistry,
    state: RuntimeState,
    persona_id: str,
    activation_type: str = "explicit",
    scope: str = "",
    actor: AuditActor = AuditActor.USER,
) -> AuditEvent:
    """Activate a persona overlay.

    Steps (per activation-protocol.md):
      1. Resolve persona from registry
      2. Validate status is active
      3. If another persona is active, deactivate it first (one overlay at a time)
      4. Set runtime state
      5. Return audit event

    Raises ActivationError on failure.
    """
    # Resolve
    persona = resolve_persona(registry, persona_id)
    if persona is None:
        raise ActivationError(
            f"Persona '{persona_id}' not found in registry",
            persona_id=persona_id,
        )

    # Validate activatable
    if not persona.activatable:
        raise ActivationError(
            f"Persona '{persona.name}' has status '{persona.status.value}' "
            f"— only 'active' personas can be activated",
            persona_id=persona.id,
        )

    # One overlay at a time — deactivate existing first
    if state.has_overlay:
        # We don't generate a separate deactivation event here;
    # the caller should handle that explicitly.  We just clear.
        state.clear()

    # Activate
    state.active = True
    state.persona_id = persona.id
    state.activated_at = _now_utc()
    state.activation_type = activation_type  # stored as string to stay flexible
    state.scope = scope

    return _audit_event(
        action=AuditAction.PERSONA_ACTIVATE,
        target=persona.id,
        actor=actor,
        activation_type=activation_type,
        scope=scope,
        persona_name=persona.name,
    )


# ---------------------------------------------------------------------------
# Deactivate
# ---------------------------------------------------------------------------

def deactivate(
    state: RuntimeState,
    reason: str = "explicit",
    actor: AuditActor = AuditActor.USER,
) -> Optional[AuditEvent]:
    """Deactivate the current persona overlay.

    Returns the audit event, or None if no overlay was active.
    """
    if not state.has_overlay:
        return None

    persona_id = state.persona_id or "unknown"
    state.clear()

    return _audit_event(
        action=AuditAction.PERSONA_DEACTIVATE,
        target=persona_id,
        actor=actor,
        reason=reason,
    )


# ---------------------------------------------------------------------------
# Compose (for prompt assembly)
# ---------------------------------------------------------------------------

def compose_context(
    persona: PersonaDefinition,
    task: str,
) -> str:
    """Compose the persona overlay text for prompt injection.

    Returns the raw body of the definition file (which contains the
    identity, perspective, questions, communication style, biases,
    and constraints).  The caller (JARVIS prompt assembler) prepends
    the core JARVIS identity and appends the current task.
    """
    return persona.raw_body.strip()
