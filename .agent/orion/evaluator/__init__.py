"""
ORION Self-Evaluation System

Evaluator as a logical role:
- Separates BUILDER from EVALUATOR
- Evaluates results against explicit criteria
- Drives correction loops until PASS or max corrections
"""

from .core import (
    EvaluatorConfig,
    EvaluationResult,
    EvaluationFinding,
    EvaluatorEngine,
    EvaluationVerdict,
    EvaluationFindingSeverity,
)
from .criteria import (
    EvaluationCriterion,
    CriterionType,
    DEFAULT_EVALUATION_CRITERIA,
)

__all__ = [
    "EvaluatorConfig",
    "EvaluationResult",
    "EvaluationFinding",
    "EvaluatorEngine",
    "EvaluationVerdict",
    "EvaluationFindingSeverity",
    "EvaluationCriterion",
    "CriterionType",
    "DEFAULT_EVALUATION_CRITERIA",
]
