# Conflicts

> Contradiction records. Detected, resolved, or visible.

## Purpose

When new information contradicts existing memory or the world model, a conflict record is created. Conflicts are never silently merged.

## Structure

```text
.jarvis/conflicts/
├── open/          # Unresolved conflicts
├── resolved/      # Conflicts with resolution
└── README.md
```

## Detection Procedure

```
new information
      ↓
conflict detector (checks existing memory + world model)
      ↓
┌──────────────┐
│ conflict?    │
└──────┬───────┘
       │
     YES
       ↓
create conflict record (.jarvis/conflicts/open/)
       ↓
resolve using: source, authority, recency, scope, evidence
       ↓
update world model
```

## Conflict Record

```yaml
---
conflict_id: CON-20260910-001
type: memory-vs-memory | memory-vs-world-model | world-model-vs-observation
detected: 2026-09-10T14:30:00Z
detected_by: jarvis

claim_a:
  id: MEM-20260910-001
  content: "Use PostgreSQL"
  source: user
  authority: user-explicit
  confidence: 1.0
  valid_until: null

claim_b:
  id: MEM-20260910-002
  content: "Project uses SQLite"
  source: github
  authority: external-information
  confidence: 0.93
  valid_until: null

resolution:
  status: open | pending | resolved
  decided_by: null
  decided: null
  winner: null
  rationale: null
  supersedes: null

created: 2026-09-10
updated: 2026-09-10
---
```

## Resolution Criteria

When resolving a conflict, weigh in order:

1. **Authority** — who can act on this? (user-explicit > external-information)
2. **Source** — where did it come from? (direct inspection > secondhand)
3. **Recency** — which is newer? (newer evidence usually wins)
4. **Scope** — which is more specific to this context?
5. **Evidence** — which is supported by observable fact?

## Resolution Example

```yaml
---
conflict_id: CON-20260910-001
type: memory-vs-memory
detected: 2026-09-10T14:30:00Z

claim_a: # user
  content: "Use PostgreSQL"
  authority: user-explicit
  confidence: 1.0

claim_b: # github
  content: "Project uses SQLite"
  authority: external-information
  confidence: 0.93

resolution:
  status: resolved
  decided_by: user
  decided: 2026-09-10T15:00:00Z
  winner: claim_a
  rationale: "User has authority over project decisions;
              GitHub content was a stale README"
  supersedes: MEM-20260910-002
---
```

After resolution:

1. Update world model to reflect winner
2. Mark loser as `superseded` (or `rejected` if incorrect)
3. Move conflict record from `open/` to `resolved/`
4. Record in journal under `corrections/`
5. Record audit event

## Rules

1. **Never silently merge conflicts** — resolution must be explicit
2. **Unresolved conflicts stay visible** — they remain in `open/`
3. **Records the loser** — superseded claims are traceable, not deleted
4. **Resolution is justified** — winner chosen with rationale, not whim
5. **World model updates require resolution** — the model is not patched around conflicts