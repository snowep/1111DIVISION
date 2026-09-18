# ORION Experience

## Purpose

Record of what ORION has actually done and learned. Distinct from knowledge (what is known) and memory (what is remembered for decisions).

---

## Experience Categories

### Completed Tasks
Verified work with outcomes.

### Delegation Patterns
Which personas for which task types, success rates.

### Verification Results
What passed, what failed, what was caught in review.

### Failure Recoveries
How failures were detected, diagnosed, corrected.

### System Improvements
Changes proposed, tested, adopted.

### Tool/Workflow Discoveries
Effective command sequences, retrieval patterns, automation.

---

## Format

Each entry:
```
[DATE] [CATEGORY] [EXP_AWARDED]
Task or event description.
Outcome: [success|partial|failure|discovery]
Lesson: [what was learned]
Ref: [commit, file, or task ID]
```

---

## Current Entries

```
[2025-09-18] [SYSTEM_IMPROVEMENT] [100]
Initial ORION system structure with persona architecture.
Outcome: success
Lesson: Scaffold structure first, instantiate on demand.
Ref: commit 7e8396a

[2025-09-19] [TOOL_WORKFLOW] [50]
Phase 4: 23 tools integrated with permissions engine (4 levels, 7 categories, 5 operations).
Outcome: success
Lesson: Autonomous for safe ops, confirm for risky; pipeline integration needs verification fix.
Ref: commit b3084ef

[2025-09-19] [FAILURE_RECOVERY] [10]
Cleanup removed backbone scaffolding directories; restored after user correction.
Outcome: recovery
Lesson: Empty directories are intentional scaffolding — verify before deleting.
Ref: commit 2e22042
```

---

## Directory Structure

```
.agent/orion/
├── experience.md          # This file (overview + entries)
├── experience/
│   └── task-records.md    # Detailed task records (4KB)
├── memory.md
├── memory/
│   ├── decisions.md
│   ├── long-term-context.md
│   └── user-preferences.md
├── identity.md
├── knowledge/
│   ├── memory-gate.md
│   ├── orion-pipeline.md
│   └── retrieval-architecture.md
├── skills/                # (empty - scaffolded)
├── evolution/             # (empty - scaffolded)
└── tools.py, permissions.py, core.py, permissions.json
```