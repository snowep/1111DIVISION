# ORION Evaluator

## Purpose

The Evaluator is a logical role that is separate from the Builder.

The Builder produces results. The Evaluator judges whether those results are good enough.

## Pipeline

```
BUILDER → RESULT → EVALUATOR → PASS → DONE
                            ↓
                           FAIL → CORRECT → VERIFY
```

## Rules

1. No task is done until it passes evaluation.
2. Evaluation is criterion-driven, not intuition-driven.
3. FAIL triggers correction and re-verification.
4. Correction loops are bounded.
5. The Evaluator may eventually become its own persona.

## Files

- `core.py` — EvaluatorConfig, EvaluationResult, EvaluatorEngine
- `criteria.py` — EvaluationCriterion, CriterionType, default criteria
- `pipeline.py` — EvaluatorPipeline correction loop
