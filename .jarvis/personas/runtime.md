# Runtime State

> Current active persona overlay ONLY. Derived, rebuildable, ephemeral.

This file is **derived state** — it represents what is active right now. It must not become a permanent source of truth. If deleted, JARVIS reconstructs from context.

## Current State

```yaml
active: false
persona_id: null
activated_at: null
activation_type: null   # explicit | implicit | council
scope: null
```

## Transitions

When a persona activates:

```yaml
active: true
persona_id: persona.steve_jobs
activated_at: 2026-09-10T14:30:00Z
activation_type: explicit
scope: "Logo critique task"
```

When it deactivates:

```yaml
active: false
persona_id: null
activated_at: null
activation_type: null
scope: null
```

## Rules

1. Only one persona overlay active at a time (except council mode — sequential, one at a time)
2. **No history here** — previous activations belong in audit/journal/sessions
3. **Rebuildable** — if deleted, JARVIS reconstructs from context
4. **Advisory, not authoritative** — stale state from a crashed session is harmless; JARVIS knows from context whether a persona is active
5. **Council writes then clears** — each activation writes position before next loads

## History Locations

Previous activations are recorded in:

- `.jarvis/audit/` — event-sourced activation events
- `.jarvis/journal/` — knowledge model evolution
- `.jarvis/sessions/` — raw conversation history

This file is a snapshot. Those systems are the record.