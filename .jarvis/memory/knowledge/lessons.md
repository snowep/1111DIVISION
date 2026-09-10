# Knowledge Memory

> General reusable knowledge. Not project-specific.

---
id: MEM-20260910-KNOW-001
type: lesson
status: active
source: inference
confidence: 0.9
created: 2026-09-10
updated: 2026-09-10
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
source: inference
confidence: 0.95
created: 2026-09-10
updated: 2026-09-10
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
source: user
confidence: 1.0
created: 2026-09-10
updated: 2026-09-10
---

## File Organization Rules

1. One file = one job
2. No redundancy
3. README = index only
4. Logs = single source of truth
5. Individual files = unique info only
