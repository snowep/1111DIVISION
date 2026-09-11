"""Tests for jarvis.persona.activation — activate, deactivate, domain match, resolve."""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.persona.activation import (
    ActivationError,
    activate,
    compose_context,
    deactivate,
    match_by_domains,
    resolve_persona,
)
from jarvis.persona.manager import scan_definitions
from jarvis.persona.models import (
    ActivationMode,
    AuditAction,
    PersonaDefinition,
    PersonaRegistry,
    PersonaStatus,
    PersonaType,
    RuntimeState,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_registry() -> PersonaRegistry:
    """Build a small in-memory registry for unit tests."""
    r = PersonaRegistry()
    r.add(PersonaDefinition(
        id="persona.alice",
        name="Alice",
        type=PersonaType.SPECIALIST,
        status=PersonaStatus.ACTIVE,
        activation=ActivationMode.EXPLICIT,
        domains=("logic", "mathematics"),
        raw_body="# Alice\n\nLogic specialist.",
    ))
    r.add(PersonaDefinition(
        id="persona.bob",
        name="Bob",
        type=PersonaType.HISTORICAL,
        status=PersonaStatus.ACTIVE,
        activation=ActivationMode.BOTH,
        domains=("strategy", "leadership", "logic"),
        raw_body="# Bob\n\nStrategic leader.",
    ))
    r.add(PersonaDefinition(
        id="persona.candidate",
        name="Candidate",
        type=PersonaType.SPECIALIST,
        status=PersonaStatus.CANDIDATE,
        activation=ActivationMode.EXPLICIT,
        domains=("testing",),
        raw_body="# Candidate\n\nNot yet active.",
    ))
    return r


# ---------------------------------------------------------------------------
# Resolve
# ---------------------------------------------------------------------------

class TestResolvePersona:
    """Tests for persona resolution from a request string."""

    def test_resolve_by_id(self):
        r = _make_registry()
        p = resolve_persona(r, "persona.alice")
        assert p is not None
        assert p.id == "persona.alice"

    def test_resolve_by_exact_name(self):
        r = _make_registry()
        p = resolve_persona(r, "Alice")
        assert p is not None
        assert p.id == "persona.alice"

    def test_resolve_by_name_case_insensitive(self):
        r = _make_registry()
        p = resolve_persona(r, "alice")
        assert p is not None
        assert p.id == "persona.alice"

    def test_resolve_by_fuzzy_substring(self):
        r = _make_registry()
        p = resolve_persona(r, "bob the builder")
        assert p is not None
        assert p.id == "persona.bob"

    def test_resolve_no_match(self):
        r = _make_registry()
        p = resolve_persona(r, "Napoleon")
        assert p is None

    def test_resolve_empty_string(self):
        r = _make_registry()
        p = resolve_persona(r, "")
        assert p is None


# ---------------------------------------------------------------------------
# Domain matching
# ---------------------------------------------------------------------------

class TestMatchByDomains:
    """Tests for domain-based implicit persona matching."""

    def test_single_domain_match(self):
        r = _make_registry()
        matches = match_by_domains(r, {"mathematics"})
        ids = [p.id for p, _ in matches]
        assert "persona.alice" in ids
        assert "persona.bob" not in ids  # Bob has no "mathematics"

    def test_multi_domain_ranking(self):
        r = _make_registry()
        # Bob has strategy+leadership+logic (3 domains), Alice has logic+mathematics (2)
        # Querying {logic} → both match, but score differs
        matches = match_by_domains(r, {"logic"})
        assert len(matches) == 2
        # Both have "logic" in their domains
        ids = {p.id for p, _ in matches}
        assert "persona.alice" in ids
        assert "persona.bob" in ids

    def test_excludes_candidate(self):
        r = _make_registry()
        matches = match_by_domains(r, {"testing"})
        # Candidate has "testing" but is not activatable
        assert len(matches) == 0

    def test_empty_query(self):
        r = _make_registry()
        matches = match_by_domains(r, set())
        assert matches == []

    def test_no_overlap(self):
        r = _make_registry()
        matches = match_by_domains(r, {"cooking", "painting"})
        assert matches == []

    def test_threshold_filtering(self):
        r = _make_registry()
        # Query {logic, mathematics}: Alice has both (score 1.0), Bob has only logic (score 0.5)
        # With threshold=0.6, only Alice qualifies
        matches = match_by_domains(r, {"logic", "mathematics"}, threshold=0.6)
        assert len(matches) == 1
        assert matches[0][0].id == "persona.alice"
        assert matches[0][1] == 1.0

    def test_threshold_filters_out_partial(self):
        r = _make_registry()
        # Query {strategy, leadership, logic, mathematics}: Bob has 3/4=0.75, Alice has 1/4=0.25
        matches = match_by_domains(r, {"strategy", "leadership", "logic", "mathematics"}, threshold=0.8)
        # Neither reaches 0.8 — Bob=0.75, Alice=0.25
        assert len(matches) == 0


# ---------------------------------------------------------------------------
# Activate
# ---------------------------------------------------------------------------

class TestActivate:
    """Tests for persona activation."""

    def test_activate_success(self):
        r = _make_registry()
        state = RuntimeState()
        event = activate(r, state, "Alice", scope="testing activation")

        assert state.active is True
        assert state.persona_id == "persona.alice"
        assert state.scope == "testing activation"
        assert event.action == AuditAction.PERSONA_ACTIVATE
        assert event.target == "persona.alice"
        assert "activation_type" in event.details

    def test_activate_by_id(self):
        r = _make_registry()
        state = RuntimeState()
        event = activate(r, state, "persona.bob")

        assert state.persona_id == "persona.bob"
        assert event.target == "persona.bob"

    def test_activate_not_found(self):
        r = _make_registry()
        state = RuntimeState()
        with pytest.raises(ActivationError, match="not found"):
            activate(r, state, "Napoleon")

    def test_activate_candidate_rejected(self):
        r = _make_registry()
        state = RuntimeState()
        with pytest.raises(ActivationError, match="status"):
            activate(r, state, "Candidate")

    def test_activate_replaces_existing(self):
        """One overlay at a time — activating a second persona replaces the first."""
        r = _make_registry()
        state = RuntimeState()

        activate(r, state, "Alice")
        assert state.persona_id == "persona.alice"

        activate(r, state, "Bob")
        assert state.persona_id == "persona.bob"

    def test_activate_generates_valid_event(self):
        r = _make_registry()
        state = RuntimeState()
        event = activate(r, state, "Alice")

        assert event.event_id.startswith("EVT-")
        assert event.timestamp is not None
        assert event.to_dict()["action"] == "persona.activate"


# ---------------------------------------------------------------------------
# Deactivate
# ---------------------------------------------------------------------------

class TestDeactivate:
    """Tests for persona deactivation."""

    def test_deactivate_clears_state(self):
        r = _make_registry()
        state = RuntimeState()
        activate(r, state, "Alice")

        event = deactivate(state, reason="explicit")

        assert state.active is False
        assert state.persona_id is None
        assert state.scope == ""
        assert event is not None
        assert event.action == AuditAction.PERSONA_DEACTIVATE
        assert event.target == "persona.alice"
        assert event.details["reason"] == "explicit"

    def test_deactivate_no_overlay_returns_none(self):
        state = RuntimeState()
        event = deactivate(state)
        assert event is None

    def test_deactivate_records_actor(self):
        r = _make_registry()
        state = RuntimeState()
        activate(r, state, "Alice")

        from jarvis.persona.models import AuditActor
        event = deactivate(state, actor=AuditActor.USER)
        assert event.actor == AuditActor.USER

    def test_activate_deactivate_lifecycle(self):
        """Full lifecycle: activate → verify → deactivate → verify."""
        r = _make_registry()
        state = RuntimeState()

        # Activate
        activate(r, state, "Alice")
        assert state.has_overlay is True
        assert state.persona_id == "persona.alice"

        # Deactivate
        deactivate(state, reason="task_complete")
        assert state.has_overlay is False
        assert state.persona_id is None


# ---------------------------------------------------------------------------
# Compose
# ---------------------------------------------------------------------------

class TestComposeContext:
    """Tests for prompt context composition."""

    def test_compose_returns_body(self):
        r = _make_registry()
        persona = r.get("persona.alice")
        ctx = compose_context(persona, "solve this puzzle")
        assert "Logic specialist." in ctx
        assert "# Alice" in ctx

    def test_compose_strips_whitespace(self):
        p = PersonaDefinition(
            id="x", name="X", type=PersonaType.SPECIALIST,
            status=PersonaStatus.ACTIVE, activation=ActivationMode.EXPLICIT,
            domains=("test",), raw_body="\n\n  # X  \n\n  Body.  \n\n",
        )
        ctx = compose_context(p, "task")
        assert ctx.startswith("# X")
        assert ctx.endswith("Body.")


# ---------------------------------------------------------------------------
# Integration: scan → activate against real definitions
# ---------------------------------------------------------------------------

class TestIntegrationScanActivate:
    """End-to-end: scan the actual .jarvis/personas/definitions/ and activate."""

    REAL_DEFS = Path(__file__).resolve().parents[2] / ".jarvis" / "personas" / "definitions"

    @pytest.mark.skipif(
        not (Path(__file__).resolve().parents[2] / ".jarvis" / "personas" / "definitions").exists(),
        reason="Real definitions directory not present",
    )
    def test_scan_real_definitions(self):
        registry, errors = scan_definitions(self.REAL_DEFS)
        assert len(errors) == 0, f"Validation errors: {errors}"
        assert registry.count >= 7, f"Expected >= 7 personas, got {registry.count}"

    @pytest.mark.skipif(
        not (Path(__file__).resolve().parents[2] / ".jarvis" / "personas" / "definitions").exists(),
        reason="Real definitions directory not present",
    )
    def test_activate_steve_jobs(self):
        registry, _ = scan_definitions(self.REAL_DEFS)
        state = RuntimeState()
        event = activate(registry, state, "Steve Jobs", scope="test activation")

        assert state.persona_id == "persona.steve_jobs"
        assert event.action == AuditAction.PERSONA_ACTIVATE

        # Deactivate
        deactivate(state, reason="test complete")
        assert state.has_overlay is False
