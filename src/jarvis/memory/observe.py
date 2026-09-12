"""P1: Observation-based conversation scanning.

Scans a raw conversation/transcript and routes statements into the vault
using the routing matrix. Statements are parsed heuristically:

  - 'I <prefer|want|need|don't>...'          -> semantic (preference)
  - 'we <decided|agreed|chose>...'           -> decisions
  - 'always/never <do>...'                   -> procedural (rule)
  - 'I think|I believe|I guess|maybe'        -> CANDIDATE (low confidence)
  - 'I heard|someone said|apparently'        -> CANDIDATE (hearsay)
  - 'today/yesterday/last <week>'            -> episodic (temporal)
  - otherwise                                -> semantic

Every extraction is deterministic and attributed (actor + provenance).
This is a **proposal** stage: nothing here VERIFIES truth, it only files
observations so downstream phases (P7 learn / council) can consolidate.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from jarvis.docstore.store import DocumentStore
from jarvis.memory.engine import remember

# ---------------------------------------------------------------------------
# Statement classification
# ---------------------------------------------------------------------------
_PREF_RE = re.compile(
    r"\b(i|we)\s+(prefer|prefers|want|wants|need|needs|don'?t\s+want|do\s+not\s+want)\b",
    re.I,
)
_DEC_RE = re.compile(
    r"\b(we|i|jarvis)\s+(decided|decide|agreed|agree|chose|choose|selected|select)\b",
    re.I,
)
_RULE_RE = re.compile(
    r"\b(always|never)\s+(do|run|use|call|check|verify|write|read|delete|create)\b",
    re.I,
)
_THINK_RE = re.compile(r"\b(i\s+think|i\s+believe|i\s+guess|maybe|probably|possibly)\b", re.I)
_HEARSAY_RE = re.compile(r"\b(i\s+heard|someone\s+said|apparently|reportedly|they\s+say)\b", re.I)
_TEMPORAL_RE = re.compile(r"\b(today|yesterday|tomorrow|last\s+\w+|this\s+(week|month|year))\b", re.I)


def _route_statement(text: str) -> tuple[str, str]:
    """Return (kind, phase) for a raw statement."""
    if _DEC_RE.search(text):
        return "decisions", "OBSERVED"
    if _RULE_RE.search(text):
        return "procedural", "OBSERVED"
    if _PREF_RE.search(text):
        return "semantic", "OBSERVED"
    if _HEARSAY_RE.search(text):
        return "semantic", "CANDIDATE"
    if _THINK_RE.search(text):
        return "semantic", "CANDIDATE"
    if _TEMPORAL_RE.search(text):
        return "episodic", "OBSERVED"
    return "semantic", "OBSERVED"


@dataclass
class Extraction:
    text: str
    kind: str
    phase: str
    confidence: float


def extract_statements(transcript: str) -> list[Extraction]:
    """Split transcript into candidate statements and classify each.

    Heuristic only — intended as the first pass; downstream phases refine.
    """
    out: list[Extraction] = []
    for raw in transcript.splitlines():
        text = raw.strip()
        if not text:
            continue
        kind, phase = _route_statement(text)
        confidence = 0.3 if phase == "CANDIDATE" else 0.5
        out.append(Extraction(text=text, kind=kind, phase=phase, confidence=confidence))
    return out


def observe(
    store: DocumentStore,
    transcript: str,
    *,
    session_id: str | None = None,
    actor: str = "user",
    provenance: dict[str, Any] | None = None,
) -> list[str]:
    """Route a transcript's statements into the vault as OBSERVED notes.

    Returns the created rel paths. Phase stays as classified (OBSERVED or
    CANDIDATE); nothing is promoted without downstream verification.
    """
    created: list[str] = []
    prov: dict[str, Any] = {"type": "user", "session_id": session_id}
    if provenance:
        prov.update(provenance)
    for ex in extract_statements(transcript):
        note = remember(
            store,
            ex.text,
            kind=ex.kind,
            confidence=ex.confidence,
            phase=ex.phase,
            provenance=prov,
            actor=actor,
        )
        created.append(note.document.path)
    return created