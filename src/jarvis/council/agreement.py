"""Agreement semantics — replace simple yes/no consensus.

The five agreement types ensure that "the council agreed" means something
specific and testable.  Absence of disagreement is never interpreted as
agreement.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional


class AgreementType(str, enum.Enum):
    """Exactly the five agreement classifications."""

    AGREE = "agree"
    QUALIFIED_AGREEMENT = "qualified_agreement"
    DISAGREE = "disagree"
    UNCERTAIN = "uncertain"
    UNADDRESSED = "unaddressed"


@dataclass(frozen=True)
class PositionVote:
    """A single persona's position on the council question.

    One vote per persona per meeting.
    """

    persona_id: str
    persona_name: str
    recommendation: str  # approve / reject / approve-with-conditions
    confidence: float  # 0.0–1.0
    evidence_refs: tuple[str, ...] = ()
    claim_refs: tuple[str, ...] = ()  # claim_ids from evidence register
    conditions: tuple[str, ...] = ()  # reversal conditions
    reasoning_summary: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be 0.0–1.0, got {self.confidence}"
            )
        valid_recs = {"approve", "reject", "approve-with-conditions"}
        if self.recommendation not in valid_recs:
            raise ValueError(
                f"Invalid recommendation '{self.recommendation}'; "
                f"expected one of {valid_recs}"
            )


@dataclass(frozen=True)
class AgreementRecord:
    """A structured agreement classification between two or more positions.

    Never inferred from absence — always explicitly computed.
    """

    agreement_type: AgreementType
    participants: tuple[str, ...]  # persona_ids
    conclusion: str  # the shared or contested conclusion
    reasoning_map: dict[str, str] = field(default_factory=dict)
    # For qualified_agreement: what each participant actually reasons
    partial_agreed: tuple[str, ...] = ()
    # For qualified_agreement: items agreed upon
    partial_disagreed: tuple[str, ...] = ()
    # For qualified_agreement: items disagreed upon
    evidence_for: tuple[str, ...] = ()
    evidence_against: tuple[str, ...] = ()
    notes: str = ""


# ---------------------------------------------------------------------------
# Agreement classification engine
# ---------------------------------------------------------------------------

def classify_pairwise(
    vote_a: PositionVote,
    vote_b: PositionVote,
) -> AgreementType:
    """Classify the agreement between exactly two positions.

    Returns the AgreementType.  Never returns UNADDRESSED — both positions
    exist, so something was addressed.
    """
    # Same recommendation → potentially agree
    if vote_a.recommendation == vote_b.recommendation:
        # Check if reasoning is substantially the same
        reasoning_overlap = _reasoning_overlap(
            vote_a.reasoning_summary,
            vote_b.reasoning_summary,
        )
        if reasoning_overlap > 0.6:
            return AgreementType.AGREE
        else:
            return AgreementType.QUALIFIED_AGREEMENT

    # Different recommendation → disagree
    if vote_a.recommendation != vote_b.recommendation:
        return AgreementType.DISAGREE

    return AgreementType.UNCERTAIN


def classify_group(
    votes: list[PositionVote],
) -> list[AgreementRecord]:
    """Classify agreement structure across all positions in a meeting.

    Returns a list of AgreementRecord — one per agreement cluster.
    Does NOT infer agreement from silence.
    """
    if not votes:
        return []

    if len(votes) == 1:
        return [
            AgreementRecord(
                agreement_type=AgreementType.UNADDRESSED,
                participants=(votes[0].persona_id,),
                conclusion=votes[0].reasoning_summary or votes[0].recommendation,
                notes="Single position — no agreement/disagreement possible",
            )
        ]

    # Group by recommendation
    by_recommendation: dict[str, list[PositionVote]] = {}
    for v in votes:
        by_recommendation.setdefault(v.recommendation, []).append(v)

    records: list[AgreementRecord] = []

    for rec, group in by_recommendation.items():
        if len(group) == 1:
            # Single voter — not addressed by anyone else
            records.append(
                AgreementRecord(
                    agreement_type=AgreementType.UNADDRESSED,
                    participants=(group[0].persona_id,),
                    conclusion=group[0].reasoning_summary or rec,
                    notes=f"Only {group[0].persona_name} voted {rec}",
                )
            )
        elif len(group) >= 2:
            # Check reasoning quality
            all_reasoning = [v.reasoning_summary for v in group]
            avg_overlap = _average_pairwise_overlap(all_reasoning)

            if avg_overlap > 0.6:
                atype = AgreementType.AGREE
            else:
                atype = AgreementType.QUALIFIED_AGREEMENT

            records.append(
                AgreementRecord(
                    agreement_type=atype,
                    participants=tuple(v.persona_id for v in group),
                    conclusion=group[0].reasoning_summary or rec,
                    reasoning_map={
                        v.persona_id: v.reasoning_summary for v in group
                    },
                )
            )

    # Disagreements
    for rec_a, group_a in by_recommendation.items():
        for rec_b, group_b in by_recommendation.items():
            if rec_a >= rec_b:
                continue  # avoid duplicates
            all_a = [v.persona_id for v in group_a]
            all_b = [v.persona_id for v in group_b]
            records.append(
                AgreementRecord(
                    agreement_type=AgreementType.DISAGREE,
                    participants=tuple(all_a + all_b),
                    conclusion=f"{rec_a} vs {rec_b}",
                    notes=f"Material conflict: {rec_a} vs {rec_b}",
                )
            )

    return records


# ---------------------------------------------------------------------------
# Majority determination — returns raw count but NEVER overrides evidence
# ---------------------------------------------------------------------------

def majority_vote(votes: list[PositionVote]) -> Optional[str]:
    """Return the majority recommendation, or None if tied.

    This is a raw count — synthesis.py decides whether the majority
    overrides evidence.
    """
    if not votes:
        return None

    counts: dict[str, int] = {}
    for v in votes:
        counts[v.recommendation] = counts.get(v.recommendation, 0) + 1

    max_count = max(counts.values())
    winners = [k for k, c in counts.items() if c == max_count]

    if len(winners) == 1:
        return winners[0]
    return None  # tie


# ---------------------------------------------------------------------------
# Text similarity helpers
# ---------------------------------------------------------------------------

def _reasoning_overlap(a: str, b: str) -> float:
    """Simple word-overlap Jaccard similarity for reasoning text.

    Returns 0.0–1.0.  Intentionally simple — the council is not NLP.
    """
    if not a or not b:
        return 0.0
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union) if union else 0.0


def _average_pairwise_overlap(texts: list[str]) -> float:
    """Average Jaccard overlap across all pairs."""
    if len(texts) < 2:
        return 0.0
    total = 0.0
    count = 0
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            total += _reasoning_overlap(texts[i], texts[j])
            count += 1
    return total / count if count else 0.0
