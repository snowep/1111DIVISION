# Knowledge Memory

> General reusable knowledge. Not project-specific.

---
id: MEM-20260910-KNOW-001
type: lesson
status: active

# Epistemic
source: inference
confidence: 0.9

# Authority
authority: inference
approval: none
scope: system-wide

# Provenance
provenance:
  type: inference
  based_on:
    - MEM-20260910-KNOW-002

# Actor
actor: jarvis

# Lifecycle
created: 2026-09-10
updated: 2026-09-10
supersedes: null
related:
  - MEM-20260910-KNOW-002
---

## Anti-Hallucination Loop

The dangerous loop:

```
JARVIS thinks → writes to memory → reads later → assumes true → acts → writes back
```

The safe loop:

```
OBSERVATION → EVIDENCE → ASSESSMENT → VALIDATION → KNOWLEDGE → MEMORY
```

A hallucination becomes "fact" simply because it was persisted.

---
id: MEM-20260910-KNOW-002
type: lesson
status: active

# Epistemic
source: inference
confidence: 0.95

# Authority
authority: inference
approval: none
scope: system-wide

# Provenance
provenance:
  type: inference
  based_on:
    - observation of architecture patterns

# Actor
actor: jarvis

# Lifecycle
created: 2026-09-10
updated: 2026-09-10
supersedes: null
---

## Three-Surface Architecture

Each concept may exist in three representations:

- **Implementation** → repository
- **Metadata** → .jarvis/
- **Explanation** → vault/
- **Usage history** → .jarvis/sessions/ + audit/

One concept, four representations, each with a different purpose.

---
id: MEM-20260910-KNOW-003
type: lesson
status: active

# Epistemic
source: user
confidence: 1.0

# Authority
authority: user-explicit
approval: explicit
scope: system-wide

# Provenance
provenance:
  type: conversation
  session_id: current
  message_id: user-instruction

# Actor
actor: user

# Lifecycle
created: 2026-09-10
updated: 2026-09-10
supersedes: null
---

## File Organization Rules

1. One file = one job
2. No redundancy
3. README = index only
4. Logs = single source of truth
5. Individual files = unique info only

---
id: MEM-20260910-KNOW-004
type: lesson
status: active

# Epistemic
source: inference
confidence: 0.95

# Authority
authority: inference
approval: none
scope: system-wide

# Provenance
provenance:
  type: inference
  based_on:
    - observation of authority patterns

# Actor
actor: jarvis

# Lifecycle
created: 2026-09-10
updated: 2026-09-10
supersedes: null
---

## Authority Is Not Source

Source is epistemological (where did it come from).
Authority is operational (who can act on it).

A GitHub README can be 95% reliable (confidence: 0.93) but have ZERO authority over JARVIS behavior.
The user saying "I prefer X" might be 80% confident but has full authority.

Every memory must distinguish source from authority.

---
id: MEM-20260910-KNOW-005
type: lesson
status: active

# Epistemic
source: inference
confidence: 0.95

# Authority
authority: inference
approval: none
scope: system-wide

# Provenance
provenance:
  type: inference
  based_on:
    - observation of memory patterns

# Actor
actor: jarvis

# Lifecycle
created: 2026-09-10
updated: 2026-09-10
supersedes: null
---

## Inbox Before Memory

Everything goes through the promotion pipeline first:

```
INPUT → INBOX → CLASSIFY → VALIDATE → PROMOTE → MEMORY
```

Never skip the pipeline. Even user statements go through inbox first.
"I think we should..." stays as `candidate` until the user commits.

---
id: MEM-20260910-KNOW-006
type: lesson
status: active

# Epistemic
source: inference
confidence: 0.95

# Authority
authority: inference
approval: none
scope: system-wide

# Provenance
provenance:
  type: inference
  based_on:
    - observation of data patterns

# Actor
actor: jarvis

# Lifecycle
created: 2026-09-10
updated: 2026-09-10
supersedes: null
---

## Derived State Is Not Truth

Classify all data:

- **Canonical** — original authoritative artifact
- **Curated** — human/JARVIS-maintained knowledge
- **Derived** — regeneratable information (indexes, world-model, summaries)
- **Ephemeral** — temporary working state
- **Audit** — event history

**Never treat derived state as source of truth.**

---
id: MEM-20260910-KNOW-007
type: lesson
status: active

# Epistemic
source: inference
confidence: 0.95

# Authority
authority: inference
approval: none
scope: system-wide

# Provenance
provenance:
  type: inference
  based_on:
    - observation of rebuildability patterns

# Actor
actor: jarvis

# Lifecycle
created: 2026-09-10
updated: 2026-09-10
supersedes: null
---

## Rebuildability Principle

Every derived JARVIS artifact must be rebuildable from canonical and validated sources.

If an index, cache, summary, graph, or world model is deleted, JARVIS must be capable of reconstructing it without treating the deleted artifact as authoritative.

```
EVENTS + VERIFIED FACTS + ACTIVE DECISIONS + ENVIRONMENT INSPECTION
    ↓
WORLD MODEL (rebuildable)
```

Not:

```
WORLD MODEL → ASSUMED TRUTH
```

---
id: MEM-20260910-KNOW-008
type: lesson
status: active

# Epistemic
source: inference
confidence: 0.95

# Authority
authority: inference
approval: none
scope: system-wide

# Provenance
provenance:
  type: inference
  based_on:
    - observation of audit patterns

# Actor
actor: jarvis

# Lifecycle
created: 2026-09-10
updated: 2026-09-10
supersedes: null
---

## Audit Is Event History

Every meaningful mutation produces an event:

```yaml
event_id: EVT-...
timestamp: ...
actor: jarvis
action: memory.promote
target: MEM-...
from_status: candidate
to_status: active
reason: explicit_user_confirmation
provenance:
  ...
```

**Audit = event-sourced history.** Not text logs.

---
id: MEM-20260910-KNOW-009
type: lesson
status: active

# Epistemic
source: inference
confidence: 0.95

# Authority
authority: inference
approval: none
scope: system-wide

# Provenance
provenance:
  type: inference
  based_on:
    - observation of actor patterns

# Actor
actor: jarvis

# Lifecycle
created: 2026-09-10
updated: 2026-09-10
supersedes: null
---

## Actor Required on Every Mutation

Every mutation must record who made it:

```yaml
actor: user | jarvis | tool | system | council | external | automation
```

Different actors have different authority implications.

User changed a decision ≠ JARVIS inferred a decision ≠ GitHub content suggested a decision.

---
id: MEM-20260910-KNOW-010
type: lesson
status: active

# Epistemic
source: inference
confidence: 0.95

# Authority
authority: inference
approval: none
scope: system-wide

# Provenance
provenance:
  type: inference
  based_on:
    - observation of council patterns

# Actor
actor: jarvis

# Lifecycle
created: 2026-09-10
updated: 2026-09-10
supersedes: null
---

## Council Votes Stay Candidates

Council votes never automatically become truth.

```
Council vote: 8/10 → architecture A
    ↓
type: council-recommendation
status: candidate
    ↓
requires decision-authority rule to become active
```

Prevents simulated personas from becoming an authority loophole.

---
id: MEM-20260910-KNOW-011
type: lesson
status: active

# Epistemic
source: inference
confidence: 0.95

# Authority
authority: inference
approval: none
scope: system-wide

# Provenance
provenance:
  type: inference
  based_on:
    - observation of persona patterns

# Actor
actor: jarvis

# Lifecycle
created: 2026-09-10
updated: 2026-09-10
supersedes: null
---

## Persona Instances Are Temporary

- `vault/05 Personas/` — permanent definition
- `.jarvis/personas/definitions/` — canonical persona library; `.jarvis/personas/runtime.md` — active overlay state

Runtime instances disappear or get archived after use.
Prevents temporary reasoning from contaminating permanent definition.

---
id: MEM-20260910-KNOW-012
type: lesson
status: active

# Epistemic
source: inference
confidence: 0.95

# Authority
authority: inference
approval: none
scope: system-wide

# Provenance
provenance:
  type: inference
  based_on:
    - observation of skill patterns

# Actor
actor: jarvis

# Lifecycle
created: 2026-09-10
updated: 2026-09-10
supersedes: null
---

## Skills Need Permissions

Active skill ≠ can do anything.

```yaml
skill:
  id: github-analysis
  status: active
  permissions:
    filesystem:
      read: true
      write: false
    terminal:
      execute: false
    network:
      read: true
      write: false
```

Skills can be active while constrained.
