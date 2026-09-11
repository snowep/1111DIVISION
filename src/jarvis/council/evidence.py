"""Evidence register and claim types.

Every research-backed council claim must trace to an evidence record.
Claims without evidence are classified but never treated as evidence-backed.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


# ---------------------------------------------------------------------------
# Claim types — exactly the six specified
# ---------------------------------------------------------------------------

class ClaimType(str, enum.Enum):
    FACT = "fact"
    INFERENCE = "inference"
    HYPOTHESIS = "hypothesis"
    OPINION = "opinion"
    ANALOGY = "analogy"
    UNVERIFIED = "unverified"


# ---------------------------------------------------------------------------
# Evidence classes — aligned with meeting-protocol.md Step 4
# ---------------------------------------------------------------------------

class EvidenceClass(str, enum.Enum):
    USER_TESTIMONY = "user-testimony"
    DIRECT_OBSERVATION = "direct-observation"
    PROJECT_ARTIFACT = "project-artifact"
    RESEARCH_SYNTHESIS = "research-synthesis"
    EXTERNAL_ARTICLE = "external-article"
    WEB_SEARCH = "web-search"
    HISTORICAL = "historical"
    INFERENCE = "inference"
    COUNCIL_VM = "council-vm"


# Default confidence per evidence class (meeting-protocol.md Step 4)
DEFAULT_CONFIDENCE: dict[EvidenceClass, float] = {
    EvidenceClass.USER_TESTIMONY: 0.90,
    EvidenceClass.DIRECT_OBSERVATION: 0.95,
    EvidenceClass.PROJECT_ARTIFACT: 0.95,
    EvidenceClass.RESEARCH_SYNTHESIS: 0.75,
    EvidenceClass.EXTERNAL_ARTICLE: 0.75,
    EvidenceClass.WEB_SEARCH: 0.60,
    EvidenceClass.HISTORICAL: 0.75,
    EvidenceClass.INFERENCE: 0.65,
    EvidenceClass.COUNCIL_VM: 0.70,
}


# ---------------------------------------------------------------------------
# Source type — where evidence was obtained
# ---------------------------------------------------------------------------

class SourceType(str, enum.Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"


# ---------------------------------------------------------------------------
# Evidence record
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Evidence:
    """A single piece of evidence in the registry.

    Immutable once created.  Evidence is the atomic unit of the council's
    epistemic layer — every claim must trace here.
    """

    evidence_id: str
    claim_type: ClaimType
    claim_text: str
    evidence_class: EvidenceClass
    source: str
    source_type: SourceType
    confidence: float  # 0.0–1.0
    retrieved_at: datetime
    url: Optional[str] = None
    supporting_evidence: tuple[str, ...] = ()  # evidence_ids this builds on
    phase: int = 1  # 1 = pre-meeting (JARVIS), 2 = in-meeting (persona)
    registered_by: Optional[str] = None  # persona_id for Phase 2
    verified: bool = False
    verification_notes: Optional[str] = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be 0.0–1.0, got {self.confidence}"
            )
        # Inference MUST have supporting evidence
        if self.claim_type == ClaimType.INFERENCE and not self.supporting_evidence:
            raise ValueError(
                f"Evidence {self.evidence_id}: INFERENCE type requires "
                "supporting_evidence (based_on evidence IDs)"
            )

    @property
    def is_verified(self) -> bool:
        return self.verified

    @property
    def is_phase1(self) -> bool:
        return self.phase == 1

    @property
    def is_phase2(self) -> bool:
        return self.phase == 2


# ---------------------------------------------------------------------------
# Evidence Registry — the authoritative register for a meeting
# ---------------------------------------------------------------------------

class EvidenceRegistry:
    """Append-only evidence registry for a council meeting.

    Enforces:
    - unique evidence IDs
    - INFERENCE must cite based_on
    - Phase 2 evidence is only council-vm or inference
    - minimum evidence count gate
    """

    def __init__(self, meeting_id: str) -> None:
        self.meeting_id = meeting_id
        self._evidence: dict[str, Evidence] = {}
        self._next_seq = 1

    def _generate_id(self, phase: int = 1) -> str:
        seq = self._next_seq
        self._next_seq += 1
        prefix = "EVD" if phase == 1 else "EVD2"
        return f"{prefix}-{seq:03d}"

    def register(
        self,
        claim_type: ClaimType,
        claim_text: str,
        evidence_class: EvidenceClass,
        source: str,
        source_type: SourceType,
        confidence: Optional[float] = None,
        retrieved_at: Optional[datetime] = None,
        url: Optional[str] = None,
        supporting_evidence: tuple[str, ...] = (),
        phase: int = 1,
        registered_by: Optional[str] = None,
        verified: bool = False,
        evidence_id: Optional[str] = None,
    ) -> Evidence:
        """Register a new piece of evidence.

        Returns the created Evidence record.
        Raises ValueError on validation failure.
        """
        # Phase 2 evidence must be council-vm or inference
        if phase == 2 and evidence_class not in (
            EvidenceClass.COUNCIL_VM,
            EvidenceClass.INFERENCE,
        ):
            raise ValueError(
                f"Phase 2 evidence can only be council-vm or inference, "
                f"got {evidence_class.value}"
            )

        # Verify supporting evidence exists
        for ref_id in supporting_evidence:
            if ref_id not in self._evidence:
                raise ValueError(
                    f"Supporting evidence {ref_id} not found in registry"
                )

        eid = evidence_id or self._generate_id(phase)
        if eid in self._evidence:
            raise ValueError(f"Evidence ID {eid} already exists")

        if confidence is None:
            confidence = DEFAULT_CONFIDENCE.get(evidence_class, 0.5)

        if retrieved_at is None:
            retrieved_at = datetime.now(timezone.utc)

        record = Evidence(
            evidence_id=eid,
            claim_type=claim_type,
            claim_text=claim_text,
            evidence_class=evidence_class,
            source=source,
            source_type=source_type,
            confidence=confidence,
            retrieved_at=retrieved_at,
            url=url,
            supporting_evidence=supporting_evidence,
            phase=phase,
            registered_by=registered_by,
            verified=verified,
        )

        self._evidence[eid] = record
        return record

    def get(self, evidence_id: str) -> Optional[Evidence]:
        return self._evidence.get(evidence_id)

    def get_all(self) -> list[Evidence]:
        return list(self._evidence.values())

    def phase1_evidence(self) -> list[Evidence]:
        return [e for e in self._evidence.values() if e.is_phase1]

    def phase2_evidence(self) -> list[Evidence]:
        return [e for e in self._evidence.values() if e.is_phase2]

    def by_persona(self, persona_id: str) -> list[Evidence]:
        """Phase 2 evidence registered by a specific persona."""
        return [
            e for e in self._evidence.values()
            if e.registered_by == persona_id
        ]

    def has_sufficient_phase1(self, minimum: int = 3) -> bool:
        """Check if Phase 1 evidence meets the minimum threshold."""
        return len(self.phase1_evidence()) >= minimum

    def unverified_count(self) -> int:
        return sum(1 for e in self._evidence.values() if not e.verified)

    def verify(self, evidence_id: str, notes: str = "") -> Evidence:
        """Mark evidence as verified. Returns updated record."""
        old = self._evidence.get(evidence_id)
        if old is None:
            raise KeyError(f"Evidence {evidence_id} not found")
        updated = Evidence(
            evidence_id=old.evidence_id,
            claim_type=old.claim_type,
            claim_text=old.claim_text,
            evidence_class=old.evidence_class,
            source=old.source,
            source_type=old.source_type,
            confidence=old.confidence,
            retrieved_at=old.retrieved_at,
            url=old.url,
            supporting_evidence=old.supporting_evidence,
            phase=old.phase,
            registered_by=old.registered_by,
            verified=True,
            verification_notes=notes or None,
        )
        self._evidence[evidence_id] = updated
        return updated

    def summary(self) -> dict:
        all_ev = self.get_all()
        return {
            "meeting_id": self.meeting_id,
            "total": len(all_ev),
            "phase1": len(self.phase1_evidence()),
            "phase2": len(self.phase2_evidence()),
            "verified": sum(1 for e in all_ev if e.verified),
            "unverified": self.unverified_count(),
            "by_claim_type": {
                ct.value: sum(1 for e in all_ev if e.claim_type == ct)
                for ct in ClaimType
            },
        }

    @property
    def count(self) -> int:
        return len(self._evidence)


# ---------------------------------------------------------------------------
# Claim classification helpers
# ---------------------------------------------------------------------------

def classify_claim(
    text: str,
    has_source: bool,
    source_is_primary: bool,
    is_observed: bool = False,
) -> ClaimType:
    """Classify a claim based on its nature and evidence basis.

    Heuristic classification — the caller should review.

    FACT requires both a primary source AND direct observation.
    A primary source without observation is INFERENCE (you trust the
    source but haven't independently verified).
    """
    if not has_source:
        return ClaimType.UNVERIFIED
    if is_observed and source_is_primary:
        return ClaimType.FACT
    # Primary source but not observed → inference (trusted but unverified)
    if source_is_primary:
        return ClaimType.INFERENCE
    if is_observed:
        return ClaimType.INFERENCE
    return ClaimType.INFERENCE


def require_evidence_backing(
    claim_text: str,
    evidence_refs: tuple[str, ...],
    registry: EvidenceRegistry,
) -> None:
    """Validate that a claim has evidence backing.

    Raises ValueError if:
    - No evidence references provided
    - Any referenced evidence ID doesn't exist in the registry
    """
    if not evidence_refs:
        raise ValueError(
            f"Claim '{claim_text[:60]}...' has no evidence references. "
            "Every council claim must cite evidence."
        )
    for ref in evidence_refs:
        if registry.get(ref) is None:
            raise ValueError(
                f"Claim '{claim_text[:60]}...' references "
                f"non-existent evidence {ref}"
            )
