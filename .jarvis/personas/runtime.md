# Runtime State

> Ephemeral. Current active persona overlay only. Not history.

## Current State

```yaml
active: false
persona_id: null
activated_at: null
activation_mode: null  # explicit | implicit | council
scope: null
```

## Rules

1. **Current state only.** This file represents what is active right now, not what was active before.
2. **Session-scoped.** On new session or startup, reset to `active: false`.
3. **No history.** Activation history belongs in `.jarvis/audit/` and `.jarvis/journal/`.
4. **Crash-safe.** If a session crashes, stale persona state does not survive. The file is reset on next startup.
5. **One overlay at a time.** Except council mode (sequential, reset between each).
6. **Derived, not authoritative.** This file is rebuilt from the session state, not treated as truth.