# Inbox

> Quarantine layer. Everything lands here first.

## Purpose

Prevent premature commitment. User statements, inferences, observations — all start as candidates. Only after validation and approval do they get promoted to persistent memory.

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
└───────────────┘
```

### Rejection Branches

```
INTERPRETED → REJECTED    (input was invalid/unsafe)
CANDIDATE   → REJECTED    (validation failed)
VERIFIED    → DEPRECATED  (no longer relevant)
```

## Flow

```
INPUT → INBOX → CLASSIFY → VALIDATE → PROMOTE → MEMORY
```

### Step 1: Input Received

Raw input enters the system:

```yaml
event_id: EVT-20260910-001
timestamp: 2026-09-10T14:30:00Z
actor: jarvis
action: memory.create
target: MEM-20260910-001
from_status: null
to_status: observed
reason: user_input_received
provenance:
  type: conversation
  session_id: ...
  message_id: ...
```

### Step 2: Classification

When an item enters the inbox, classify:

1. **Type:** What kind of memory is this? (project, knowledge, episodic, working)
2. **Authority:** Who can act on it? (user-explicit, external-information, inference, etc.)
3. **Approval:** Is this approved for action? (explicit, implicit, none)
4. **Scope:** What domain does it apply to?
5. **Confidence:** How reliable is this information?

```yaml
# Example classification
id: MEM-20260910-001
type: project-decision
status: candidate

# Epistemic
source: user
confidence: 0.7  # user said "I think" — not committed

# Authority
authority: user-explicit
approval: none   # not yet confirmed
scope: 11:11 Division

# Provenance
provenance:
  type: conversation
  session_id: ...
  message_id: ...

# Actor
actor: user
```

### Step 3: Validation

Before promotion, verify:

1. Is this confirmed by the user or by evidence?
2. Does this conflict with existing memory?
3. Is the authority sufficient for the intended action?
4. Is the scope correct?

### Step 4: Promotion

After validation, promote to the appropriate memory class:

- **working/** — temporary, disposable
- **episodic/** — what happened (history, not truth)
- **project/** — validated project state (high confidence)
- **knowledge/** — general reusable knowledge

```yaml
# Promotion event
event_id: EVT-20260910-002
timestamp: 2026-09-10T14:35:00Z
actor: jarvis
action: memory.promote
target: MEM-20260910-001
from_status: candidate
to_status: active
reason: explicit_user_confirmation
provenance:
  type: conversation
  session_id: ...
  message_id: ...
```

### Step 5: Rejection

If validation fails:

```yaml
# Rejection event
event_id: EVT-20260910-003
timestamp: 2026-09-10T14:36:00Z
actor: jarvis
action: memory.reject
target: MEM-20260910-001
from_status: candidate
to_status: rejected
reason: contradicts_verified_fact_MEM-20260910-050
provenance:
  type: inference
  based_on:
    - MEM-20260910-050
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

## Confidence Guidelines

| Confidence | Meaning | Example |
|------------|---------|---------|
| 1.0 | Verified fact | Direct inspection, explicit user statement |
| 0.9 | Strong evidence | Multiple corroborating sources |
| 0.7-0.8 | Reasonable inference | User statement without verification |
| 0.5-0.6 | Uncertain | Partial evidence, conflicting signals |
| 0.0-0.4 | Low confidence | Speculation, weak inference |

**Never conflate confidence with authority.** A confident statement without authority cannot control behavior.

## Example

User says: "I think we should abandon the current architecture."

This enters inbox as:

```yaml
---
id: MEM-20260910-001
type: project-decision
status: candidate

# Epistemic
source: user
confidence: 0.7  # user said "I think" — not committed

# Authority
authority: user-explicit
approval: none   # not yet confirmed
scope: 11:11 Division

# Provenance
provenance:
  type: conversation
  session_id: ...
  message_id: ...

# Actor
actor: user

# Lifecycle
created: 2026-09-10
updated: 2026-09-10
supersedes: null
related: []
---
```

Only when the user commits does it become:

```yaml
status: active
approval: explicit
confidence: 1.0
```
