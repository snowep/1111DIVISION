"""Test 6: Majority can lose to evidence.

JARVIS must compare evidence, claims, disagreements, agreement quality,
confidence, and unresolved questions.  The majority vote must never
override stronger evidence.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from jarvis.council.evidence import (
    ClaimType,
    EvidenceClass,
    EvidenceRegistry,
    SourceType,
)
from jarvis.council.agreement import (
    AgreementType,
    PositionVote,
    classify_group,
)
from jarvis.council.synthesis import (
    assess_evidence_strength,
    analyze_disagreements,
    compute_confidence,
    synthesize,
)


class TestMajorityCanLoseToEvidence:
    """Evidence quality trumps vote count when the gap is significant."""

    @pytest.fixture
    def majority_loses_registry(self):
        """Registry where evidence strongly favors 'reject'.

        approve votes cite EVD-APPROVE-* (weak),
        reject votes cite EVD-REJECT-* (strong).
        """
        reg = EvidenceRegistry(meeting_id="TEST-MAJ-LOSES")

        # Weak evidence cited by approve side
        reg.register(
            claim_type=ClaimType.OPINION,
            claim_text="Market window is closing",
            evidence_class=EvidenceClass.EXTERNAL_ARTICLE,
            source="blog post",
            source_type=SourceType.SECONDARY,
            confidence=0.45,
            retrieved_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
            evidence_id="EVD-APPROVE-01",
        )

        # Strong evidence cited by reject side
        reg.register(
            claim_type=ClaimType.FACT,
            claim_text="Critical auth vulnerability found in /api/auth",
            evidence_class=EvidenceClass.DIRECT_OBSERVATION,
            source="code review",
            source_type=SourceType.PRIMARY,
            confidence=0.95,
            retrieved_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
            evidence_id="EVD-REJECT-01",
        )
        reg.register(
            claim_type=ClaimType.FACT,
            claim_text="Load testing fails at 500 concurrent users",
            evidence_class=EvidenceClass.DIRECT_OBSERVATION,
            source="load test results",
            source_type=SourceType.PRIMARY,
            confidence=0.95,
            retrieved_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
            evidence_id="EVD-REJECT-02",
        )

        return reg

    def test_evidence_overrides_majority(
        self, five_votes_majority_loses, majority_loses_registry
    ):
        """When evidence strongly favors reject, synthesis overrides 3-2 approve majority."""
        # Patch the votes to cite the correct evidence IDs
        patched_votes = [
            PositionVote(
                persona_id="persona.steve_jobs",
                persona_name="Steve Jobs",
                recommendation="approve",
                confidence=0.9,
                evidence_refs=("EVD-APPROVE-01",),
                reasoning_summary="Ship it",
            ),
            PositionVote(
                persona_id="persona.creative_director",
                persona_name="Creative Director",
                recommendation="approve",
                confidence=0.85,
                evidence_refs=("EVD-APPROVE-01",),
                reasoning_summary="Design is ready",
            ),
            PositionVote(
                persona_id="persona.business_strategist",
                persona_name="Business Strategist",
                recommendation="approve",
                confidence=0.8,
                evidence_refs=("EVD-APPROVE-01",),
                reasoning_summary="Market window closing",
            ),
            PositionVote(
                persona_id="persona.security_architect",
                persona_name="Security Architect",
                recommendation="reject",
                confidence=0.95,
                evidence_refs=("EVD-REJECT-01", "EVD-REJECT-02"),
                reasoning_summary="Critical auth vulnerability must be fixed",
            ),
            PositionVote(
                persona_id="persona.systems_engineer",
                persona_name="Systems Engineer",
                recommendation="reject",
                confidence=0.90,
                evidence_refs=("EVD-REJECT-01", "EVD-REJECT-02"),
                reasoning_summary="Architecture cannot handle load",
            ),
        ]

        agreements = classify_group(patched_votes)

        result = synthesize(
            question="Should we ship the current build?",
            votes=patched_votes,
            registry=majority_loses_registry,
            agreements=agreements,
        )

        # Majority was approve (3 vs 2)
        assert result.majority_vote == "approve"

        # But evidence overrides it
        assert result.evidence_overrides_majority is True
        assert result.recommendation == "reject"

    def test_strong_evidence_wins_over_weak_majority(
        self, five_votes_majority_loses, majority_loses_registry
    ):
        """Evidence strength assessment favors reject."""
        # Patch votes to cite correct evidence IDs
        patched_votes = [
            PositionVote(
                persona_id="persona.steve_jobs",
                persona_name="Steve Jobs",
                recommendation="approve",
                confidence=0.9,
                evidence_refs=("EVD-APPROVE-01",),
            ),
            PositionVote(
                persona_id="persona.creative_director",
                persona_name="Creative Director",
                recommendation="approve",
                confidence=0.85,
                evidence_refs=("EVD-APPROVE-01",),
            ),
            PositionVote(
                persona_id="persona.business_strategist",
                persona_name="Business Strategist",
                recommendation="approve",
                confidence=0.8,
                evidence_refs=("EVD-APPROVE-01",),
            ),
            PositionVote(
                persona_id="persona.security_architect",
                persona_name="Security Architect",
                recommendation="reject",
                confidence=0.95,
                evidence_refs=("EVD-REJECT-01", "EVD-REJECT-02"),
            ),
            PositionVote(
                persona_id="persona.systems_engineer",
                persona_name="Systems Engineer",
                recommendation="reject",
                confidence=0.90,
                evidence_refs=("EVD-REJECT-01", "EVD-REJECT-02"),
            ),
        ]
        strengths = assess_evidence_strength(
            patched_votes, majority_loses_registry
        )

        # Reject side has high-confidence, primary evidence
        assert "reject" in strengths
        reject_strength = strengths["reject"]
        assert reject_strength.average_confidence > 0.8
        assert reject_strength.primary_count >= 1

    def test_weak_evidence_does_not_override_majority(self):
        """When evidence is weak, majority wins normally."""
        reg = EvidenceRegistry(meeting_id="TEST-WEAK-EVID")

        # Weak evidence for reject
        reg.register(
            claim_type=ClaimType.UNVERIFIED,
            claim_text="Maybe there's a vulnerability",
            evidence_class=EvidenceClass.WEB_SEARCH,
            source="random blog",
            source_type=SourceType.SECONDARY,
            confidence=0.30,
            retrieved_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
            evidence_id="EVD-W01",
        )

        # Strong evidence for approve
        reg.register(
            claim_type=ClaimType.FACT,
            claim_text="All tests pass, security scan clean",
            evidence_class=EvidenceClass.DIRECT_OBSERVATION,
            source="CI pipeline",
            source_type=SourceType.PRIMARY,
            confidence=0.95,
            retrieved_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
            evidence_id="EVD-W02",
        )

        votes = [
            PositionVote(
                persona_id="p1", persona_name="A",
                recommendation="approve", confidence=0.9,
                evidence_refs=("EVD-W02",),
            ),
            PositionVote(
                persona_id="p2", persona_name="B",
                recommendation="approve", confidence=0.85,
                evidence_refs=("EVD-W02",),
            ),
            PositionVote(
                persona_id="p3", persona_name="C",
                recommendation="reject", confidence=0.5,
                evidence_refs=("EVD-W01",),
            ),
        ]

        agreements = classify_group(votes)
        result = synthesize(
            question="Ship it?",
            votes=votes,
            registry=reg,
            agreements=agreements,
        )

        # Majority approve wins — weak evidence doesn't override
        assert result.recommendation == "approve"
        assert result.evidence_overrides_majority is False

    def test_tied_evidence_majority_wins(self):
        """When evidence is equally strong on both sides, majority wins."""
        reg = EvidenceRegistry(meeting_id="TEST-TIED-EVID")

        for eid, conf in [("EVD-T01", 0.80), ("EVD-T02", 0.80)]:
            reg.register(
                claim_type=ClaimType.FACT,
                claim_text=f"Fact {eid}",
                evidence_class=EvidenceClass.DIRECT_OBSERVATION,
                source="inspection",
                source_type=SourceType.PRIMARY,
                confidence=conf,
                retrieved_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
                evidence_id=eid,
            )

        votes = [
            PositionVote(
                persona_id="p1", persona_name="A",
                recommendation="approve", confidence=0.85,
                evidence_refs=("EVD-T01",),
            ),
            PositionVote(
                persona_id="p2", persona_name="B",
                recommendation="approve", confidence=0.80,
                evidence_refs=("EVD-T01",),
            ),
            PositionVote(
                persona_id="p3", persona_name="C",
                recommendation="reject", confidence=0.85,
                evidence_refs=("EVD-T02",),
            ),
        ]

        agreements = classify_group(votes)
        result = synthesize(
            question="Ship it?",
            votes=votes,
            registry=reg,
            agreements=agreements,
        )

        # Tied evidence → majority wins
        assert result.recommendation == "approve"
        assert result.evidence_overrides_majority is False

    def test_synthesis_computes_confidence(self, five_votes_majority_loses, majority_loses_registry):
        """Synthesis produces a confidence assessment."""
        agreements = classify_group(five_votes_majority_loses)
        result = synthesize(
            question="Ship it?",
            votes=five_votes_majority_loses,
            registry=majority_loses_registry,
            agreements=agreements,
        )

        assert 0.0 <= result.confidence.overall_confidence <= 1.0
        assert result.confidence.label in (
            "VERY HIGH", "HIGH", "MEDIUM", "LOW", "VERY LOW"
        )

    def test_unresolved_questions_captured(self):
        """Disagreements that evidence cannot resolve become unresolved questions."""
        reg = EvidenceRegistry(meeting_id="TEST-UNRESOLVED")

        # Weak evidence on both sides
        reg.register(
            claim_type=ClaimType.OPINION,
            claim_text="Opinion A",
            evidence_class=EvidenceClass.EXTERNAL_ARTICLE,
            source="blog",
            source_type=SourceType.SECONDARY,
            confidence=0.40,
            retrieved_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
            evidence_id="EVD-U01",
        )
        reg.register(
            claim_type=ClaimType.OPINION,
            claim_text="Opinion B",
            evidence_class=EvidenceClass.EXTERNAL_ARTICLE,
            source="blog",
            source_type=SourceType.SECONDARY,
            confidence=0.40,
            retrieved_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
            evidence_id="EVD-U02",
        )

        votes = [
            PositionVote(
                persona_id="p1", persona_name="A",
                recommendation="approve", confidence=0.5,
                evidence_refs=("EVD-U01",),
            ),
            PositionVote(
                persona_id="p2", persona_name="B",
                recommendation="reject", confidence=0.5,
                evidence_refs=("EVD-U02",),
            ),
        ]

        agreements = classify_group(votes)
        result = synthesize(
            question="Which approach?",
            votes=votes,
            registry=reg,
            agreements=agreements,
        )

        # Evidence is weak on both sides — tied, so recommendation is uncertain
        assert result.recommendation == "uncertain"  # tied, no majority

    def test_reversal_conditions_captured(self):
        """Reversal conditions from votes are collected in synthesis."""
        votes = [
            PositionVote(
                persona_id="p1", persona_name="A",
                recommendation="approve", confidence=0.9,
                conditions=("If error rate exceeds 1%, revert",),
            ),
            PositionVote(
                persona_id="p2", persona_name="B",
                recommendation="approve", confidence=0.85,
                conditions=("If user complaints exceed 20, halt",),
            ),
        ]

        reg = EvidenceRegistry(meeting_id="TEST-REV")
        reg.register(
            claim_type=ClaimType.FACT,
            claim_text="Error rate is 0.1%",
            evidence_class=EvidenceClass.DIRECT_OBSERVATION,
            source="monitoring",
            source_type=SourceType.PRIMARY,
            confidence=0.95,
            retrieved_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
            evidence_id="EVD-R01",
        )

        agreements = classify_group(votes)
        result = synthesize(
            question="Ship it?",
            votes=votes,
            registry=reg,
            agreements=agreements,
        )

        assert len(result.reversal_conditions) >= 1
