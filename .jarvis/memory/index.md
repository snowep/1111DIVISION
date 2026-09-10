# Memory Index

> Five memory classes. Authority-separated. Provenance-tracked. Promotion-gated. Time-aware.

## Memory Types

| Type | Purpose | Persistence | Confidence |
|------|---------|-------------|------------|
| `inbox/` | Quarantine — new information, not yet validated | Until processed | Unknown |
| `working/` | Temporary cognition | Session-scoped | Low |
| `episodic/` | What happened | Permanent | Varies |
| `project/` | Validated project state | Long-term | High |
| `knowledge/` | General reusable knowledge | Long-term | Medium-High |

## Storage Layers

Markdown/YAML is the canonical human-readable state. Operational layers are derived and rebuildable.

```
Markdown/YAML   → canonical state (source of truth)
SQLite          → operational indexing / transactions (derived)
Vector index    → semantic retrieval (derived)
Graph           → relationships (derived)
Cache           → performance (derived)
```

**Rule:** The runtime layers are rebuilt from canonical Markdown. They are never authoritative on their own.

## Memory Promotion Gate

Every piece of new information passes through the gate before entering memory:

```
            NEW INFORMATION
                   │
                   ▼
          ┌─────────────────┐
          │ MEMORY GATE     │
          ├─────────────────┤
          │ relevance       │
          │ provenance      │
          │ authority       │
          │ confidence      │
          │ contradiction   │
          │ sensitivity     │
          │ duplication     │
          │ longevity       │
          └────────┬────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
      REJECT     CANDIDATE   PROMOTE
```

### Gate Checks

| Check | Question |
|-------|----------|
| Relevance | Does this matter now or later? |
| Provenance | Do we know where it came from? |
| Authority | Who can act on this? |
| Confidence | How likely is it correct? |
| Contradiction | Does it conflict with existing memory? (→ .jarvis/conflicts/) |
| Sensitivity | Is this safe to store? |
| Duplication | Do we already have this? |
| Longevity | Will this still matter later? |

### Outcomes

- **REJECT** — fails gate (irrelevant, unsafe, unverifiable, duplicate)
- **CANDIDATE** — passes gate but needs validation (enters inbox)
- **PROMOTE** — passes gate with sufficient rigor (goes to memory directly, rare)

## State Machine

```
┌───────────────┐
│   OBSERVED    │  Raw input received
└───────┬───────┘
        ↓
┌───────────────┐
│  INTERPRETED  │  JARVIS has processed the input
└───────┬───────┘
        ↓
┌───────────────┐
│   CANDIDATE   │  In inbox, awaiting validation
└───────┬───────┘
        ↓
┌───────────────┐
│   VERIFIED    │  Validated against evidence
└───────┬───────┘
        ↓
┌───────────────┐
│    ACTIVE     │  Approved for operational use
└───────┬───────┘
        ↓
┌───────────────┐
│   SUPERSEDED  │  Replaced by newer information
└───────────────┘
```

### Rejection Branches

```
INTERPRETED → REJECTED    (input was invalid/unsafe)
CANDIDATE   → REJECTED    (validation failed)
VERIFIED    → DEPRECATED  (no longer relevant)
```

### Promotion Rules

1. **OBSERVED → INTERPRETED**: Automatic (JARVIS processes input)
2. **INTERPRETED → CANDIDATE**: Passes gate → enters inbox
3. **CANDIDATE → VERIFIED**: Requires evidence or user confirmation
4. **VERIFIED → ACTIVE**: Requires approval (explicit or implicit)
5. **ACTIVE → SUPERSEDED**: When newer information replaces this

## Metadata Fields

### Epistemic (is this correct?)

```yaml
confidence: 0.0 to 1.0    # how likely is this information correct?
source: user | project-file | official-documentation | web | github | council | inference | experiment | system
```

**Critical:** Confidence is NOT authority. A user can be wrong (confidence: 0.7) but still have authority.

### Authority (may this control behavior?)

```yaml
authority: user-explicit | user-implicit | external-information | inference | system | project-observation
approval: explicit | implicit | none
scope: project-name | domain | system-wide
```

### Provenance (where did it come from?)

```yaml
provenance:
  type: github | conversation | inference | observation | council | tool | automation
  
  # For GitHub sources:
  repository: owner/repo
  ref: main
  commit: abc123
  path: docs/architecture.md
  retrieved: 2026-09-10
  
  # For conversation sources:
  session_id: ...
  message_id: ...
  
  # For inference sources:
  based_on:
    - MEM-001
    - OBS-004
    - DEC-002
    
  # For observation sources:
  inspected: file | code | config | environment
  timestamp: 2026-09-10T14:30:00Z
```

### Actor (who made this change?)

```yaml
actor: user | jarvis | tool | system | council | external | automation
```

### Temporal (when is this valid?)

```yaml
valid_from: 2026-09-01
valid_until: 2026-09-10   # null = still valid
```

### Lifecycle

```yaml
status: observed | interpreted | candidate | verified | active | superseded | deprecated | rejected | unknown
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
| `project-observation` | Direct inspection of project state | Schema inspection, code review |

## Approval Values

| Approval | Meaning |
|----------|---------|
| `explicit` | User confirmed this is correct and actionable |
| `implicit` | User hasn't objected, context implies approval |
| `none` | Not approved for action — information only |

## Confidence Guidelines

| Confidence | Meaning | Example |
|------------|---------|---------|
| 1.0 | Verified fact | Direct inspection, explicit user statement |
| 0.9 | Strong evidence | Multiple corroborating sources |
| 0.7-0.8 | Reasonable inference | User statement without verification |
| 0.5-0.6 | Uncertain | Partial evidence, conflicting signals |
| 0.0-0.4 | Low confidence | Speculation, weak inference |

**Never conflate confidence with authority.** A confident statement without authority cannot control behavior.