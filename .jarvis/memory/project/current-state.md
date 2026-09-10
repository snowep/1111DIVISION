# Project Memory

> Validated project state. Only verified facts.

---
id: MEM-20260910-PROJ-001
type: project-state
status: active

# Epistemic
source: user
confidence: 1.0

# Authority
authority: user-explicit
approval: explicit
scope: 11:11 Division

# Provenance
provenance:
  type: conversation
  session_id: current
  message_id: user-introduction

# Actor
actor: user

# Lifecycle
created: 2026-09-10
updated: 2026-09-10
supersedes: null
related:
  - DEC-001
  - DEC-002
  - DEC-003
  - DEC-004
---

## 11:11 Division — Current State

### Brand

- **Name:** 11:11 Division
- **Style:** streetwear
- **Narrative:** D&D + Bible narrative, fallen angels
- **Price:** 239k IDR
- **Location:** Manado

### Council

- **Seats:** 4 fixed + rotating + reserved
- **Status:** Established, ready for meetings

### Design System

- **Palette:** A (locked)
- **Typography:** Söhne (locked)
- **Wordmark:** "11:11 DIVISION" stacked (locked)

### Lore

- **Status:** Deferred
- **Note:** Full canon integration not yet

---

## Decisions

### Locked

- **DEC-001:** Brand Palette → Palette A
- **DEC-002:** Wordmark Architecture → Wordmark-first identity

### Active

- **DEC-003:** Drop Model → TBD
- **DEC-004:** Lore Strategy → TBD

---

## Architecture

### Three Surfaces

- **.jarvis/** — operational intelligence state (machine truth)
- **vault/** — curated human-readable knowledge
- **repository/** — implementation and canonical project artifacts

### Memory System

- **Authority-separated** — source ≠ authority
- **Provenance-tracked** — full evidence chains
- **Promotion-pipelined** — inbox → classify → validate → promote → memory
- **Event-sourced audit** — mutations as events

### Data Classification

- **Canonical** — original authoritative artifacts
- **Curated** — human/JARVIS knowledge
- **Derived** — rebuildable (world model, indexes, caches)
- **Ephemeral** — temporary working state
- **Audit** — event history

### Derived State Rule

World model, indexes, caches — all rebuildable from canonical sources.
Never treat derived state as source of truth.
