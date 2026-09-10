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

# Lifecycle
created: 2026-09-10
updated: 2026-09-10
supersedes: null
---

## Three-Surface Architecture

Each concept may exist in three representations:
- Implementation → repo
- Metadata → .jarvis/
- Explanation → vault/
- Usage history → .jarvis/sessions/ + audit/

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
