"""Memory Filter: weighting and temporal decay heuristics.

Implements the JARVIS Master Prompt Section 10 (MEMORY FILTER) logic.
Every memory gets an `importance` scalar (0.0 to 1.0). Low-weight
memories are automatically assigned a short `valid_until` decay boundary.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Heuristic scoring
# ---------------------------------------------------------------------------
_HIGH_VAL_RE = re.compile(
    r"\b(always|never|must|required|decision|decided|prefer|architecture|security|axiom)\b", re.I
)
_LOW_VAL_RE = re.compile(
    r"\b(today|yesterday|tomorrow|maybe|guess|heard|probably|temporary|test|fix|oops)\b", re.I
)


def assess_importance(text: str, kind: str) -> float:
    """Calculate an importance weight [0.0 - 1.0] for a memory candidate."""
    base_weight = 0.5
    
    # 1. Base weight by structural kind
    if kind == "decisions":
        base_weight = 0.9
    elif kind == "procedural":
        base_weight = 0.8
    elif kind == "learned":
        base_weight = 0.8
    elif kind == "semantic":
        base_weight = 0.6
    elif kind == "episodic":
        base_weight = 0.3
        
    # 2. Heuristic keyword modifiers
    if _HIGH_VAL_RE.search(text):
        base_weight += 0.2
    if _LOW_VAL_RE.search(text):
        base_weight -= 0.2
        
    return max(0.0, min(1.0, base_weight))


def calculate_decay(importance: float) -> str | None:
    """Return an ISO-8601 valid_until string for low-importance memories.
    
    0.0 - 0.3 : decays in 24 hours (ephemeral)
    0.3 - 0.5 : decays in 7 days (short-term context)
    > 0.5     : no decay (permanent until superseded)
    """
    now = datetime.now(timezone.utc)
    if importance < 0.3:
        return (now + timedelta(days=1)).isoformat(timespec="seconds")
    if importance < 0.6:
        return (now + timedelta(days=7)).isoformat(timespec="seconds")
    return None
