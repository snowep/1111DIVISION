"""Test 5: Historical persona cannot invent private claims.

Historical personas must distinguish documented from simulated reasoning.
Private beliefs, quotes, and undocumented claims are never fabricated.
"""

from __future__ import annotations

import pytest

from jarvis.council.grounding import (
    ClaimOrigin,
    GroundedClaim,
    GroundingResult,
    ground_claim,
    ground_position,
)


class TestHistoricalPersonaCannotInventPrivateClaims:
    """Historical personas are grounded in documented views, not fabrication."""

    def test_documented_view_is_classified_documented(self):
        """A claim matching a documented view is classified DOCUMENTED."""
        claim = ground_claim(
            claim_text="Simplicity is the ultimate sophistication",
            persona_id="persona.steve_jobs",
            persona_name="Steve Jobs",
            is_historical=True,
            documented_views=("Simplicity is the ultimate sophistication",),
        )
        assert claim.origin == ClaimOrigin.DOCUMENTED

    def test_simulated_reasoning_is_classified_simulated(self):
        """A claim not in documented views is classified SIMULATED."""
        claim = ground_claim(
            claim_text="We should use a microservices architecture",
            persona_id="persona.steve_jobs",
            persona_name="Steve Jobs",
            is_historical=True,
            documented_views=("Simplicity is the ultimate sophistication",),
        )
        assert claim.origin == ClaimOrigin.SIMULATED
        assert "Simulated reasoning" in claim.caveat

    def test_fabrication_pattern_detected(self):
        """Claims containing fabrication patterns are UNSUPPORTED."""
        claim = ground_claim(
            claim_text="In private, I think microservices are overrated",
            persona_id="persona.steve_jobs",
            persona_name="Steve Jobs",
            is_historical=True,
            documented_views=(),
        )
        assert claim.origin == ClaimOrigin.UNSUPPORTED
        assert "fabrication" in claim.caveat.lower()

    def test_multiple_fabrication_patterns_detected(self):
        """Various fabrication patterns are all detected."""
        patterns = [
            "I personally believe this is wrong",
            "My secret opinion is that we should stop",
            "Behind closed doors, we discussed this",
            "What I never told anyone is that...",
            "Off the record, I think the design is broken",
        ]
        for text in patterns:
            claim = ground_claim(
                claim_text=text,
                persona_id="persona.steve_jobs",
                persona_name="Steve Jobs",
                is_historical=True,
            )
            assert claim.origin == ClaimOrigin.UNSUPPORTED, (
                f"Pattern not detected: '{text}'"
            )

    def test_specialist_persona_doesnt_need_historical_grounding(self):
        """Specialist personas (non-historical) are always SIMULATED."""
        claim = ground_claim(
            claim_text="The architecture has a single point of failure",
            persona_id="persona.security_architect",
            persona_name="Security Architect",
            is_historical=False,
        )
        assert claim.origin == ClaimOrigin.SIMULATED
        assert "Specialist persona" in claim.caveat

    def test_ground_position_counts_violations(self):
        """ground_position tallies documented, simulated, and unsupported."""
        result = ground_position(
            persona_id="persona.steve_jobs",
            persona_name="Steve Jobs",
            is_historical=True,
            claims=[
                {"text": "Simplicity matters above all", "evidence_id": None,
                 "source": None},
                {"text": "We should use React", "evidence_id": None,
                 "source": None},
                {"text": "In private, I hated the iPhone design",
                 "evidence_id": None, "source": None},
            ],
            documented_views=("Simplicity matters above all",),
        )
        assert result.documented_count >= 1
        assert result.simulated_count >= 1
        assert result.unsupported_count >= 1
        assert result.has_violations

    def test_documented_with_source_reference(self):
        """A claim with evidence + source reference is DOCUMENTED."""
        claim = ground_claim(
            claim_text="Design is how it works",
            persona_id="persona.steve_jobs",
            persona_name="Steve Jobs",
            is_historical=True,
            evidence_id="EVD-001",
            source_reference="https://example.com/interview",
        )
        assert claim.origin == ClaimOrigin.DOCUMENTED
        assert claim.source_reference == "https://example.com/interview"

    def test_response_remains_jarvis(self):
        """The grounding result attributes to persona but caveats it."""
        result = ground_position(
            persona_id="persona.steve_jobs",
            persona_name="Steve Jobs",
            is_historical=True,
            claims=[
                {"text": "Ship it", "evidence_id": None, "source": None},
            ],
        )
        # The result knows this is simulated reasoning
        assert result.is_historical is True
        for claim in result.claims:
            # Either documented or simulated — never "this is actually Steve Jobs"
            assert claim.origin in (ClaimOrigin.DOCUMENTED, ClaimOrigin.SIMULATED,
                                     ClaimOrigin.UNSUPPORTED)
