# Personas

> Permanent definitions in vault. Temporary instances in .jarvis.

## Two Layers

### Definition (vault)

Permanent persona definition. Never changes during runtime.

```text
vault/05 Personas/
├── Council/
│   ├── Security Architect.md
│   ├── Systems Engineer.md
│   ├── Creative Director.md
│   └── ...
├── Specialists/
│   └── ...
└── README.md
```

### Instance (.jarvis)

Temporary runtime context. Created for specific tasks, archived after use.

```text
.jarvis/personas/
├── instances/
│   ├── SEC-20260910-01/
│   │   ├── context.md      # Why this persona was invoked
│   │   ├── task.md         # What it needs to analyze
│   │   ├── arguments.md    # Its reasoning
│   │   ├── observations.md # What it found
│   │   └── conclusion.md   # Its recommendation
│   ├── SYS-20260910-01/
│   │   └── ...
│   └── README.md
└── README.md
```

## Lifecycle

```
1. User requests persona analysis
    ↓
2. JARVIS loads definition from vault
    ↓
3. JARVIS creates instance in .jarvis/personas/instances/
    ↓
4. Instance performs analysis
    ↓
5. Instance produces conclusion
    ↓
6. Instance is archived or deleted
    ↓
7. Definition remains unchanged
```

## Why This Matters

**Without this separation:**

- Temporary reasoning contaminates permanent definition
- Persona "learns" from one-off analysis
- Definition becomes polluted with session-specific context

**With this separation:**

- Definition is stable, versioned, curated
- Instance is disposable, temporary, focused
- No cross-contamination

## Instance Format

```yaml
# .jarvis/personas/instances/SEC-20260910-01/context.md

---
instance_id: SEC-20260910-01
persona: Security Architect
invoked: 2026-09-10T14:30:00Z
task: Review authentication architecture
status: active
---

## Context

User requested security review of authentication system.
This is a one-time analysis, not ongoing monitoring.
```

```yaml
# .jarvis/personas/instances/SEC-20260910-01/conclusion.md

---
instance_id: SEC-20260910-01
persona: Security Architect
completed: 2026-09-10T15:00:00Z
status: complete
---

## Conclusion

Found 3 critical vulnerabilities:
1. ...
2. ...
3. ...

## Recommendation

Immediate action required on #1 and #2.
```

## Archival

After use, instances can be:

1. **Deleted** — if the analysis is no longer relevant
2. **Archived** — if the analysis might be referenced later

Archived instances move to:

```text
.jarvis/personas/archived/
├── SEC-20260910-01/
│   └── ...
└── README.md
```

## Rules

1. **Definitions are permanent** — never modified by instances
2. **Instances are temporary** — created for tasks, deleted/archived after
3. **No cross-contamination** — instance reasoning stays in instance
4. **Audit trail** — instance creation and conclusion are logged
5. **User control** — user can request specific persona for analysis
