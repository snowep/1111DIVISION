# ORION Memory

## Purpose

Selective, durable memory for the orchestrator. Not a log. Not a transcript. Only what improves future decisions.

---

## Memory Categories

### System Decisions
Architectural choices, version changes, structural modifications.

### Persona Registry
Active personas, their purposes, boundaries, status.

### Promotion Ledger
What was promoted from persona → shared → ORION, when, why.

### Cross-Persona Patterns
Recurring issues, successful delegation patterns, coordination improvements.

### Workspace Map
Project locations, research areas, experiment status, tool availability.

### Evolution Proposals
Submitted, tested, accepted/rejected system changes.

---

## Memory Rules

1. **No conversation fragments** — Extract the lesson, discard the chat
2. **No temporary state** — Runtime state goes in state.md, not memory
3. **No persona-private info** — Unless explicitly promoted
4. **One entry per durable fact** — Update in place, don't append duplicates
5. **Provenance preserved** — Source persona, date, confidence

---

## Format

Each entry:
```
[DATE] [CATEGORY] [CONFIDENCE]
Fact or decision.
Source: [persona|system|user|observation]
Ref: [file or commit if applicable]
```

---

## Current Entries

```
[2025-09-18] [SYSTEM_DECISION] [HIGH]
ORION backbone structure established with persona architecture.
Source: system
Ref: commit 7e8396a

[2025-09-19] [SYSTEM_DECISION] [HIGH]
Phase 4 complete: ORION Workspace + Tools with JARVIS-like Autonomy (23 tools, 47 permission rules).
Source: system
Ref: commit b3084ef

[2025-09-19] [SYSTEM_DECISION] [HIGH]
Cleanup completed: removed duplicate .agent/.agent/, test files, empty placeholders; restored backbone scaffolding.
Source: system
Ref: commit 2e22042

[2025-09-19] [PERSONA_REGISTRY] [HIGH]
Four personas scaffolded: Researcher, Developer, Designer, Analyst. Awaiting instantiation.
Source: system
Ref: config.md backbone definition
```

---

## Directory Structure

```
.agent/orion/
├── memory.md              # This file (overview + entries)
├── memory/
│   ├── decisions.md       # System decisions log
│   ├── long-term-context.md
│   └── user-preferences.md
├── identity.md
├── experience.md
├── experience/
│   └── task-records.md
├── knowledge/             # System knowledge
│   ├── memory-gate.md
│   ├── orion-pipeline.md
│   └── retrieval-architecture.md
├── skills/                # (empty - scaffolded)
├── evolution/             # (empty - scaffolded)
└── tools.py, permissions.py, core.py, permissions.json
```