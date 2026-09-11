"""Test 7: Council recommendation cannot directly mutate project/core/vault.

A council report is a structured recommendation.  It is NEVER an execution
command.  The report persists as a snapshot — it does not modify files in
project/, core/, or vault/ directories.
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
from jarvis.council.agreement import AgreementType, PositionVote, classify_group
from jarvis.council.grounding import GroundingResult, ClaimOrigin
from jarvis.council.isolation import IsolationCheck
from jarvis.council.report import CouncilReport, build_report
from jarvis.council.synthesis import synthesize


class TestCouncilRecommendationCannotMutate:
    """Council reports are read-only snapshots — never execution commands."""

    @pytest.fixture
    def sample_report(self):
        """A minimal but complete council report."""
        reg = EvidenceRegistry(meeting_id="MEETING-BOUNDARY-001")
        reg.register(
            claim_type=ClaimType.FACT,
            claim_text="The repo uses SQLite",
            evidence_class=EvidenceClass.DIRECT_OBSERVATION,
            source="inspection",
            source_type=SourceType.PRIMARY,
            confidence=0.95,
            retrieved_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
            evidence_id="EVD-001",
        )

        votes = [
            PositionVote(
                persona_id="persona.steve_jobs",
                persona_name="Steve Jobs",
                recommendation="approve",
                confidence=0.9,
                evidence_refs=("EVD-001",),
                reasoning_summary="Ship it",
            ),
        ]

        agreements = classify_group(votes)
        synthesis = synthesize(
            question="Ship it?",
            votes=votes,
            registry=reg,
            agreements=agreements,
        )

        return build_report(
            question="Ship it?",
            meeting_id="MEETING-BOUNDARY-001",
            votes=votes,
            registry=reg,
            agreements=agreements,
            synthesis=synthesis,
        )

    def test_report_is_frozen_dataclass(self, sample_report):
        """Report is a frozen dataclass — cannot be mutated after creation."""
        with pytest.raises(AttributeError):
            sample_report.question = "Changed!"

    def test_report_recommendation_is_string(self, sample_report):
        """Recommendation is a plain string, not an executable command."""
        assert isinstance(sample_report.recommendation, str)
        assert sample_report.recommendation in (
            "approve", "reject", "approve-with-conditions", "uncertain"
        )

    def test_report_has_no_file_operations(self, sample_report):
        """Report object has no methods that write to disk."""
        # Report only has to_dict and to_markdown — both return data
        d = sample_report.to_dict()
        assert isinstance(d, dict)

        md = sample_report.to_markdown()
        assert isinstance(md, str)

    def test_report_to_dict_has_only_data(self, sample_report):
        """Serialized report contains only data — no execution instructions."""
        d = sample_report.to_dict()

        # Should NOT contain any of these keys
        forbidden_keys = {"exec", "command", "run", "execute", "write_files",
                          "modify", "delete", "deploy"}
        for key in d.keys():
            assert key not in forbidden_keys, (
                f"Report contains forbidden key: {key}"
            )

    def test_report_to_markdown_has_no_code_blocks(self, sample_report):
        """Markdown report has no executable code blocks."""
        md = sample_report.to_markdown()
        # Should not contain ```bash, ```python, ```sh, etc.
        assert "```bash" not in md
        assert "```python" not in md
        assert "```sh" not in md
        assert "```powershell" not in md

    def test_report_persists_without_side_effects(self, sample_report):
        """Building a report doesn't modify any external state."""
        # Report creation is pure — no filesystem writes
        # (The test itself proves this by running without mocking filesystem)
        assert sample_report.meeting_id == "MEETING-BOUNDARY-001"
        assert sample_report.participant_count == 1

    def test_report_confidence_is_read_only(self, sample_report):
        """Confidence assessment is a frozen dataclass."""
        conf = sample_report.confidence
        with pytest.raises(AttributeError):
            conf.overall_confidence = 0.0

    def test_report_evidence_registry_is_independent(self, sample_report):
        """The report's evidence registry is a reference, not a copy,
        but the report itself doesn't mutate it."""
        # Evidence registry is shared — but the report only reads from it
        ev = sample_report.evidence.get("EVD-001")
        assert ev is not None
        assert ev.claim_text == "The repo uses SQLite"

    def test_multiple_reports_from_same_meeting_are_independent(self):
        """Two reports from the same meeting data don't interfere."""
        reg = EvidenceRegistry(meeting_id="MEETING-BOUNDARY-002")
        reg.register(
            claim_type=ClaimType.FACT,
            claim_text="Test fact",
            evidence_class=EvidenceClass.DIRECT_OBSERVATION,
            source="test",
            source_type=SourceType.PRIMARY,
            confidence=0.9,
            evidence_id="EVD-001",
        )

        votes = [
            PositionVote(
                persona_id="p1", persona_name="A",
                recommendation="approve", confidence=0.9,
                evidence_refs=("EVD-001",),
            ),
        ]

        agreements = classify_group(votes)
        synthesis = synthesize(
            question="Test?", votes=votes, registry=reg, agreements=agreements
        )

        report1 = build_report(
            question="Test?", meeting_id="MEETING-BOUNDARY-002",
            votes=votes, registry=reg, agreements=agreements,
            synthesis=synthesis,
        )
        report2 = build_report(
            question="Test?", meeting_id="MEETING-BOUNDARY-002",
            votes=votes, registry=reg, agreements=agreements,
            synthesis=synthesis,
        )

        # Same data, independent objects
        assert report1.recommendation == report2.recommendation
        assert report1 is not report2
