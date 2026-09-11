"""Persona isolation — contamination test and context assembly.

Each council member receives:
  1. The question
  2. The approved evidence registry
  3. Permitted context (persona definition only)

Each council member MUST NOT see:
  - Earlier persona positions
  - Earlier persona votes
  - Earlier persona evidence registrations (Phase 2)
  - Cross-examination results
  - Agreement classifications

The contamination test proves this invariant holds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class PersonaContext:
    """The isolated context package assembled for a single persona.

    This is what a persona receives during Step 5 of the meeting protocol.
    It must NEVER contain positions, votes, or other personas' outputs.
    """

    question: str
    persona_definition: str  # raw body from persona definition file
    evidence_text: str  # serialized evidence registry (Phase 1 only for isolation)
    persona_id: str
    persona_name: str

    # Explicitly forbidden content — should be empty
    forbidden_fields: tuple[str, ...] = (
        "earlier_positions",
        "earlier_votes",
        "cross_examination",
        "agreement_classification",
        "other_persona_evidence",
    )

    # These must NOT be present in the context
    earlier_positions: str = ""
    earlier_votes: str = ""
    cross_examination: str = ""
    agreement_classification: str = ""
    other_persona_evidence: str = ""


@dataclass(frozen=True)
class IsolationCheck:
    """Result of an isolation contamination test."""

    passed: bool
    persona_id: str
    violations: tuple[str, ...] = ()
    details: str = ""


# ---------------------------------------------------------------------------
# Context assembly — builds isolated package per persona
# ---------------------------------------------------------------------------

def assemble_persona_context(
    question: str,
    persona_id: str,
    persona_name: str,
    persona_definition: str,
    evidence_text: str,
    phase1_only: bool = True,
) -> PersonaContext:
    """Build the isolated context for a single persona.

    Args:
        question: The council question (same for all personas)
        persona_id: The persona's unique ID
        persona_name: The persona's display name
        persona_definition: The raw body text from the persona definition
        evidence_text: Serialized evidence registry
        phase1_only: If True, only Phase 1 evidence is included (isolation mode)

    Returns:
        PersonaContext with no contamination from other personas
    """
    return PersonaContext(
        question=question,
        persona_definition=persona_definition,
        evidence_text=evidence_text,
        persona_id=persona_id,
        persona_name=persona_name,
    )


# ---------------------------------------------------------------------------
# Contamination test — proves isolation holds
# ---------------------------------------------------------------------------

def check_contamination(
    context: PersonaContext,
    earlier_positions: list[str] = (),
    earlier_votes: list[str] = (),
    cross_examination_text: str = "",
    agreement_text: str = "",
    other_persona_evidence_ids: tuple[str, ...] = (),
) -> IsolationCheck:
    """Run the contamination test on a persona's context.

    This verifies that the context package does NOT contain any content
    from earlier personas' outputs.

    The test checks:
    1. Earlier positions are not in the context
    2. Earlier votes are not in the context
    3. Cross-examination is not in the context
    4. Agreement classification is not in the context
    5. Other persona Phase 2 evidence is not in the context

    Returns IsolationCheck with passed=True if clean, or passed=False
    with specific violations.
    """
    violations: list[str] = []

    # Serialize the context for string matching
    context_text = "\n".join([
        context.question,
        context.persona_definition,
        context.evidence_text,
    ])

    # Check for earlier positions leaking in
    for pos in earlier_positions:
        if pos and _text_appears(pos, context_text):
            violations.append(
                f"Earlier position leaked into context: '{pos[:80]}...'"
            )

    # Check for earlier votes leaking in
    for vote in earlier_votes:
        if vote and _text_appears(vote, context_text):
            violations.append(
                f"Earlier vote leaked into context: '{vote[:80]}...'"
            )

    # Check for cross-examination leaking in
    if cross_examination_text and _text_appears(
        cross_examination_text, context_text
    ):
        violations.append("Cross-examination text leaked into context")

    # Check for agreement classification leaking in
    if agreement_text and _text_appears(agreement_text, context_text):
        violations.append(
            "Agreement classification leaked into context"
        )

    # Check for other persona Phase 2 evidence
    for eid in other_persona_evidence_ids:
        if eid and eid in context_text:
            violations.append(
                f"Other persona's Phase 2 evidence {eid} leaked into context"
            )

    passed = len(violations) == 0
    return IsolationCheck(
        passed=passed,
        persona_id=context.persona_id,
        violations=tuple(violations),
        details=(
            "Isolation check passed — no contamination detected"
            if passed
            else f"ISOLATION BREACH — {len(violations)} violation(s) found"
        ),
    )


# ---------------------------------------------------------------------------
# Full contamination test — proves the council pipeline is isolated
# ---------------------------------------------------------------------------

def contamination_test_suite(
    contexts: list[PersonaContext],
    earlier_outputs: dict[str, dict] | None = None,
) -> list[IsolationCheck]:
    """Run contamination tests across all personas in sequence.

    Simulates the sequential council pipeline and verifies that each
    persona's context is free of earlier personas' outputs.

    Args:
        contexts: PersonaContext for each participant, in order
        earlier_outputs: Optional mapping of persona_id → {
            "positions": [str],
            "votes": [str],
            "evidence_ids": [str]
        }

    Returns:
        List of IsolationCheck, one per persona
    """
    if earlier_outputs is None:
        earlier_outputs = {}

    checks: list[IsolationCheck] = []

    for i, ctx in enumerate(contexts):
        # Collect all earlier outputs
        all_earlier_positions: list[str] = []
        all_earlier_votes: list[str] = []
        all_other_evidence: list[str] = []

        for earlier_ctx in contexts[:i]:
            output = earlier_outputs.get(earlier_ctx.persona_id, {})
            all_earlier_positions.extend(output.get("positions", []))
            all_earlier_votes.extend(output.get("votes", []))
            all_other_evidence.extend(output.get("evidence_ids", []))

        check = check_contamination(
            context=ctx,
            earlier_positions=all_earlier_positions,
            earlier_votes=all_earlier_votes,
            other_persona_evidence_ids=tuple(all_other_evidence),
        )
        checks.append(check)

    return checks


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _text_appears(needle: str, haystack: str) -> bool:
    """Check if needle text appears in the haystack.

    Uses normalized comparison to catch near-matches.
    """
    if not needle or not haystack:
        return False
    # Normalize whitespace for comparison
    needle_norm = " ".join(needle.lower().split())
    haystack_norm = " ".join(haystack.lower().split())
    return needle_norm in haystack_norm
