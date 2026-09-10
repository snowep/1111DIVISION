# Journal

> What happened to the knowledge model?

## Purpose

The journal records the **evolutionary history of knowledge** — how beliefs, decisions, and understanding changed over time.

Different from audit:
- **Audit** = what did the system do? (events, actions, mutations)
- **Journal** = what happened to the knowledge model? (beliefs, decisions, corrections)

## Structure

```text
.jarvis/journal/
├── observations/        # Raw observations that influenced knowledge
├── beliefs/             # Belief states and their evolution
├── decisions/           # Decision lifecycle: created → challenged → modified → superseded
├── state-transitions/   # Memory state changes with reasoning
└── corrections/         # When JARVIS was wrong, and what corrected it
```

## Sub-journals

### Observations

What JARVIS observed that changed understanding:

```yaml
---
observation_id: OBS-20260910-001
observed: 2026-09-10T14:30:00Z
actor: jarvis
observation: "User said the repo may use SQLite"
influenced:
  - MEM-20260910-001
---
```

### Beliefs

States JARVIS held and their evolution:

```yaml
---
belief_id: BEL-20260910-001
topic: project-database
held_from: 2026-09-01
held_until: 2026-09-10
belief: "Project uses SQLite"
confidence_during: 0.7
changed_by: MEM-20260910-001 (explicit user correction)
replaced_by: null or BEL-...
---
```

### Decisions

The full lifecycle of a decision:

```text
DEC-004
created
    ↓
challenged
    ↓
modified
    ↓
superseded
```

```yaml
---
decision_id: DEC-004
topic: Lore Strategy
lifecycle:
  - date: 2026-08-01
    stage: created
    note: "Initial open question"
  - date: 2026-09-10
    stage: challenged
    note: "User raised new considerations"
  - date: 2026-09-15
    stage: modified
    note: "Scope narrowed to brand canon only"
  - date: 2026-10-01
    stage: superseded
    note: "Replaced by DEC-005"
---
```

### State-Transitions

Formal memory state changes with the reasoning:

```yaml
---
transition_id: TRX-20260910-001
date: 2026-09-10T14:35:00Z
target: MEM-20260910-001
from_status: candidate
to_status: active
trigger: explicit_user_confirmation
evidence:
  - conversation message_id
---
```

### Corrections

When JARVIS was wrong, and what set it right:

```yaml
---
correction_id: COR-20260910-001
date: 2026-09-10T15:00:00Z
wrong_belief: MEM-20260910-050 "Project uses SQLite"
was_wrong_because: "Inferred from user hesitation, not verified"
corrected_to: "Project uses PostgreSQL (explicit user statement)"
corrected_by: user
source_of_correction:
  type: conversation
  message_id: ...
---
```

## Journal vs Audit

| Dimension | Audit | Journal |
|-----------|-------|---------|
| Question | What did the system do? | What happened to knowledge? |
| Primarily | Actions, events | Beliefs, decisions |
| Focus | Operations | Epistemics |
| Nature | Append-only event log | Evolutionary narrative |
| Example | `memory.promote` event | Decision lifecycle: created → challenged → superseded |

Both are needed. They answer different questions.

## Rules

1. **Journal entries are append-only** — history is not rewritten
2. **Corrections reference what was wrong** — never silently fix the past
3. **Decisions record their lifecycle** — created, challenged, modified, superseded
4. **Journal feeds the world model** — evolutionary history informs current state
5. **Audit and journal stay separate** — different questions, different records