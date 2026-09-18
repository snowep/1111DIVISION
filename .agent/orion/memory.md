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

*[Empty — system initialized 2025-09-18]*