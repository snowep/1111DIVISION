"""Test 1: Missing evidence cannot be labelled evidence-backed.

Every council claim must trace to an evidence record.
Claims without evidence are classified but never treated as evidence-backed.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from jarvis.council.evidence import (
    ClaimType,
    EvidenceClass,
    EvidenceRegistry,
    SourceType,
    require_evidence_backing,
)


class TestMissingEvidenceCannotBeLabelledEvidenceBacked:
    """Claims without evidence references fail validation."""

    def test_claim_with_no_evidence_refs_raises(self, populated_registry):
        """A claim citing zero evidence IDs is rejected."""
        with pytest.raises(ValueError, match="no evidence references"):
            require_evidence_backing(
                claim_text="We should definitely rewrite the engine",
                evidence_refs=(),
                registry=populated_registry,
            )

    def test_claim_with_nonexistent_evidence_ref_raises(self, populated_registry):
        """A claim citing a non-existent evidence ID is rejected."""
        with pytest.raises(ValueError, match="non-existent evidence"):
            require_evidence_backing(
                claim_text="The engine is slow",
                evidence_refs=("EVD-999",),
                registry=populated_registry,
            )

    def test_claim_with_valid_evidence_ref_passes(self, populated_registry):
        """A claim citing a real evidence ID passes validation."""
        # Should not raise
        require_evidence_backing(
            claim_text="The repo uses FastAPI",
            evidence_refs=("EVD-001",),
            registry=populated_registry,
        )

    def test_claim_with_multiple_valid_refs_passes(self, populated_registry):
        """A claim citing multiple real evidence IDs passes."""
        require_evidence_backing(
            claim_text="Architecture needs rewrite",
            evidence_refs=("EVD-001", "EVD-003"),
            registry=populated_registry,
        )

    def test_unverified_evidence_still_counts(self, populated_registry):
        """Unverified evidence is still valid evidence — just flagged."""
        reg = EvidenceRegistry(meeting_id="TEST")
        reg.register(
            claim_type=ClaimType.UNVERIFIED,
            claim_text="Some unverified claim",
            evidence_class=EvidenceClass.WEB_SEARCH,
            source="google",
            source_type=SourceType.SECONDARY,
            confidence=0.3,
            retrieved_at=datetime.now(timezone.utc),
            evidence_id="EVD-U01",
            verified=False,
        )
        # Should not raise — unverified is still evidence
        require_evidence_backing(
            claim_text="This might be true",
            evidence_refs=("EVD-U01",),
            registry=reg,
        )

    def test_inference_without_based_on_raises(self):
        """INFERENCE type evidence without supporting_evidence is rejected."""
        reg = EvidenceRegistry(meeting_id="TEST")
        with pytest.raises(ValueError, match="INFERENCE type requires"):
            reg.register(
                claim_type=ClaimType.INFERENCE,
                claim_text="Derived conclusion",
                evidence_class=EvidenceClass.INFERENCE,
                source="reasoning",
                source_type=SourceType.PRIMARY,
                confidence=0.65,
                supporting_evidence=(),  # empty!
            )

    def test_inference_with_valid_based_on_passes(self):
        """INFERENCE type with valid supporting evidence passes."""
        reg = EvidenceRegistry(meeting_id="TEST")
        reg.register(
            claim_type=ClaimType.FACT,
            claim_text="Base fact",
            evidence_class=EvidenceClass.DIRECT_OBSERVATION,
            source="inspection",
            source_type=SourceType.PRIMARY,
            confidence=0.95,
            evidence_id="EVD-B01",
        )
        reg.register(
            claim_type=ClaimType.INFERENCE,
            claim_text="Derived conclusion",
            evidence_class=EvidenceClass.INFERENCE,
            source="reasoning",
            source_type=SourceType.PRIMARY,
            confidence=0.65,
            supporting_evidence=("EVD-B01",),
        )

    def test_empty_registry_rejects_all_claims(self):
        """With zero evidence, every claim is rejected."""
        reg = EvidenceRegistry(meeting_id="EMPTY")
        with pytest.raises(ValueError):
            require_evidence_backing(
                claim_text="Anything",
                evidence_refs=(),
                registry=reg,
            )
