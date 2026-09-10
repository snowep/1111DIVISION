# Runtime State

> Current active persona overlay ONLY. Derived, rebuildable, ephemeral.

This file is **derived state** — it represents what is active right now. It is not a source of truth. It contains no history. It is rebuildable from context.

## Current State

```yaml
active: false
persona_id: null
activated_at: null
activation_type: null  # explicit | implicit | council
task_context: null
```

## Transitions

When a persona activates:

```yaml
active: true
persona_id: persona.steve_jobs
activated_at: 2026-09-10T14:30:00Z
activation_type: explicit
task_context: "Critique the new logo"
```

When it deactivates:

```yaml
active: false
persona_id: null
activated_at: null
activation_type: null
task_context: null
```

## Rules

1. **Only one overlay at a time** (except council mode, which is sequential)
2. **No history here** — history belongs in audit/journal/sessions
3. **Rebuildable** — if deleted, JARVIS reconstructs from context
4. **Stale state is safe** — a crashed session may leave stale state; JARVIS rebuilds from conversation context on next session. This file is advisory, not authoritative.
5. **Council mode** — sequential activation, one at a time. Each activation writes position then clears.

## History Lives Elsewhere

| System | What it records |
|--------|----------------|
| `.jarvis/audit/` | Event-sourced mutation history |
| `.jarvis/journal/` | Knowledge model evolution |
| `.jarvis/sessions/` | Raw conversation history |

This file is a snapshot. Those systems are the record.