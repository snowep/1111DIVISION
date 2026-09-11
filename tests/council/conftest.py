"""Shared fixtures for council epistemic layer tests."""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timezone

import pytest

# Ensure src is on path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from jarvis.council.evidence import (
    ClaimType,
    EvidenceClass,
    EvidenceRegistry,
    SourceType,
)
from jarvis.council.agreement import AgreementType, PositionVote
from jarvis.council.isolation import PersonaContext
from jarvis.council.grounding import ClaimOrigin


# ---------------------------------------------------------------------------
# Evidence fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def evidence_registry() -> EvidenceRegistry:
    """A fresh evidence registry for a test meeting."""
    return EvidenceRegistry(meeting_id="MEETING-TEST-001")


@pytest.fixture
def populated_registry() -> EvidenceRegistry:
    """Registry with 5 Phase 1 evidence items."""
    reg = EvidenceRegistry(meeting_id="MEETING-TEST-002")

    reg.register(
        claim_type=ClaimType.FACT,
        claim_text="The repository uses FastAPI for the backend",
        evidence_class=EvidenceClass.DIRECT_OBSERVATION,
        source="repo inspection",
        source_type=SourceType.PRIMARY,
        confidence=0.95,
        retrieved_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
        evidence_id="EVD-001",
    )

    reg.register(
        claim_type=ClaimType.FACT,
        claim_text="Deployment target is AWS ECS",
        evidence_class=EvidenceClass.PROJECT_ARTIFACT,
        source="docs/deployment.md",
        source_type=SourceType.PRIMARY,
        confidence=0.90,
        retrieved_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
        evidence_id="EVD-002",
    )

    reg.register(
        claim_type=ClaimType.INFERENCE,
        claim_text="Current architecture cannot handle >1000 concurrent users",
        evidence_class=EvidenceClass.RESEARCH_SYNTHESIS,
        source="performance analysis",
        source_type=SourceType.PRIMARY,
        confidence=0.70,
        retrieved_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
        supporting_evidence=("EVD-001",),
        evidence_id="EVD-003",
    )

    reg.register(
        claim_type=ClaimType.FACT,
        claim_text="User prefers PostgreSQL over MySQL",
        evidence_class=EvidenceClass.USER_TESTIMONY,
        source="conversation",
        source_type=SourceType.PRIMARY,
        confidence=0.90,
        retrieved_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
        evidence_id="EVD-004",
    )

    reg.register(
        claim_type=ClaimType.OPINION,
        claim_text="Rewriting the auth system would take 3 months",
        evidence_class=EvidenceClass.EXTERNAL_ARTICLE,
        source="engineering blog post",
        source_type=SourceType.SECONDARY,
        confidence=0.60,
        retrieved_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
        evidence_id="EVD-005",
    )

    return reg


# ---------------------------------------------------------------------------
# Vote fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def three_votes_unanimous() -> list[PositionVote]:
    """Three personas all approving — unanimous."""
    return [
        PositionVote(
            persona_id="persona.steve_jobs",
            persona_name="Steve Jobs",
            recommendation="approve",
            confidence=0.9,
            evidence_refs=("EVD-001", "EVD-002"),
            reasoning_summary="The architecture is clean and should ship",
        ),
        PositionVote(
            persona_id="persona.security_architect",
            persona_name="Security Architect",
            recommendation="approve",
            confidence=0.85,
            evidence_refs=("EVD-001", "EVD-003"),
            reasoning_summary="The architecture is clean and should ship",
        ),
        PositionVote(
            persona_id="persona.skeptic",
            persona_name="Skeptic",
            recommendation="approve",
            confidence=0.8,
            evidence_refs=("EVD-001",),
            reasoning_summary="The architecture is clean and should ship",
        ),
    ]


@pytest.fixture
def three_votes_split() -> list[PositionVote]:
    """Three personas split: approve, reject, approve-with-conditions."""
    return [
        PositionVote(
            persona_id="persona.steve_jobs",
            persona_name="Steve Jobs",
            recommendation="approve",
            confidence=0.9,
            evidence_refs=("EVD-001",),
            reasoning_summary="Ship it, the core is solid",
        ),
        PositionVote(
            persona_id="persona.security_architect",
            persona_name="Security Architect",
            recommendation="reject",
            confidence=0.85,
            evidence_refs=("EVD-003",),
            reasoning_summary="Cannot ship without rate limiting on auth endpoints",
        ),
        PositionVote(
            persona_id="persona.skeptic",
            persona_name="Skeptic",
            recommendation="approve-with-conditions",
            confidence=0.7,
            evidence_refs=("EVD-001", "EVD-005"),
            reasoning_summary="Ship with conditions: add monitoring before launch",
        ),
    ]


@pytest.fixture
def three_votes_qualified_agreement() -> list[PositionVote]:
    """Three personas: same recommendation, different reasoning."""
    return [
        PositionVote(
            persona_id="persona.steve_jobs",
            persona_name="Steve Jobs",
            recommendation="approve",
            confidence=0.9,
            evidence_refs=("EVD-001",),
            reasoning_summary="Product simplicity demands we ship now",
        ),
        PositionVote(
            persona_id="persona.security_architect",
            persona_name="Security Architect",
            recommendation="approve",
            confidence=0.85,
            evidence_refs=("EVD-003",),
            reasoning_summary="Security posture is adequate for launch risk level",
        ),
        PositionVote(
            persona_id="persona.skeptic",
            persona_name="Skeptic",
            recommendation="approve",
            confidence=0.7,
            evidence_refs=("EVD-005",),
            reasoning_summary="Cost of delay exceeds cost of known issues",
        ),
    ]


@pytest.fixture
def five_votes_majority_loses() -> list[PositionVote]:
    """Five personas where majority votes approve but evidence favors reject.

    This tests that evidence can override majority.
    """
    return [
        PositionVote(
            persona_id="persona.steve_jobs",
            persona_name="Steve Jobs",
            recommendation="approve",
            confidence=0.9,
            evidence_refs=("EVD-001",),
            reasoning_summary="Ship it",
        ),
        PositionVote(
            persona_id="persona.creative_director",
            persona_name="Creative Director",
            recommendation="approve",
            confidence=0.85,
            evidence_refs=("EVD-001",),
            reasoning_summary="Design is ready, launch momentum matters",
        ),
        PositionVote(
            persona_id="persona.business_strategist",
            persona_name="Business Strategist",
            recommendation="approve",
            confidence=0.8,
            evidence_refs=("EVD-001",),
            reasoning_summary="Market window is closing, ship now",
        ),
        PositionVote(
            persona_id="persona.security_architect",
            persona_name="Security Architect",
            recommendation="reject",
            confidence=0.95,
            evidence_refs=("EVD-003", "EVD-002"),
            reasoning_summary="Critical auth vulnerability must be fixed first — EVD-003 shows systemic risk",
        ),
        PositionVote(
            persona_id="persona.systems_engineer",
            persona_name="Systems Engineer",
            recommendation="reject",
            confidence=0.90,
            evidence_refs=("EVD-003", "EVD-002"),
            reasoning_summary="Architecture cannot handle load without auth rewrite — EVD-003 proves this",
        ),
    ]


# ---------------------------------------------------------------------------
# Persona context fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def clean_context() -> PersonaContext:
    """A clean persona context with no contamination."""
    return PersonaContext(
        question="Should we rewrite the memory engine?",
        persona_definition="You are the Systems Engineer. Focus on architecture.",
        evidence_text="EVD-001: The current engine uses SQLite.\nEVD-002: Load testing shows 500 req/s max.",
        persona_id="persona.systems_engineer",
        persona_name="Systems Engineer",
    )


@pytest.fixture
def contaminated_context() -> PersonaContext:
    """A persona context that contains leaked content from earlier positions."""
    return PersonaContext(
        question="Should we rewrite the memory engine?",
        persona_definition="You are the Systems Engineer. Focus on architecture.",
        evidence_text="EVD-001: The current engine uses SQLite.",
        persona_id="persona.skeptic",
        persona_name="Skeptic",
        # This is the contamination — earlier position leaked in
        earlier_positions="Steve Jobs said: Ship it, the core is solid",
    )
