"""Council report — structured persistence of council results.

A council report contains:
  - Question
  - Participants
  - Independent positions (with claim classifications)
  - Evidence register
  - Claim classifications
  - Disagreements
  - Convergence/divergence
  - Final recommendation
  - Confidence
  - Unresolved issues
  - "What would change my mind?"

The report is the single artifact that captures what the council
actually determined.  It is a snapshot, not a mutable document.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .agreement import AgreementRecord, AgreementType, PositionVote
from .evidence import Evidence, EvidenceRegistry
from .grounding import GroundingResult
from .isolation import IsolationCheck
from .synthesis import ConfidenceAssessment, DisagreementAnalysis, SynthesisResult


@dataclass(frozen=True)
class ParticipantRecord:
    """A single participant's full record in the council."""

    persona_id: str
    persona_name: str
    recommendation: str
    confidence: float
    evidence_refs: tuple[str, ...] = ()
    claim_refs: tuple[str, ...] = ()
    reasoning_summary: str = ""
    reversal_conditions: tuple[str, ...] = ()
    grounding: Optional[GroundingResult] = None
    isolation_check: Optional[IsolationCheck] = None

    @property
    def has_grounding_violations(self) -> bool:
        return self.grounding.has_violations if self.grounding else False

    @property
    def isolation_passed(self) -> bool:
        return self.isolation_check.passed if self.isolation_check else True


@dataclass(frozen=True)
class CouncilReport:
    """The complete, structured council result.

    Immutable once created.  This is the single artifact that captures
    what the council determined.
    """

    question: str
    meeting_id: str
    participants: tuple[ParticipantRecord, ...]
    evidence: EvidenceRegistry
    agreements: tuple[AgreementRecord, ...]
    synthesis: SynthesisResult
    generated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Summary fields (derived from synthesis)
    @property
    def recommendation(self) -> str:
        return self.synthesis.recommendation

    @property
    def confidence(self) -> ConfidenceAssessment:
        return self.synthesis.confidence

    @property
    def majority_vote(self) -> Optional[str]:
        return self.synthesis.majority_vote

    @property
    def evidence_overrides_majority(self) -> bool:
        return self.synthesis.evidence_overrides_majority

    @property
    def unresolved_questions(self) -> tuple[str, ...]:
        return self.synthesis.unresolved_questions

    @property
    def reversal_conditions(self) -> tuple[str, ...]:
        return self.synthesis.reversal_conditions

    @property
    def disagreements(self) -> DisagreementAnalysis:
        return self.synthesis.disagreements

    @property
    def participant_count(self) -> int:
        return len(self.participants)

    @property
    def all_isolation_passed(self) -> bool:
        return all(p.isolation_passed for p in self.participants)

    @property
    def has_grounding_violations(self) -> bool:
        return any(p.has_grounding_violations for p in self.participants)

    # Agreement summary
    @property
    def agreement_summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for a in self.agreements:
            counts[a.agreement_type.value] = counts.get(a.agreement_type.value, 0) + 1
        return counts

    # Vote breakdown
    @property
    def vote_breakdown(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for p in self.participants:
            counts[p.recommendation] = counts.get(p.recommendation, 0) + 1
        return counts

    def to_dict(self) -> dict:
        """Serialize the report to a dictionary for persistence."""
        return {
            "question": self.question,
            "meeting_id": self.meeting_id,
            "generated_at": self.generated_at.isoformat(),
            "recommendation": self.recommendation,
            "confidence": {
                "overall": self.confidence.overall_confidence,
                "label": self.confidence.label,
                "evidence_quality": self.confidence.evidence_quality_score,
                "convergence": self.confidence.convergence_score,
                "argument_strength": self.confidence.argument_strength_score,
                "counterargument_weakness": self.confidence.counterargument_weakness_score,
            },
            "majority_vote": self.majority_vote,
            "evidence_overrides_majority": self.evidence_overrides_majority,
            "override_reasoning": self.synthesis.override_reasoning,
            "participants": [
                {
                    "persona_id": p.persona_id,
                    "persona_name": p.persona_name,
                    "recommendation": p.recommendation,
                    "confidence": p.confidence,
                    "evidence_refs": list(p.evidence_refs),
                    "reasoning_summary": p.reasoning_summary,
                    "reversal_conditions": list(p.reversal_conditions),
                    "isolation_passed": p.isolation_passed,
                    "has_grounding_violations": p.has_grounding_violations,
                }
                for p in self.participants
            ],
            "evidence_summary": self.evidence.summary(),
            "agreements": [
                {
                    "type": a.agreement_type.value,
                    "participants": list(a.participants),
                    "conclusion": a.conclusion,
                    "notes": a.notes,
                }
                for a in self.agreements
            ],
            "vote_breakdown": self.vote_breakdown,
            "unresolved_questions": list(self.unresolved_questions),
            "reversal_conditions": list(self.reversal_conditions),
            "all_isolation_passed": self.all_isolation_passed,
            "has_grounding_violations": self.has_grounding_violations,
        }

    def to_markdown(self) -> str:
        """Serialize the report to Markdown for human readability."""
        lines = [
            f"# Council Report — {self.meeting_id}",
            "",
            f"**Question:** {self.question}",
            f"**Generated:** {self.generated_at.isoformat()}",
            "",
            "---",
            "",
            "## Recommendation",
            "",
            f"**{self.recommendation.upper()}**",
            "",
            f"Confidence: {self.confidence.overall_confidence} ({self.confidence.label})",
            "",
        ]

        if self.evidence_overrides_majority:
            lines.extend([
                "⚠️ **Evidence overrides majority vote.**",
                "",
                self.synthesis.override_reasoning,
                "",
            ])

        lines.extend([
            "## Participants",
            "",
            "| Persona | Vote | Confidence | Isolation | Grounding |",
            "|---------|------|------------|-----------|-----------|",
        ])
        for p in self.participants:
            iso = "✓" if p.isolation_passed else "✗ BREACH"
            gnd = "✓" if not p.has_grounding_violations else "✗ VIOLATION"
            lines.append(
                f"| {p.persona_name} | {p.recommendation} | "
                f"{p.confidence} | {iso} | {gnd} |"
            )

        lines.extend(["", "## Vote Breakdown", ""])
        for rec, count in self.vote_breakdown.items():
            lines.append(f"- **{rec}**: {count}")

        lines.extend(["", "## Agreements", ""])
        for a in self.agreements:
            lines.append(
                f"- **{a.agreement_type.value}** among "
                f"{', '.join(a.participants)}: {a.conclusion}"
            )

        if self.unresolved_questions:
            lines.extend(["", "## Unresolved Questions", ""])
            for q in self.unresolved_questions:
                lines.append(f"- {q}")

        if self.reversal_conditions:
            lines.extend(["", "## What Would Change My Mind", ""])
            for rc in self.reversal_conditions:
                lines.append(f"- {rc}")

        lines.extend([
            "",
            "---",
            "",
            f"**Isolation:** {'All passed' if self.all_isolation_passed else 'BREACH DETECTED'}",
            f"**Grounding violations:** {'None' if not self.has_grounding_violations else 'DETECTED'}",
            f"**Evidence overrides majority:** {'Yes' if self.evidence_overrides_majority else 'No'}",
        ])

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def build_report(
    question: str,
    meeting_id: str,
    votes: list[PositionVote],
    registry: EvidenceRegistry,
    agreements: list[AgreementRecord],
    synthesis: SynthesisResult,
    grounding_results: Optional[dict[str, GroundingResult]] = None,
    isolation_checks: Optional[dict[str, IsolationCheck]] = None,
) -> CouncilReport:
    """Build a CouncilReport from all meeting artifacts.

    This is the final step of the council pipeline.
    """
    participants = []
    for v in votes:
        gr = grounding_results.get(v.persona_id) if grounding_results else None
        ic = isolation_checks.get(v.persona_id) if isolation_checks else None
        participants.append(
            ParticipantRecord(
                persona_id=v.persona_id,
                persona_name=v.persona_name,
                recommendation=v.recommendation,
                confidence=v.confidence,
                evidence_refs=v.evidence_refs,
                claim_refs=v.claim_refs,
                reasoning_summary=v.reasoning_summary,
                reversal_conditions=v.conditions,
                grounding=gr,
                isolation_check=ic,
            )
        )

    return CouncilReport(
        question=question,
        meeting_id=meeting_id,
        participants=tuple(participants),
        evidence=registry,
        agreements=tuple(agreements),
        synthesis=synthesis,
    )
