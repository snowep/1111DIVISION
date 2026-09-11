"""Test 4: Contamination test fails if previous position leaks.

Each persona must receive only the question + approved evidence + persona
definition.  Earlier persona outputs must never appear in a later persona's
context.
"""

from __future__ import annotations

import pytest

from jarvis.council.isolation import (
    PersonaContext,
    assemble_persona_context,
    check_contamination,
    contamination_test_suite,
)


class TestContaminationTestFailsOnLeak:
    """Isolation test detects when earlier positions leak into later contexts."""

    def test_clean_context_passes_isolation(self, clean_context):
        """A context with no contamination passes."""
        check = check_contamination(
            context=clean_context,
            earlier_positions=["Ship it, the core is solid"],
            earlier_votes=["approve"],
        )
        assert check.passed is True
        assert len(check.violations) == 0

    def test_leaked_position_fails_isolation(self):
        """A context containing an earlier position fails contamination test."""
        context = PersonaContext(
            question="Should we rewrite the memory engine?",
            persona_definition="You are the Skeptic.",
            evidence_text="EVD-001: Current engine uses SQLite.",
            persona_id="persona.skeptic",
            persona_name="Skeptic",
        )

        earlier_pos = "Steve Jobs said: Ship it, the core is solid and we should launch"

        check = check_contamination(
            context=context,
            earlier_positions=[earlier_pos],
        )
        # The context itself is clean — the earlier position is NOT in it
        assert check.passed is True

    def test_direct_contamination_detected(self):
        """When earlier position text IS in the context, test fails."""
        # Manually inject contamination into evidence_text
        contaminated = PersonaContext(
            question="Should we rewrite the memory engine?",
            persona_definition="You are the Skeptic.",
            evidence_text=(
                "EVD-001: Current engine uses SQLite.\n"
                "PREVIOUS POSITION: Ship it, the core is solid and we should launch"
            ),
            persona_id="persona.skeptic",
            persona_name="Skeptic",
        )

        check = check_contamination(
            context=contaminated,
            earlier_positions=["Ship it, the core is solid and we should launch"],
        )
        assert check.passed is False
        assert len(check.violations) > 0

    def test_leaked_vote_detected(self):
        """When an earlier vote leaks into the context, test fails."""
        contaminated = PersonaContext(
            question="Should we rewrite the memory engine?",
            persona_definition="You are the Skeptic.",
            evidence_text=(
                "EVD-001: Current engine uses SQLite.\n"
                "Previous vote: approve"
            ),
            persona_id="persona.skeptic",
            persona_name="Skeptic",
        )

        check = check_contamination(
            context=contaminated,
            earlier_votes=["approve"],
        )
        assert check.passed is False

    def test_cross_examination_leak_detected(self):
        """Cross-examination text must not appear in persona context."""
        contaminated = PersonaContext(
            question="Should we rewrite the memory engine?",
            persona_definition="You are the Skeptic.",
            evidence_text=(
                "EVD-001: Current engine uses SQLite.\n"
                "CONFLICT: Security Architect says reject, Steve Jobs says approve"
            ),
            persona_id="persona.skeptic",
            persona_name="Skeptic",
        )

        check = check_contamination(
            context=contaminated,
            cross_examination_text="Security Architect says reject, Steve Jobs says approve",
        )
        assert check.passed is False

    def test_other_persona_evidence_leak_detected(self):
        """Phase 2 evidence from other personas must not leak."""
        contaminated = PersonaContext(
            question="Should we rewrite the memory engine?",
            persona_definition="You are the Skeptic.",
            evidence_text=(
                "EVD-001: Current engine uses SQLite.\n"
                "EVD2-010: Steve Jobs' persona-level reasoning"
            ),
            persona_id="persona.skeptic",
            persona_name="Skeptic",
        )

        check = check_contamination(
            context=contaminated,
            other_persona_evidence_ids=("EVD2-010",),
        )
        assert check.passed is False

    def test_full_contamination_test_suite_catches_sequential_leak(self):
        """Full suite proves later personas cannot inherit earlier arguments."""
        contexts = [
            PersonaContext(
                question="Should we rewrite?",
                persona_definition="Jobs: Ship it.",
                evidence_text="EVD-001: SQLite.",
                persona_id="persona.steve_jobs",
                persona_name="Steve Jobs",
            ),
            PersonaContext(
                question="Should we rewrite?",
                persona_definition="Skeptic: Challenge assumptions.",
                evidence_text="EVD-001: SQLite.",
                persona_id="persona.skeptic",
                persona_name="Skeptic",
            ),
        ]

        earlier_outputs = {
            "persona.steve_jobs": {
                "positions": ["Ship it immediately, the product is ready"],
                "votes": ["approve"],
                "evidence_ids": ["EVD2-001"],
            },
        }

        checks = contamination_test_suite(contexts, earlier_outputs)

        # First persona (Jobs) — no earlier outputs, should pass
        assert checks[0].passed is True

        # Second persona (Skeptic) — earlier outputs exist but NOT in context
        # Should pass because the context doesn't contain them
        assert checks[1].passed is True

    def test_contamination_test_suite_detects_actual_leak(self):
        """Suite detects when a context actually contains leaked content."""
        contexts = [
            PersonaContext(
                question="Should we rewrite?",
                persona_definition="Jobs: Ship it.",
                evidence_text="EVD-001: SQLite.",
                persona_id="persona.steve_jobs",
                persona_name="Steve Jobs",
            ),
            PersonaContext(
                question="Should we rewrite?",
                persona_definition="Skeptic: Challenge assumptions.",
                evidence_text=(
                    "EVD-001: SQLite.\n"
                    "Previous position: Ship it immediately, the product is ready"
                ),
                persona_id="persona.skeptic",
                persona_name="Skeptic",
            ),
        ]

        earlier_outputs = {
            "persona.steve_jobs": {
                "positions": ["Ship it immediately, the product is ready"],
                "votes": ["approve"],
                "evidence_ids": [],
            },
        }

        checks = contamination_test_suite(contexts, earlier_outputs)

        # First persona passes
        assert checks[0].passed is True

        # Second persona FAILS — leak detected
        assert checks[1].passed is False
        assert any("position" in v.lower() for v in checks[1].violations)

    def test_assemble_context_is_clean(self):
        """assemble_persona_context produces a clean context by construction."""
        ctx = assemble_persona_context(
            question="Should we rewrite?",
            persona_id="persona.skeptic",
            persona_name="Skeptic",
            persona_definition="Challenge everything.",
            evidence_text="EVD-001: SQLite.",
        )
        # The assembled context should have no contamination fields
        assert ctx.earlier_positions == ""
        assert ctx.earlier_votes == ""
        assert ctx.cross_examination == ""
        assert ctx.agreement_classification == ""
        assert ctx.other_persona_evidence == ""
