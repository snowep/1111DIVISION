"""Self-Critique Engine: turning failures into permanent lessons.

This module implements JARVIS Master Prompt Section 68 (SELF-CRITIQUE) and
Section 37 (CONTINUOUS IMPROVEMENT). It is called after a task to:

1. Detect if a failure or suboptimal outcome occurred.
2. Extract the assumption that was wrong.
3. Generate a permanent lesson stored in `vault/learned/` (kind: 'learned').
4. Optionally tag the lesson for future retrieval by skill adaptation.

This is **not** an automatic LLM call; it is a deterministic framework the
intelligence layer (JARVIS in Open WebUI) uses to structure its own
self-reflection before writing to the canonical vault.
"""
from __future__ import annotations

from dataclasses import dataclass

from jarvis.docstore.store import DocumentStore
from jarvis.memory import remember


@dataclass
class Critique:
    """The structured output of a self-critique pass."""
    failure_description: str
    wrong_assumption: str
    corrected_understanding: str
    lesson: str  # the permanent knowledge to be stored
    tags: list[str]
    importance: float = 0.8  # lessons are high importance by default


def critique_task(
    store: DocumentStore,
    task_description: str,
    expected_outcome: str,
    actual_outcome: str,
    *,
    session_id: str | None = None,
) -> Critique:
    """Analyze a task outcome and return a structured critique.

    This is a heuristic, rule-based first pass; the intelligence layer
    (JARVIS) will refine this with its own reasoning before storage.
    """
    # 1. Detect if there is a mismatch (failure/suboptimal)
    if expected_outcome.strip().lower() == actual_outcome.strip().lower():
        # No mismatch, no critique needed
        return Critique(
            failure_description="",
            wrong_assumption="",
            corrected_understanding="",
            lesson="",
            tags=[],
            importance=0.0,
        )

    # 2. Heuristic extraction of the wrong assumption
    wrong = _extract_wrong_assumption(task_description, expected_outcome, actual_outcome)
    corrected = _extract_corrected_understanding(task_description, expected_outcome, actual_outcome)
    lesson = f"When {task_description}, assuming {wrong} led to {actual_outcome}. Correct understanding: {corrected}."

    # 3. Tagging for retrieval
    tags = ["lesson", "failure"]
    if "test" in task_description.lower():
        tags.append("testing")
    if "permission" in task_description.lower() or "security" in task_description.lower():
        tags.append("security")
    if "performance" in task_description.lower() or "speed" in task_description.lower():
        tags.append("performance")

    return Critique(
        failure_description=f"Expected: {expected_outcome}. Actual: {actual_outcome}.",
        wrong_assumption=wrong,
        corrected_understanding=corrected,
        lesson=lesson,
        tags=tags,
        importance=0.8,  # Lessons are inherently important
    )


def _extract_wrong_assumption(task: str, expected: str, actual: str) -> str:
    """Heuristic: what assumption likely caused the gap?"""
    # Simple placeholder; the intelligence layer will improve this.
    if "timeout" in actual.lower() or "failed" in actual.lower():
        return "that the operation would complete quickly"
    if "permission" in actual.lower() or "denied" in actual.lower():
        return "that the required permission was granted"
    if "not found" in actual.lower():
        return "that the resource existed at the expected location"
    return "that the initial conditions were as assumed"


def _extract_corrected_understanding(task: str, expected: str, actual: str) -> str:
    """Heuristic: what is the corrected takeaway?"""
    # Simple placeholder; the intelligence layer will improve this.
    if "timeout" in actual.lower():
        return "to check progress and set realistic timeouts"
    if "permission" in actual.lower():
        return "to verify permissions before attempting the operation"
    if "not found" in actual.lower():
        return "to verify existence and correct path before proceeding"
    return "to verify preconditions and have a fallback plan"


def store_lesson(
    store: DocumentStore,
    critique: Critique,
    actor: str = "jarvis",
    session_id: str | None = None,
) -> str | None:
    """If the critique yielded a lesson, store it in the learned vault."""
    if not critique.lesson:
        return None  # No lesson to store

    note = remember(
        store,
        critique.lesson,
        kind="learned",
        tags=critique.tags,
        importance=critique.importance,
        phase="OBSERVED",  # Starts as observation, moves to VERIFIED via use
        actor=actor,
        provenance={"type": "self-critique", "session_id": session_id},
    )
    return note.document.path