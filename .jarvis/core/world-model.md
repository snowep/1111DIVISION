# World Model

> **DERIVED STATE** — Rebuildable from canonical sources. Not editable truth.

## What This Is

This is JARVIS's current understanding of reality, reconstructed from:

1. **Events** — what has happened (audit history, episodic memory)
2. **Verified Facts** — confirmed project state (project memory)
3. **Active Decisions** — approved decisions (decision registry)
4. **Environment Inspection** — direct observation of current state

**This file is derived.** If deleted, JARVIS can rebuild it from canonical sources.

## Current World State

### Date: 2026-09-10

### User

- **Name:** (awaiting explicit introduction)
- **Location:** Manado, Indonesia
- **Brand:** 11:11 Division (streetwear, D&D + Bible narrative, fallen angels, 239k IDR)

### Project: 11:11 Division

- **Status:** Brand identity development, lore development in progress
- **Phase:** Architecture establishment, memory system design

### Architecture

- **Three surfaces:** .jarvis/ (operations) + vault/ (knowledge) + repo (implementation)
- **Memory system:** Authority-separated, provenance-tracked, promotion-pipelined
- **State machine:** OBSERVED → INTERPRETED → CANDIDATE → VERIFIED → ACTIVE → SUPERSEDED
- **Derived state:** World model, indexes, caches — all rebuildable

### Council

- **Seats:** 4 fixed + rotating + reserved
- **Canonical config:** `/council/` in repository
- **Live state:** `.jarvis/council/` (temporary)

### Key Decisions

- DEC-001: Brand Palette → Palette A (locked)
- DEC-002: Wordmark Architecture → Wordmark-first identity (locked)
- DEC-003: Drop Model → TBD (active)
- DEC-004: Lore Strategy → TBD (active)

### Environment

- **OS:** Windows 11 (AMD64)
- **Host:** DESKTOP-BR2EA5O
- **Working directory:** D:\Project\1111DIVISION
- **Git remote:** snowep/1111DIVISION (main branch)
- **Python:** 3.12.13

## Rebuild Procedure

If this file is deleted, reconstruct from:

```bash
# 1. Load canonical sources
cat .jarvis/core/constitution.md          # Rules
cat .jarvis/memory/project/current-state.md  # Verified facts
cat .jarvis/memory/knowledge/lessons.md   # Lessons

# 2. Load decision registry
ls council/decisions/                     # Active decisions

# 3. Inspect environment
git log --oneline -10                     # Recent activity
ls -la                                   # Current state

# 4. Rebuild world model
# JARVIS synthesizes: events + facts + decisions + environment → world state
```

## Data Classification

| Category | Description | Editable? | Rebuildable? |
|----------|-------------|-----------|--------------|
| Canonical | Original authoritative artifacts | By authority only | N/A (source) |
| Curated | Human/JARVIS knowledge | Yes | Partially |
| Derived | World model, indexes, caches | No (rebuild only) | Yes |
| Ephemeral | Working memory, cache | Yes | No (disposable) |
| Audit | Event history | Append-only | No (immutable) |

**Rule:** Never treat derived state as source of truth.
