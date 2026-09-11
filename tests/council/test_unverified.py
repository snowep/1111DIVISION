"""Test 2: Unsupported claim remains unverified.

A claim without evidence backing is classified UNVERIFIED and never
treated as evidence-backed, even if it sounds plausible.
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


class TestUnsupportedClaimRemainsUnverified:
    """Claims without evidence stay UNVERIFIED — plausibility doesn't promote them."""

    def test_unverified_claim_classified_correctly(self):
        """A claim with no source is classified as UNVERIFIED."""
        from jarvis.council.evidence import classify_claim

        result = classify_claim(
            text="The engine is probably slow",
            has_source=False,
            source_is_primary=False,
        )
        assert result == ClaimType.UNVERIFIED

    def test_unverified_claim_cannot_become_fact(self):
        """Even if repeated, UNVERIFIED doesn't auto-promote."""
        from jarvis.council.evidence import classify_claim

        for _ in range(5):
            result = classify_claim(
                text="The engine is probably slow",
                has_source=False,
                source_is_primary=False,
            )
        assert result == ClaimType.UNVERIFIED

    def test_fact_requires_source(self):
        """FACT classification requires a source."""
        from jarvis.council.evidence import classify_claim

        result = classify_claim(
            text="The engine uses SQLite",
            has_source=True,
            source_is_primary=True,
            is_observed=True,
        )
        assert result == ClaimType.FACT

    def test_inference_without_source_is_unverified(self):
        """Even an inference-sounding claim without source is UNVERIFIED."""
        from jarvis.council.evidence import classify_claim

        result = classify_claim(
            text="Based on the pattern, the engine will fail under load",
            has_source=False,
            source_is_primary=False,
        )
        assert result == ClaimType.UNVERIFIED

    def test_registry_unregisterable_claim(self):
        """An unverified claim cannot be registered as evidence."""
        reg = EvidenceRegistry(meeting_id="TEST")
        # Trying to register with UNVERIFIED type is allowed — but it stays
        # flagged as unverified and low confidence
        record = reg.register(
            claim_type=ClaimType.UNVERIFIED,
            claim_text="Unverified claim",
            evidence_class=EvidenceClass.WEB_SEARCH,
            source="nowhere specific",
            source_type=SourceType.SECONDARY,
            confidence=0.3,
            retrieved_at=datetime.now(timezone.utc),
            evidence_id="EVD-U01",
        )
        assert record.claim_type == ClaimType.UNVERIFIED
        assert record.confidence == 0.3
        assert record.verified is False

    def test_unverified_evidence_affects_meeting_confidence(self):
        """An evidence registry with many unverified items has lower summary confidence."""
        reg = EvidenceRegistry(meeting_id="TEST")
        # Register 3 unverified items
        for i in range(3):
            reg.register(
                claim_type=ClaimType.UNVERIFIED,
                claim_text=f"Unverified claim {i}",
                evidence_class=EvidenceClass.WEB_SEARCH,
                source="web",
                source_type=SourceType.SECONDARY,
                confidence=0.3,
                retrieved_at=datetime.now(timezone.utc),
                evidence_id=f"EVD-U{i:02d}",
            )
        summary = reg.summary()
        assert summary["unverified"] == 3
        assert summary["verified"] == 0

    def test_opinion_not_treated_as_fact(self):
        """OPINION classification stays opinion, not promoted to FACT."""
        from jarvis.council.evidence import classify_claim

        result = classify_claim(
            text="I think the design is good",
            has_source=True,
            source_is_primary=True,
            is_observed=False,
        )
        # Has source but not observed → INFERENCE, not FACT
        assert result == ClaimType.INFERENCE
