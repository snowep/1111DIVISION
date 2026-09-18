"""
Evaluator-driven correction pipeline.

This module formalizes the Phase 5 loop:

    BUILDER → RESULT → EVALUATOR → PASS → DONE
                                ↓
                               FAIL → CORRECT → VERIFY
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from .core import EvaluatorEngine, EvaluationResult


@dataclass
class CorrectionAttempt:
    """Record of one correction cycle."""
    cycle: int
    findings: list[str]
    action: str
    success: bool
    verification: dict


class EvaluatorPipeline:
    """
    Orchestrates the Evaluator correction loop.

    The pipeline keeps the Builder and Evaluator as separate logical roles.
    The Builder produces results; the Evaluator judges them.
    """

    def __init__(self, evaluator: EvaluatorEngine):
        self.evaluator = evaluator
        self.max_cycles = evaluator.config.max_correction_cycles

    def run(
        self,
        task: object,
        builder: Callable[[object], dict],
        verifier: Callable[[object], dict],
        corrector: Callable[[object, EvaluationResult], dict],
        on_pass: Optional[Callable[[object, EvaluationResult], None]] = None,
        on_fail: Optional[Callable[[object, EvaluationResult], None]] = None,
    ) -> EvaluationResult:
        """
        Run the full BUILDER → EVALUATOR pipeline.

        Args:
            task: Task object being evaluated.
            builder: Produces the task result.
            verifier: Produces verification evidence.
            corrector: Applies corrections when evaluation fails.
            on_pass: Optional callback invoked when evaluation passes.
            on_fail: Optional callback invoked when evaluation fails.

        Returns:
            Final EvaluationResult.
        """
        result = builder(task)
        task.final_result = result

        for cycle in range(1, self.max_cycles + 2):
            verification = verifier(task)
            evaluation = self.evaluator.evaluate(
                task,
                verification=verification,
                correction_budget_remaining=self.max_cycles - (cycle - 1),
                evaluation_cycle=cycle,
            )

            if evaluation.passed:
                if on_pass:
                    on_pass(task, evaluation)
                return evaluation

            if not evaluation.requires_correction:
                if on_fail:
                    on_fail(task, evaluation)
                return evaluation

            correction = corrector(task, evaluation)
            correction_record = CorrectionAttempt(
                cycle=cycle,
                findings=[f.message for f in evaluation.findings],
                action=str(correction),
                success=bool(correction),
                verification=verification,
            )
            if not hasattr(task, "correction_attempts"):
                task.correction_attempts = []
            task.correction_attempts.append(correction_record)

            # Re-verify after correction before the next evaluation.
            verification = verifier(task)

        final_verification = verifier(task)
        final_evaluation = self.evaluator.evaluate(
            task,
            verification=final_verification,
            correction_budget_remaining=0,
            evaluation_cycle=self.max_cycles + 1,
        )
        if on_fail and not final_evaluation.passed:
            on_fail(task, final_evaluation)
        return final_evaluation
