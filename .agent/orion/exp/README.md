# ORION EXP

## Purpose

EXP measures verified useful experience, not activity volume.

## Pipeline

```
Task completed
       ↓
Verified
       ↓
Experience recorded
       ↓
EXP awarded
       ↓
Level updated
```

## Rules

1. EXP is only awarded after evaluation passes.
2. Duplicate task IDs cannot earn EXP twice.
3. EXP is not a productivity metric.
4. EXP exists to track verified capability growth, not to incentivize activity.

## Files

- `manager.py` — EXPManager, EXPRecord, EXPLevel, EXPEvent
