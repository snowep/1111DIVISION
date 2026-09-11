"""Historical persona grounding — distinguishes documented from simulated.

For historical personas:
- Documented/publicly supported viewpoint → labeled as historical claim
- Simulated reasoning → labeled as simulated reasoning

The response remains JARVIS, not the historical person.
Private beliefs, quotes, and undocumented claims are never fabricated.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional


class ClaimOrigin(str, enum.Enum):
    """Whether a claim is grounded in documented history or simulated."""

    DOCUMENTED = "documented"
    # Publicly supported, recorded, verifiable

    SIMULATED = "simulated"
    # Reasoning derived from persona definition, not historical record

    UNSUPPORTED = "unsupported"
    # Neither documented nor logically derived from persona definition


@dataclass(frozen=True)
class GroundedClaim:
    """A claim with explicit origin marking.

    Every claim made by a historical persona must be classified:
    - DOCUMENTED: we can point to a public record
    - SIMULATED: this is what the persona definition implies
    - UNSUPPORTED: cannot be attributed to this persona
    """

    claim_text: str
    origin: ClaimOrigin
    persona_id: str
    persona_name: str
    evidence_id: Optional[str] = None
    source_reference: Optional[str] = None  # URL, book, interview, etc.
    caveat: str = ""  # e.g., "Simulated reasoning based on public persona"

    @property
    def is_documented(self) -> bool:
        return self.origin == ClaimOrigin.DOCUMENTED

    @property
    def is_simulated(self) -> bool:
        return self.origin == ClaimOrigin.SIMULATED

    @property
    def is_unsupported(self) -> bool:
        return self.origin == ClaimOrigin.UNSUPPORTED


@dataclass(frozen=True)
class GroundingResult:
    """Result of grounding a persona's full position."""

    persona_id: str
    persona_name: str
    is_historical: bool
    claims: tuple[GroundedClaim, ...] = ()
    documented_count: int = 0
    simulated_count: int = 0
    unsupported_count: int = 0
    violations: tuple[str, ...] = ()

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0

    @property
    def all_documented(self) -> bool:
        return self.unsupported_count == 0 and self.simulated_count == 0


# ---------------------------------------------------------------------------
# Grounding rules
# ---------------------------------------------------------------------------

# These are patterns that indicate a claim is fabricating private beliefs
FabricationPatterns = [
    "I personally believe",
    "In private",
    "My secret opinion is",
    "Behind closed doors",
    "What I never told anyone",
    "My private diary says",
    "I once confided",
    "Off the record, I",
]


# ---------------------------------------------------------------------------
# Grounding engine
# ---------------------------------------------------------------------------

def ground_claim(
    claim_text: str,
    persona_id: str,
    persona_name: str,
    is_historical: bool,
    documented_views: tuple[str, ...] = (),
    evidence_id: Optional[str] = None,
    source_reference: Optional[str] = None,
) -> GroundedClaim:
    """Classify a single claim's origin.

    Args:
        claim_text: The claim being made
        persona_id: The persona making the claim
        persona_name: Display name
        is_historical: Whether this is a historical persona
        documented_views: Known documented views (text snippets)
        evidence_id: Evidence register reference
        source_reference: URL, book, interview citation

    Returns:
        GroundedClaim with origin classification
    """
    if not is_historical:
        # Specialist personas don't need historical grounding
        return GroundedClaim(
            claim_text=claim_text,
            origin=ClaimOrigin.SIMULATED,
            persona_id=persona_id,
            persona_name=persona_name,
            evidence_id=evidence_id,
            caveat="Specialist persona — reasoning based on role definition",
        )

    # Check for fabrication patterns
    claim_lower = claim_text.lower()
    for pattern in FabricationPatterns:
        if pattern.lower() in claim_lower:
            return GroundedClaim(
                claim_text=claim_text,
                origin=ClaimOrigin.UNSUPPORTED,
                persona_id=persona_id,
                persona_name=persona_name,
                evidence_id=evidence_id,
                caveat=f"Contains fabrication pattern: '{pattern}'",
            )

    # Check if claim matches documented views
    if documented_views:
        for view in documented_views:
            if _text_overlap(claim_text, view) > 0.4:
                return GroundedClaim(
                    claim_text=claim_text,
                    origin=ClaimOrigin.DOCUMENTED,
                    persona_id=persona_id,
                    persona_name=persona_name,
                    evidence_id=evidence_id,
                    source_reference=source_reference,
                )

    # Has evidence → can be documented if evidence is primary
    if evidence_id and source_reference:
        return GroundedClaim(
            claim_text=claim_text,
            origin=ClaimOrigin.DOCUMENTED,
            persona_id=persona_id,
            persona_name=persona_name,
            evidence_id=evidence_id,
            source_reference=source_reference,
        )

    # Otherwise: simulated reasoning
    return GroundedClaim(
        claim_text=claim_text,
        origin=ClaimOrigin.SIMULATED,
        persona_id=persona_id,
        persona_name=persona_name,
        evidence_id=evidence_id,
        caveat="Simulated reasoning based on persona definition",
    )


def ground_position(
    persona_id: str,
    persona_name: str,
    is_historical: bool,
    claims: list[dict],  # [{"text": str, "evidence_id": str|None, "source": str|None}]
    documented_views: tuple[str, ...] = (),
) -> GroundingResult:
    """Ground all claims in a persona's position.

    Returns a GroundingResult with per-claim classification and violation count.
    """
    grounded: list[GroundedClaim] = []
    violations: list[str] = []

    for claim in claims:
        g = ground_claim(
            claim_text=claim.get("text", ""),
            persona_id=persona_id,
            persona_name=persona_name,
            is_historical=is_historical,
            documented_views=documented_views,
            evidence_id=claim.get("evidence_id"),
            source_reference=claim.get("source"),
        )
        grounded.append(g)
        if g.origin == ClaimOrigin.UNSUPPORTED:
            violations.append(
                f"Unsupported claim: '{g.claim_text[:80]}...' — {g.caveat}"
            )

    documented = sum(1 for g in grounded if g.origin == ClaimOrigin.DOCUMENTED)
    simulated = sum(1 for g in grounded if g.origin == ClaimOrigin.SIMULATED)
    unsupported = sum(1 for g in grounded if g.origin == ClaimOrigin.UNSUPPORTED)

    return GroundingResult(
        persona_id=persona_id,
        persona_name=persona_name,
        is_historical=is_historical,
        claims=tuple(grounded),
        documented_count=documented,
        simulated_count=simulated,
        unsupported_count=unsupported,
        violations=tuple(violations),
    )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _text_overlap(a: str, b: str) -> float:
    """Word-level Jaccard similarity."""
    if not a or not b:
        return 0.0
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union) if union else 0.0
