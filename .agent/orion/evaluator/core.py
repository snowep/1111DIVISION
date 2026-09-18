"""
ORION Evaluator Engine

The Evaluator is a logical role that is deliberately separate from the Builder.
It evaluates produced results against explicit, measurable criteria and drives
the correction loop until the result passes or the correction budget is exhausted.

Pipeline:
    BUILDER → RESULT → EVALUATOR → PASS → DONE
                                ↓
                               FAIL → CORRECT → VERIFY
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from .criteria import (
    DEFAULT_EVALUATION_CRITERIA,
    EvaluationCriterion,
    normalize_criteria,
)


class EvaluationVerdict(str, Enum):
    """Overall evaluation verdict."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"


class EvaluationFindingSeverity(str, Enum):
    """Severity of an evaluation finding."""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class EvaluationFinding:
    """A single finding produced by the Evaluator."""
    criterion: str
    severity: EvaluationFindingSeverity
    message: str
    evidence: str = ""
    suggestion: Optional[str] = None
    resolved: bool = False

    def to_dict(self) -> dict:
        return {
            "criterion": self.criterion,
            "severity": self.severity.value,
            "message": self.message,
            "evidence": self.evidence,
            "suggestion": self.suggestion,
            "resolved": self.resolved,
        }


@dataclass
class EvaluationResult:
    """
    Complete output of an evaluation cycle.

    Attributes:
        verdict: PASS, FAIL, or WARNING.
        score: Normalized overall score (0.0-1.0).
        criterion_scores: Per-criterion scores.
        findings: Detailed findings that explain the verdict.
        requires_correction: Whether the result must enter the correction loop.
        correction_budget_remaining: Remaining correction attempts.
        evaluated_at: ISO timestamp of evaluation.
    """
    verdict: EvaluationVerdict
    score: float
    criterion_scores: Dict[str, float]
    findings: List[EvaluationFinding] = field(default_factory=list)
    requires_correction: bool = False
    correction_budget_remaining: int = 0
    evaluated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    evaluation_cycle: int = 1
    notes: str = ""

    @property
    def passed(self) -> bool:
        return self.verdict == EvaluationVerdict.PASS

    @property
    def failed(self) -> bool:
        return self.verdict == EvaluationVerdict.FAIL

    @property
    def has_warnings(self) -> bool:
        return any(f.severity == EvaluationFindingSeverity.WARNING for f in self.findings)

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict.value,
            "score": round(self.score, 4),
            "criterion_scores": {k: round(v, 4) for k, v in self.criterion_scores.items()},
            "findings": [f.to_dict() for f in self.findings],
            "requires_correction": self.requires_correction,
            "correction_budget_remaining": self.correction_budget_remaining,
            "evaluated_at": self.evaluated_at,
            "evaluation_cycle": self.evaluation_cycle,
            "notes": self.notes,
        }


@dataclass
class EvaluatorConfig:
    """
    Configuration for the Evaluator.

    Attributes:
        criteria: Ordered list of evaluation criteria.
        pass_threshold: Minimum overall score for PASS.
        warning_threshold: Minimum score for WARNING; below this is FAIL.
        max_correction_cycles: Maximum correction attempts before final FAIL.
        require_verification: Whether verification evidence is mandatory.
        require_no_critical_findings: Whether any CRITICAL finding forces FAIL.
        scoring_weights: Optional override map for criterion weights.
    """
    criteria: List[EvaluationCriterion] = field(default_factory=lambda: list(DEFAULT_EVALUATION_CRITERIA))
    pass_threshold: float = 0.8
    warning_threshold: float = 0.6
    max_correction_cycles: int = 3
    require_verification: bool = True
    require_no_critical_findings: bool = True
    scoring_weights: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.criteria = normalize_criteria(self.criteria)
        if not 0.0 <= self.warning_threshold <= self.pass_threshold <= 1.0:
            raise ValueError("Thresholds must satisfy 0 <= warning <= pass <= 1")
        if self.max_correction_cycles < 0:
            raise ValueError("max_correction_cycles cannot be negative")
        if self.scoring_weights:
            for criterion in self.criteria:
                if criterion.key in self.scoring_weights:
                    criterion.weight = self.scoring_weights[criterion.key]


class EvaluatorEngine:
    """
    Evaluates task results against explicit criteria.

    The Evaluator is intentionally separate from the Builder. It does not
    implement the task; it judges whether the produced result is good enough.
    """

    def __init__(self, root: Path | str, config: Optional[EvaluatorConfig] = None):
        self.root = Path(root)
        self.config = config or EvaluatorConfig()

    def evaluate(
        self,
        task: object,
        verification: Optional[dict] = None,
        correction_budget_remaining: Optional[int] = None,
        evaluation_cycle: int = 1,
    ) -> EvaluationResult:
        """
        Evaluate a task result.

        The evaluation is criterion-driven. Each criterion receives a score,
        then scores are weighted into an overall result.
        """
        verification = verification or {}
        budget = (
            self.config.max_correction_cycles
            if correction_budget_remaining is None
            else correction_budget_remaining
        )

        criterion_scores = {
            criterion.key: self._score_criterion(criterion, task, verification)
            for criterion in self.config.criteria
        }

        findings = self._build_findings(criterion_scores, task, verification)
        overall_score = self._weighted_score(criterion_scores)

        critical_failure = (
            self.config.require_no_critical_findings
            and any(f.severity == EvaluationFindingSeverity.CRITICAL for f in findings)
        )
        verification_missing = (
            self.config.require_verification
            and not verification
        )

        if critical_failure or verification_missing or overall_score < self.config.warning_threshold:
            verdict = EvaluationVerdict.FAIL
        elif overall_score < self.config.pass_threshold or any(
            f.severity == EvaluationFindingSeverity.WARNING for f in findings
        ):
            verdict = EvaluationVerdict.WARNING
        else:
            verdict = EvaluationVerdict.PASS

        requires_correction = verdict in (EvaluationVerdict.FAIL, EvaluationVerdict.WARNING)
        if requires_correction and budget <= 0:
            verdict = EvaluationVerdict.FAIL
            requires_correction = False

        return EvaluationResult(
            verdict=verdict,
            score=overall_score,
            criterion_scores=criterion_scores,
            findings=findings,
            requires_correction=requires_correction,
            correction_budget_remaining=max(0, budget - 1 if requires_correction else budget),
            evaluation_cycle=evaluation_cycle,
            notes=self._build_notes(verdict, findings, overall_score),
        )

    def _score_criterion(self, criterion: EvaluationCriterion, task: object, verification: dict) -> float:
        """Score one criterion using the criterion's evaluator or a built-in scorer."""
        method_name = f"score_{criterion.key}"
        method = getattr(self, method_name, None)
        if method is None:
            return 0.0

        try:
            return float(method(task, verification))
        except TypeError:
            return float(method(task))
        except Exception:
            return 0.0

    def _weighted_score(self, criterion_scores: Dict[str, float]) -> float:
        """Compute weighted overall score."""
        total_weight = sum(
            criterion.weight for criterion in self.config.criteria
        )
        if total_weight <= 0:
            return 0.0

        weighted_sum = 0.0
        for criterion in self.config.criteria:
            score = criterion_scores.get(criterion.key, 0.0)
            weighted_sum += score * criterion.weight

        return max(0.0, min(1.0, weighted_sum / total_weight))

    def _build_findings(
        self,
        criterion_scores: Dict[str, float],
        task: object,
        verification: dict,
    ) -> List[EvaluationFinding]:
        """Build detailed findings from criterion scores."""
        findings = []

        for criterion in self.config.criteria:
            score = criterion_scores.get(criterion.key, 0.0)
            if score >= criterion.pass_threshold:
                continue

            severity = (
                EvaluationFindingSeverity.CRITICAL
                if criterion.required and score < criterion.pass_threshold * 0.5
                else EvaluationFindingSeverity.WARNING
            )
            findings.append(EvaluationFinding(
                criterion=criterion.key,
                severity=severity,
                message=f"{criterion.label} scored {score:.2f} below threshold {criterion.pass_threshold:.2f}",
                evidence=self._evidence_for(criterion.key, task, verification),
                suggestion=self._suggestion_for(criterion.key),
            ))

        failed_execution_steps = self._failed_execution_steps(task)
        if failed_execution_steps:
            findings.append(EvaluationFinding(
                criterion="correctness",
                severity=EvaluationFindingSeverity.CRITICAL,
                message=f"{len(failed_execution_steps)} execution step(s) failed",
                evidence="; ".join(failed_execution_steps),
                suggestion="Correct failed steps and re-verify the result.",
            ))

        if not self._has_final_result(task):
            findings.append(EvaluationFinding(
                criterion="completeness",
                severity=EvaluationFindingSeverity.CRITICAL,
                message="No final result was produced",
                evidence="task.final_result is empty",
                suggestion="Produce a final result before evaluation.",
            ))

        return findings

    def _evidence_for(self, criterion_key: str, task: object, verification: dict) -> str:
        """Return compact evidence for a criterion."""
        if criterion_key == "objective_met":
            return str(getattr(task, "objective", ""))[:300]
        if criterion_key == "verification_passed":
            return json.dumps(verification)[:500]
        if criterion_key == "completeness":
            return f"plan={len(getattr(task, 'plan', []))}, executed={len(getattr(task, 'execution_log', []))}"
        if criterion_key == "correctness":
            return f"critique={len(getattr(task, 'critique_findings', []))}, corrections={len(getattr(task, 'corrections', []))}"
        if criterion_key == "safety":
            return f"approvals={len(getattr(task, 'approval_requests', []))}"
        return ""

    def _suggestion_for(self, criterion_key: str) -> str:
        suggestions = {
            "objective_met": "Re-check the objective and ensure the result directly satisfies it.",
            "verification_passed": "Add verification evidence or fix the failing verification.",
            "completeness": "Complete missing steps, artifacts, or edge cases.",
            "correctness": "Resolve correctness issues and re-run verification.",
            "safety": "Review permissions and remove unsafe side effects.",
            "reproducibility": "Document inputs and steps so the result can be reproduced.",
            "quality": "Improve maintainability, clarity, or user experience.",
            "efficiency": "Reduce unnecessary work or resource usage.",
        }
        return suggestions.get(criterion_key, "Review and improve the result.")

    def _failed_execution_steps(self, task: object) -> List[str]:
        return [
            str(log.get("action", "unknown"))
            for log in getattr(task, "execution_log", [])
            if not log.get("success", False)
        ]

    def _has_final_result(self, task: object) -> bool:
        return bool(getattr(task, "final_result", None))

    def _build_notes(
        self,
        verdict: EvaluationVerdict,
        findings: List[EvaluationFinding],
        score: float,
    ) -> str:
        if verdict == EvaluationVerdict.PASS:
            return f"Result passed evaluation with score {score:.2f}."
        if verdict == EvaluationVerdict.WARNING:
            return f"Result has warnings; correction recommended before completion."
        return f"Result failed evaluation with score {score:.2f}; correction required."

    # ------------------------------------------------------------------
    # Built-in criterion scorers
    # ------------------------------------------------------------------

    def score_objective_met(self, task: object, verification: dict) -> float:
        if not self._has_final_result(task):
            return 0.0
        if verification.get("objective_met") is True:
            return 1.0
        if verification.get("objective_met") is False:
            return 0.0
        return 0.5

    def score_verification_passed(self, task: object, verification: dict) -> float:
        if not verification:
            return 0.0
        overall = verification.get("overall")
        if overall == "PASS":
            return 1.0
        if overall == "WARNING":
            return 0.6
        if overall == "FAIL":
            return 0.0

        checks = [verification.get(key) for key in (
            "plan_coverage", "objective_met", "artifacts_exist", "no_regressions"
        ) if key in verification]
        if not checks:
            return 0.0
        return sum(1 for value in checks if value is True) / len(checks)

    def score_completeness(self, task: object, verification: dict) -> float:
        plan = getattr(task, "plan", [])
        executed = getattr(task, "execution_log", [])
        if not plan:
            return 0.5
        coverage = min(1.0, len(executed) / len(plan))
        if not self._has_final_result(task):
            coverage *= 0.5
        return coverage

    def score_correctness(self, task: object, verification: dict) -> float:
        total = len(getattr(task, "execution_log", []))
        if total == 0:
            return 0.0
        successful = sum(1 for log in task.execution_log if log.get("success", False))
        base = successful / total

        critique = getattr(task, "critique_findings", [])
        critical = sum(1 for item in critique if "CRITICAL" in str(item) or "FAIL" in str(item))
        if critical:
            base *= 0.3

        return max(0.0, min(1.0, base))

    def score_safety(self, task: object, verification: dict) -> float:
        approvals = getattr(task, "approval_requests", [])
        if not approvals:
            return 1.0

        # Pending approvals indicate a controlled risk boundary, not a failure.
        # Unresolved high-risk operations reduce the score.
        unresolved = [a for a in approvals if not a.get("resolved", False)]
        if not unresolved:
            return 1.0

        return max(0.0, 0.5 - 0.1 * len(unresolved))

    def score_reproducibility(self, task: object, verification: dict) -> float:
        # Reproducibility is inferred from documented plan and execution logs.
        has_plan = bool(getattr(task, "plan", []))
        has_logs = bool(getattr(task, "execution_log", []))
        return 0.5 + 0.25 * has_plan + 0.25 * has_logs

    def score_quality(self, task: object, verification: dict) -> float:
        if not self._has_final_result(task):
            return 0.0
        if not getattr(task, "critique_findings", []):
            return 0.8
        return 0.6

    def score_efficiency(self, task: object, verification: dict) -> float:
        # Efficiency is informational unless explicitly measured.
        return 0.7
