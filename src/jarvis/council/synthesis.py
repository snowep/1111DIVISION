"""Synthesis — JARVIS compares evidence, claims, disagreements, and confidence.

The majority vote must never override stronger evidence.
Synthesis is where JARVIS (without persona overlay) determines the
actual recommendation by weighing evidence quality against vote counts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .agreement import AgreementRecord, AgreementType, PositionVote, majority_vote
from .evidence import Evidence, EvidenceRegistry


# ---------------------------------------------------------------------------
# Evidence strength assessment
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvidenceStrength:
    """Quantified assessment of evidence supporting a position."""

    position: str  # approve / reject / approve-with-conditions
    supporting_evidence: tuple[Evidence, ...] = ()
    average_confidence: float = 0.0
    verified_count: int = 0
    primary_count: int = 0
    total_count: int = 0
    strongest_claim: str = ""
    weakest_claim: str = ""

    @property
    def verified_ratio(self) -> float:
        return (
            self.verified_count / self.total_count
            if self.total_count > 0
            else 0.0
        )

    @property
    def primary_ratio(self) -> float:
        return (
            self.primary_count / self.total_count
            if self.total_count > 0
            else 0.0
        )


def assess_evidence_strength(
    votes: list[PositionVote],
    registry: EvidenceRegistry,
) -> dict[str, EvidenceStrength]:
    """Assess evidence strength for each recommendation position.

    Groups votes by recommendation and evaluates the evidence they cite.
    """
    by_rec: dict[str, list[PositionVote]] = {}
    for v in votes:
        by_rec.setdefault(v.recommendation, []).append(v)

    strengths: dict[str, EvidenceStrength] = {}

    for rec, rec_votes in by_rec.items():
        all_evidence: list[Evidence] = []
        for v in rec_votes:
            for eid in v.evidence_refs:
                ev = registry.get(eid)
                if ev is not None:
                    all_evidence.append(ev)

        if not all_evidence:
            strengths[rec] = EvidenceStrength(position=rec)
            continue

        confidences = [e.confidence for e in all_evidence]
        avg_conf = sum(confidences) / len(confidences)
        verified = sum(1 for e in all_evidence if e.verified)
        primary = sum(
            1 for e in all_evidence
            if e.source_type.value == "primary"
        )

        # Find strongest and weakest claims
        sorted_by_conf = sorted(all_evidence, key=lambda e: e.confidence)
        weakest = sorted_by_conf[0].claim_text if sorted_by_conf else ""
        strongest = sorted_by_conf[-1].claim_text if sorted_by_conf else ""

        strengths[rec] = EvidenceStrength(
            position=rec,
            supporting_evidence=tuple(all_evidence),
            average_confidence=avg_conf,
            verified_count=verified,
            primary_count=primary,
            total_count=len(all_evidence),
            strongest_claim=strongest,
            weakest_claim=weakest,
        )

    return strengths


# ---------------------------------------------------------------------------
# Disagreement analysis
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DisagreementAnalysis:
    """Structured analysis of disagreements."""

    material_conflicts: int = 0
    total_disagreements: int = 0
    unresolved: tuple[str, ...] = ()
    resolution_possible: bool = False
    evidence_favors: Optional[str] = None  # which position evidence supports
    evidence_confidence_gap: float = 0.0


def analyze_disagreements(
    agreements: list[AgreementRecord],
    evidence_strengths: dict[str, EvidenceStrength],
) -> DisagreementAnalysis:
    """Analyze disagreements and determine if evidence resolves them."""
    disagreements = [
        a for a in agreements
        if a.agreement_type == AgreementType.DISAGREE
    ]

    unresolved: list[str] = []
    evidence_favors = None
    confidence_gap = 0.0

    if disagreements:
        # Compare evidence strength across disagreeing positions
        positions = set()
        for d in disagreements:
            positions.update(d.participants)

        # Find the recommendation with strongest evidence
        best_rec = None
        best_score = -1.0
        for rec, strength in evidence_strengths.items():
            score = (
                strength.average_confidence * 0.4
                + strength.verified_ratio * 0.3
                + strength.primary_ratio * 0.3
            )
            if score > best_score:
                best_score = score
                best_rec = rec

        if best_rec and len(evidence_strengths) > 1:
            scores = {}
            for rec, strength in evidence_strengths.items():
                scores[rec] = (
                    strength.average_confidence * 0.4
                    + strength.verified_ratio * 0.3
                    + strength.primary_ratio * 0.3
                )
            sorted_scores = sorted(scores.items(), key=lambda x: x[1])
            if len(sorted_scores) >= 2:
                gap = sorted_scores[-1][1] - sorted_scores[0][1]
                if gap > 0.15:
                    evidence_favors = sorted_scores[-1][0]
                    confidence_gap = gap

        for d in disagreements:
            if not evidence_favors:
                unresolved.append(d.conclusion)

    return DisagreementAnalysis(
        material_conflicts=len(disagreements),
        total_disagreements=len(disagreements),
        unresolved=tuple(unresolved),
        resolution_possible=evidence_favors is not None,
        evidence_favors=evidence_favors,
        evidence_confidence_gap=confidence_gap,
    )


# ---------------------------------------------------------------------------
# Confidence propagation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConfidenceAssessment:
    """Final confidence assessment for the council recommendation."""

    overall_confidence: float = 0.0
    label: str = "UNKNOWN"
    evidence_quality_score: float = 0.0
    convergence_score: float = 0.0
    argument_strength_score: float = 0.0
    counterargument_weakness_score: float = 0.0

    def __post_init__(self) -> None:
        # Auto-compute label from confidence
        if self.overall_confidence >= 0.85:
            object.__setattr__(self, "label", "VERY HIGH")
        elif self.overall_confidence >= 0.70:
            object.__setattr__(self, "label", "HIGH")
        elif self.overall_confidence >= 0.50:
            object.__setattr__(self, "label", "MEDIUM")
        elif self.overall_confidence >= 0.30:
            object.__setattr__(self, "label", "LOW")
        else:
            object.__setattr__(self, "label", "VERY LOW")


def compute_confidence(
    votes: list[PositionVote],
    evidence_strengths: dict[str, EvidenceStrength],
    disagreements: DisagreementAnalysis,
) -> ConfidenceAssessment:
    """Compute council confidence using the weighted model from meeting-protocol.

    Weights (default strategic-direction):
      evidence_quality: 0.25
      persona_convergence: 0.35
      argument_strength: 0.20
      counterargument_weakness: 0.20
    """
    # Evidence quality: mean confidence of cited evidence
    all_confidences = []
    for strength in evidence_strengths.values():
        for ev in strength.supporting_evidence:
            all_confidences.append(ev.confidence)
    eq_score = (
        sum(all_confidences) / len(all_confidences) if all_confidences else 0.5
    )

    # Persona convergence: how much do they agree?
    if len(votes) == 0:
        pc_score = 0.0
    else:
        recs = set(v.recommendation for v in votes)
        # Fewer distinct recommendations = higher convergence
        pc_score = 1.0 - ((len(recs) - 1) / max(len(votes) - 1, 1))
        # Adjust for material disagreements
        if disagreements.material_conflicts > 0:
            pc_score = max(0.0, pc_score - 0.1 * disagreements.material_conflicts)

    # Argument strength: ratio of evidence-backed claims
    total_refs = sum(len(v.evidence_refs) for v in votes)
    total_votes = len(votes) if votes else 1
    arg_score = min(1.0, total_refs / (total_votes * 2)) if total_votes else 0.0

    # Counterargument weakness: how strong are the counter-arguments?
    # Higher when counterarguments are weak (evidence favors one side)
    if disagreements.evidence_favors and disagreements.evidence_confidence_gap > 0:
        cav_score = min(1.0, 0.5 + disagreements.evidence_confidence_gap)
    elif disagreements.material_conflicts == 0:
        cav_score = 0.8  # no disagreements = no strong counterarguments
    else:
        cav_score = 0.4  # unresolved disagreements

    # Weighted average
    overall = (
        eq_score * 0.25
        + pc_score * 0.35
        + arg_score * 0.20
        + cav_score * 0.20
    )

    return ConfidenceAssessment(
        overall_confidence=round(overall, 3),
        evidence_quality_score=round(eq_score, 3),
        convergence_score=round(pc_score, 3),
        argument_strength_score=round(arg_score, 3),
        counterargument_weakness_score=round(cav_score, 3),
    )


# ---------------------------------------------------------------------------
# Full synthesis
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SynthesisResult:
    """The complete output of JARVIS synthesis."""

    question: str
    recommendation: str  # the final recommendation
    majority_vote: Optional[str]
    evidence_overrides_majority: bool
    evidence_strengths: dict[str, EvidenceStrength] = field(default_factory=dict)
    disagreements: DisagreementAnalysis = field(default_factory=DisagreementAnalysis)
    confidence: ConfidenceAssessment = field(default_factory=ConfidenceAssessment)
    majority_reasoning: str = ""
    override_reasoning: str = ""
    unresolved_questions: tuple[str, ...] = ()
    reversal_conditions: tuple[str, ...] = ()


def synthesize(
    question: str,
    votes: list[PositionVote],
    registry: EvidenceRegistry,
    agreements: list[AgreementRecord],
) -> SynthesisResult:
    """Perform the full JARVIS synthesis.

    This is the critical function: it determines whether the majority
    vote or the evidence wins.

    Rules:
    1. Compute evidence strength per position
    2. Compute majority vote
    3. If evidence strongly favors a non-majority position → override
    4. If evidence is weak or ambiguous → majority wins
    5. Never let vote count override stronger evidence
    """
    # Step 1: Evidence strength
    evidence_strengths = assess_evidence_strength(votes, registry)

    # Step 2: Majority vote
    maj_vote = majority_vote(votes)

    # Step 3: Disagreement analysis
    disagreements = analyze_disagreements(agreements, evidence_strengths)

    # Step 4: Confidence
    confidence = compute_confidence(votes, evidence_strengths, disagreements)

    # Step 5: Determine if evidence overrides majority
    evidence_overrides = False
    override_reasoning = ""

    if maj_vote and disagreements.evidence_favors:
        if disagreements.evidence_favors != maj_vote:
            # Evidence favors a different position than the majority
            if disagreements.evidence_confidence_gap > 0.15:
                evidence_overrides = True
                override_reasoning = (
                    f"Evidence strongly favors '{disagreements.evidence_favors}' "
                    f"(confidence gap: {disagreements.evidence_confidence_gap:.2f}) "
                    f"over majority vote '{maj_vote}'. "
                    f"The majority can be wrong when evidence is stronger."
                )

    # Step 6: Final recommendation
    if evidence_overrides:
        final_rec = disagreements.evidence_favors or maj_vote or "uncertain"
    else:
        final_rec = maj_vote or "uncertain"

    # Collect unresolved questions
    unresolved: list[str] = list(disagreements.unresolved)

    # Collect reversal conditions from all votes
    reversal: list[str] = []
    for v in votes:
        reversal.extend(v.conditions)

    return SynthesisResult(
        question=question,
        recommendation=final_rec,
        majority_vote=maj_vote,
        evidence_overrides_majority=evidence_overrides,
        evidence_strengths=evidence_strengths,
        disagreements=disagreements,
        confidence=confidence,
        majority_reasoning=(
            f"Majority vote: {maj_vote}"
            if maj_vote
            else "No majority — tied or insufficient votes"
        ),
        override_reasoning=override_reasoning,
        unresolved_questions=tuple(unresolved),
        reversal_conditions=tuple(reversal),
    )
