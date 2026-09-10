# Runtime State

> Tracks which persona overlay is currently active, if any.

## Current State

```yaml
active_persona: null
persona_mode: null  # explicit | implicit | council | null
task_context: null
activated_at: null
```

## Transitions

| When | From | To | Trigger |
|------|------|----|---------|
| | | | |

## Rules

1. Only one persona overlay active at a time (except council mode, which is sequential)
2. Explicit activation: user says "act as X" or "be the X"
3. Implicit activation: JARVIS contextually applies perspective without announcing
4. Deactivation: "Drop the persona." or task completion
5. Council mode: sequential activation, one at a time, each produces output before next loads
6. JARVIS identity is always present — persona is an overlay, not a replacement