"""
Evaluation criteria used by the ORION Evaluator.

Criteria are explicit, measurable, and auditable. The Evaluator does not
guess; it scores against defined dimensions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional


class CriterionType(str, Enum):
    """Type of evaluation criterion."""
    OBJECTIVE = "objective"
    VERIFICATION = "verification"
    COMPLETENESS = "completeness"
    CORRECTNESS = "correctness"
    SAFETY = "safety"
    REPRODUCIBILITY = "reproducibility"
    QUALITY = "quality"
    EFFICIENCY = "efficiency"


@dataclass
class EvaluationCriterion:
    """
    A measurable evaluation criterion.

    Attributes:
        key: Stable identifier for the criterion.
        label: Human-readable name.
        weight: Relative importance in overall scoring (0.0-1.0).
        description: What this criterion measures.
        pass_threshold: Minimum score for this criterion to pass (0.0-1.0).
        required: Whether failure on this criterion forces overall FAIL.
        evaluator: Optional callable that computes the score for this criterion.
    """
    key: str
    label: str
    weight: float = 1.0
    description: str = ""
    pass_threshold: float = 0.7
    required: bool = False
    evaluator: Optional[Callable[[object, object], float]] = None

    def validate(self) -> None:
        """Validate criterion configuration."""
        if not self.key or not self.label:
            raise ValueError("Criterion requires key and label")
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"Criterion {self.key} weight must be between 0 and 1")
        if not 0.0 <= self.pass_threshold <= 1.0:
            raise ValueError(f"Criterion {self.key} pass_threshold must be between 0 and 1")


DEFAULT_EVALUATION_CRITERIA = [
    EvaluationCriterion(
        key="objective_met",
        label="Objective Met",
        weight=0.35,
        description="The delivered result satisfies the stated objective and success criteria.",
        pass_threshold=0.8,
        required=True,
    ),
    EvaluationCriterion(
        key="verification_passed",
        label="Verification Passed",
        weight=0.25,
        description="Verification evidence confirms the result works as intended.",
        pass_threshold=0.75,
        required=True,
    ),
    EvaluationCriterion(
        key="completeness",
        label="Completeness",
        weight=0.15,
        description="All required steps, artifacts, and edge cases are addressed.",
        pass_threshold=0.7,
    ),
    EvaluationCriterion(
        key="correctness",
        label="Correctness",
        weight=0.15,
        description="The result is accurate, internally consistent, and free of critical errors.",
        pass_threshold=0.75,
        required=True,
    ),
    EvaluationCriterion(
        key="safety",
        label="Safety",
        weight=0.10,
        description="The result respects permissions, avoids destructive side effects, and handles risk.",
        pass_threshold=0.8,
        required=True,
    ),
]


def normalize_criteria(criteria: List[EvaluationCriterion]) -> List[EvaluationCriterion]:
    """Validate and return a normalized criterion list."""
    for criterion in criteria:
        criterion.validate()
    return criteria


def criterion_score(
    criterion: EvaluationCriterion,
    evaluator: EvaluatorEngine,
    task: object,
    verification: Optional[dict] = None,
) -> float:
    """
    Compute a criterion score.

    Uses a custom evaluator when provided; otherwise falls back to the
    evaluator engine's built-in scoring method.
    """
    if criterion.evaluator is not None:
        return criterion.evaluator(evaluator, task)

    method_name = f"score_{criterion.key}"
    method = getattr(evaluator, method_name, None)
    if method is None:
        return 0.0

    try:
        return float(method(task, verification or {}))
    except TypeError:
        return float(method(task))


# Avoid circular import by resolving the type hint at runtime.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .core import EvaluatorEngine