# Memory Index

> Four kinds of memory. Each with different persistence, confidence, and purpose.

## Types

| Type | Purpose | Persistence | Confidence |
|------|---------|-------------|------------|
| `working/` | Temporary cognition | Session-scoped | Low |
| `episodic/` | What happened | Permanent | Varies |
| `project/` | Validated project state | Long-term | High |
| `knowledge/` | General reusable knowledge | Long-term | Medium-High |

## Rules

1. **Working memory** is aggressively disposable. It should be cleared when the task is done.
2. **Episodic memory** is history. It does NOT mean the conclusions are true.
3. **Project memory** is validated state. Only verified facts go here.
4. **Knowledge memory** is reusable across projects. General patterns and principles.

## Metadata

Every persisted memory should have frontmatter:

```yaml
---
id: MEM-20260910-001
type: project-decision
status: active
source: user
confidence: 1.0
created: 2026-09-10
updated: 2026-09-10
supersedes: null
related:
  - DEC-002
---
```

## Source Values

`user` | `project-file` | `official-documentation` | `web` | `github` | `council` | `inference` | `experiment` | `system`

## Status Values

`candidate` | `verified` | `active` | `superseded` | `deprecated` | `rejected` | `unknown`
