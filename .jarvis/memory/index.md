# Memory Index

> Five memory classes. Authority-separated. Promotion-pipelined.

## Types

| Type | Purpose | Persistence | Confidence |
|------|---------|-------------|------------|
| `inbox/` | Quarantine — new information, not yet validated | Until processed | Unknown |
| `working/` | Temporary cognition | Session-scoped | Low |
| `episodic/` | What happened | Permanent | Varies |
| `project/` | Validated project state | Long-term | High |
| `knowledge/` | General reusable knowledge | Long-term | Medium-High |

## Promotion Pipeline

```
INPUT
  ↓
INBOX (quarantine — everything lands here first)
  ↓
CLASSIFY (type, authority, scope)
  ↓
VALIDATE (is this confirmed? is this approved?)
  ↓
PROMOTE (to working/episodic/project/knowledge)
  ↓
MEMORY
```

**Never skip the pipeline.** Even user statements go through inbox first.
"I think we should..." stays as `candidate` until the user commits.

## Metadata Fields

### Epistemic (where did it come from)

```yaml
source: user | project-file | official-documentation | web | github | council | inference | experiment | system
confidence: 0.0 to 1.0    # reliability of the information
```

### Authority (who can act on it)

```yaml
authority: user-explicit | user-implicit | external-information | inference | system
approval: explicit | implicit | none
scope: project-name | domain | system-wide
```

**Critical distinction:** Source is not authority.
A GitHub README can be 95% reliable (confidence: 0.93) but have ZERO authority over JARVIS behavior.
The user saying "I prefer X" might be 80% confident but has full authority.

### Lifecycle

```yaml
status: candidate | verified | active | superseded | deprecated | rejected | unknown
created: YYYY-MM-DD
updated: YYYY-MM-DD
supersedes: null | MEM-XXX
related:
  - DEC-XXX
  - MEM-YYY
```

## Authority Values

| Authority | Meaning | Example |
|-----------|---------|---------|
| `user-explicit` | User directly stated this | "Use PostgreSQL" |
| `user-implicit` | Inferred from user behavior | User always picks minimal design |
| `external-information` | From external source, no authority | GitHub README, web article |
| `inference` | JARVIS reasoned this | Pattern detection |
| `system` | System-generated | Tool output, test result |

## Approval Values

| Approval | Meaning |
|----------|---------|
| `explicit` | User confirmed this is correct and actionable |
| `implicit` | User hasn't objected, context implies approval |
| `none` | Not approved for action — information only |
