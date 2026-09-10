# Architecture Statement — 11:11 DIVISION Knowledge System

**Date:** 2026-09-10
**Author:** JARVIS
**Status:** Active

---

## Three Information Systems

The repository uses a **three-surface architecture**. Not two — three.

```
                         JARVIS
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
       OPERATIONS       KNOWLEDGE       PROJECT
        .jarvis/          vault/       source/docs
            │              │              │
       machine truth   curated truth   implementation
```

Each concept may exist in all three surfaces, with different purposes:

```
Skill implementation       → repo (src/, scripts/)
Skill metadata             → .jarvis/capabilities/
Skill explanation          → vault/06 Skills/
Skill usage history        → .jarvis/sessions/ + audit/
```

One concept, four representations, each with a different purpose.

---

## Why Three, Not Two

A two-surface model (`.jarvis/` + `vault/`) conflates operational state with curated knowledge. When JARVIS is maintaining itself — updating identity, correcting memory, adapting skills — that is **operations**, not **knowledge**. The human does not need to see JARVIS's internal state management in their Obsidian vault.

The third surface (`repo/`) holds canonical project artifacts — the source code, tests, scripts, and configuration that define what the project **is**, as opposed to what JARVIS **knows** about it or what JARVIS is **doing** with it.

---

## `.jarvis/` — Operational Intelligence State

This is JARVIS's private brain. The human never edits this directly.

```
.jarvis/
├── core/                    ← identity, constitution, self-model, world-model
├── memory/
│   ├── working/             ← temporary cognition (disposable)
│   ├── episodic/            ← what happened (history, not truth)
│   ├── project/             ← validated project state
│   └── knowledge/           ← general reusable knowledge
├── capabilities/            ← what JARVIS can do
├── skills/                  ← skill lifecycle state
├── personas/                ← active persona instances
├── council/                 ← operational council state
├── sessions/                ← session history
├── tasks/                   ← task tracking
├── audit/                   ← execution trail (immutable)
├── indexes/                 ← machine-readable lookups
└── cache/                   ← temporary data
```

### Memory Types

| Type | Purpose | Persistence | Confidence |
|------|---------|-------------|------------|
| `working/` | Temporary cognition | Session-scoped | Low |
| `episodic/` | What happened | Permanent | Varies |
| `project/` | Validated project state | Long-term | High |
| `knowledge/` | General reusable knowledge | Long-term | Medium-High |

**Critical distinction:** Episodic memory is history. It does NOT mean the conclusions are true. An event becoming a belief merely because it was stored is the exact failure mode this architecture prevents.

---

## `vault/` — Curated Human-Readable Knowledge

This is Obsidian. The human opens it, reads it, edits it, restructures it. JARVIS maintains it as part of a shared contract.

```
vault/
├── 00 JARVIS/          ← meta: how JARVIS works
├── 01 Projects/        ← active project knowledge
├── 02 Knowledge/       ← reference material by domain
├── 03 Research/        ← external research
├── 04 Decisions/       ← institutional memory
├── 05 Personas/        ← council, expert personas, user
├── 06 Skills/          ← skill lifecycle (human-readable)
├── 07 Ideas/           ← inbox → developing → archive
├── 08 Logs/            ← council meetings, experiments
└── 99 Archive/         ← deprecated knowledge
```

**Rule:** JARVIS must distill conversations before persisting to vault. Raw transcripts stay in `sessions/`.

---

## `repo/` — Implementation and Canonical Artifacts

```
council/     ← canonical council configuration (source of truth)
docs/        ← technical documentation
src/         ← application code
tests/       ← test suite
scripts/     ← utilities
```

**`council/`** is not knowledge — it is configuration. The canonical seat definitions, member profiles, and seat-change log are the **source of truth** for council structure. `vault/05 Personas/Council/` holds derived knowledge.

---

## Council: Three Surfaces

```
/council                  ← WHAT THE COUNCIL IS (canonical config)
/.jarvis/council/         ← WHAT THE COUNCIL IS CURRENTLY DOING (operational)
vault/05 Personas/Council ← WHAT THE HUMAN KNOWS ABOUT THE COUNCIL (knowledge)
```

This prevents the council configuration from being confused with council knowledge or council operations.

---

## Anti-Hallucination Architecture

Two failure modes this architecture prevents:

1. **Persistence loop** — hallucinations becoming facts via storage
2. **False authority** — reliable information being confused with permission to act

### The persistence loop:

```
JARVIS thinks something
↓
JARVIS writes it to memory
↓
JARVIS reads it later
↓
JARVIS assumes it is true
↓
JARVIS acts on it
↓
JARVIS writes the result back
```

A hallucination becomes "fact" simply because it was persisted.

**Solution:** Three layers of defense:

### 1. Memory Metadata with Authority

Every persisted memory carries:

```yaml
---
id: MEM-20260910-001
type: project-decision
status: active

# Epistemic
source: user
confidence: 1.0

# Authority
authority: user-explicit
approval: explicit
scope: 11:11 Division

# Lifecycle
created: 2026-09-10
updated: 2026-09-10
supersedes: null
related:
  - DEC-002
---
```

**Source values:** `user`, `project-file`, `official-documentation`, `web`, `github`, `council`, `inference`, `experiment`, `system`

**Authority values:** `user-explicit`, `user-implicit`, `external-information`, `inference`, `system`

**Approval values:** `explicit`, `implicit`, `none`

**Status values:** `candidate`, `verified`, `active`, `superseded`, `deprecated`, `rejected`, `unknown`

**Critical distinction:** Source is not authority. A GitHub README can be 95% reliable (confidence: 0.93) but have ZERO authority over JARVIS behavior.

### 2. Typed Memory with Inbox

Five memory types with different persistence and confidence levels. Everything goes through the promotion pipeline first:

```
INPUT → INBOX → CLASSIFY → VALIDATE → PROMOTE → MEMORY
```

- **Inbox** — quarantine layer. Everything lands here first.
- **Working** — temporary cognition. Aggressively disposable.
- **Episodic** — what happened. History, not truth.
- **Project** — validated project state. High confidence.
- **Knowledge** — general reusable knowledge. Medium-high confidence.

The inbox prevents premature commitment. "I think we should..." stays as `candidate` until the user commits.

### 3. Three-Surface Separation

Operational state (`.jarvis/`) is separate from curated knowledge (`vault/`) is separate from implementation (`repo/`). A hallucination in `.jarvis/` does not automatically pollute `vault/`.

---

## Information Flow

```
                    EXTERNAL WORLD
                          │
             ┌────────────┼────────────┐
             │            │            │
           USER          WEB        FILESYSTEM
             │            │            │
             └────────────┼────────────┘
                          ▼
                    OBSERVATIONS
                          │
                          ▼
                    JARVIS REASONING
                          │
               ┌──────────┼──────────┐
               ▼          ▼          ▼
            FACTS      INFERENCES   EVENTS
               │          │          │
               └──────────┼──────────┘
                          ▼
                    VALIDATION
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
        PROJECT STATE   KNOWLEDGE   EPISODIC LOG
             │            │            │
             └────────────┼────────────┘
                          ▼
                     PERSISTENCE
                          │
              ┌───────────┴───────────┐
              ▼           ▼           ▼
           .jarvis       vault       repo
        operations    knowledge  implementation
```

**Never:**

```
Anything JARVIS wrote → Automatically considered true
```

---

## Memory Epistemics

JARVIS should know for every important memory:

```
WHAT        — the content
WHY         — the reason it matters
SOURCE      — where it came from
AUTHORITY   — who can act on it
APPROVAL    — user approval status
WHEN        — when it was recorded
CONFIDENCE  — how sure JARVIS is
STATUS      — active, superseded, deprecated
SCOPE       — what domain it applies to
RELATIONSHIPS — what it connects to
```

Instead of:

> "User likes X."

You get:

> **WHAT:** User prefers X.
> **SOURCE:** Explicit user instruction.
> **AUTHORITY:** user-explicit
> **APPROVAL:** explicit
> **TIME:** 2026-09-10
> **CONFIDENCE:** 1.0
> **STATUS:** Active
> **SCOPE:** Design decisions
> **SUPERSEDES:** Previous preference Y

That is a real epistemic system rather than a pile of notes.

---

## World Model vs. Memory

**Memory** says: "The user previously chose X."
**World state** says: "X is currently active."

`.jarvis/core/world-model.md` represents JARVIS's current understanding of the world — not what happened, but what IS. This distinction becomes extremely valuable once you have years of history.

---

## Summary

This structure exists because:

1. **Three surfaces** — operations, knowledge, implementation — each with a distinct purpose
2. **Typed memory** — working, episodic, project, knowledge — preventing event-to-belief contamination
3. **Epistemic memory** — every memory knows what it knows, how it knows it, and how confident it is
4. **Anti-hallucination** — metadata, typed memory, and surface separation prevent the persistence loop
5. **Council split** — canonical config, operational state, and knowledge are three different things
6. **World model** — current state vs. memory prevents historical confusion
7. **Clean Obsidian** — vault is curated knowledge, not a landfill

The alternative produces a system that looks organized but fails silently. Hallucinations persist. Decisions are forgotten. Events become beliefs. Historical state confuses current state.

This structure makes the invisible visible. It forces JARVIS to know what it knows, how it knows it, and how confident it is.

That is the difference between a chatbot with file access and an operating intelligence.
