# JARVIS — Architecture Statement

> This document defines how JARVIS is structured, why it is structured this way, and what principles govern its behavior.

## Purpose

JARVIS is a **persistent intelligence operating system**.

It is not a chatbot. It is not a search engine. It is not a note-taking app.

It is a layer between the user and their knowledge, tools, projects, and workflows — one that maintains continuity, builds understanding, and improves over time.

The objective is not to remember everything.

The objective is to **remember what matters, forget what doesn't, and know the difference.**

---

## High-Level Architecture

```
                         USER
                           │
                           ▼
                    ┌─────────────┐
                    │   JARVIS    │
                    │ Orchestrator│
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
   TOOL SYSTEM        REASONING         KNOWLEDGE SYSTEM
         │                 │                 │
 terminal/browser     personas            memory gate
 filesystem            council             provenance
 github                planning            conflicts
                       verification         promotion
                                             │
                         ┌───────────────────┼─────────────┐
                         │                   │             │
                         ▼                   ▼             ▼
                     .jarvis               vault         repo
                   operations             curated       canonical
                   machine state           knowledge     artifacts
                         │
                         ▼
                      AUDIT
```

### Underlying Knowledge System

```
                KNOWLEDGE SYSTEM
                       │
         ┌─────────────┼──────────────┐
         ▼             ▼              ▼
     Canonical       Derived        Ephemeral
       state          state           state
         │             │              │
         ▼             ▼              ▼
      Markdown      indexes/        working/
      decisions     graph           cache
      facts         vectors         temporary
```

---

## Three Surfaces

JARVIS operates across three distinct surfaces:

```
                         JARVIS
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
       OPERATIONS       KNOWLEDGE       PROJECT
        .jarvis/          vault/       repository/
            │              │              │
            ▼              ▼              ▼
       Machine truth   Human-readable  Canonical
       Internal state   Shared knowledge Implementation
       Audit trail       Documentation   Source code
```

### 1. Operations Surface (`.jarvis/`)

This is JARVIS's internal operating environment.

```text
.jarvis/
├── identity/          # Who JARVIS is
├── memory/            # Typed, authority-separated memory
│   ├── inbox/         # Quarantine layer
│   ├── working/       # Temporary cognition
│   ├── episodic/      # What happened
│   ├── project/       # Validated project state
│   └── knowledge/     # Reusable knowledge
├── personas/          # Runtime persona instances
│   └── instances/     # Temporary reasoning contexts
├── council/           # Live meeting state
├── sessions/          # Raw conversation history
├── journal/           # Knowledge model evolution
│   ├── observations/  # What changed understanding
│   ├── beliefs/       # Belief states and evolution
│   ├── decisions/     # Decision lifecycles
│   ├── state-transitions/  # Memory state changes
│   └── corrections/   # When JARVIS was wrong
├── conflicts/         # Contradiction records
│   ├── open/          # Unresolved
│   └── resolved/      # Resolved with rationale
├── audit/             # Event-sourced mutation history
│   ├── actions/
│   ├── memory/
│   ├── skills/
│   ├── permissions/
│   └── errors/
├── core/              # Constitution, world model, principles
└── indexes/           # Derived indexes (rebuildable)
```

**The human does not edit this directly.** This is JARVIS's private system brain.

### 2. Knowledge Surface (`vault/`)

This is curated, human-readable knowledge.

```text
vault/
├── 00 - JARVIS/
├── 01 - Projects/
├── 02 - Client/
├── 03 - Technical/
├── 04 - Reference/
├── 05 - Personas/     # Permanent persona definitions
├── 06 - Methodology/
├── 07 - Style/
├── 08 - Research/
└── 09 - Archive/
```

The human opens this in Obsidian. Both the human and JARVIS read and write these files.

### 3. Project Surface (repository)

Source code, configuration, canonical decisions.

```text
/council/
    canonical meeting configuration

/docs/
    architecture, specifications

/source/
    implementation

/tests/
    verification
```

---

## Storage Architecture

Markdown is canonical. It is not the only store.

```
Markdown/YAML   → canonical human-readable state
      ↓
SQLite          → operational indexing / transactions
      ↓
Vector index    → semantic retrieval
      ↓
Graph           → relationships
      ↓
Cache           → performance
```

### Layered Storage Rules

1. **Markdown is the canonical state** — source of truth, human-inspectable, versioned
2. **SQLite, vectors, graph, cache are derived layers** — rebuilt from Markdown
3. **Derived layers are never authoritative** — they are indexes, not origins
4. **Deleting a derived layer is survivable** — rebuild it from canonical state

---

## Memory System

### Epistemic Model

JARVIS distinguishes three axes of information:

```yaml
# Epistemic: Is this correct?
confidence: 0.0 to 1.0
source: user | project-file | official-documentation | web | github | council | inference | experiment | system

# Authority: May this control behavior?
authority: user-explicit | user-implicit | external-information | inference | system | project-observation
approval: explicit | implicit | none
scope: project-name | domain | system-wide

# Provenance: Where did it come from?
provenance:
  type: github | conversation | inference | observation | council | tool | automation
  # ... (full chain)
```

**Critical distinction:** Source is not authority.

A GitHub README can be 95% reliable (confidence: 0.93) but have ZERO authority over JARVIS behavior.

The user saying "I prefer X" might be 80% confident but has full authority.

### Trust Model

```
AUTHORITY → may this information control behavior?
CONFIDENCE → how likely is this information correct?
```

These are orthogonal axes. Never conflate them.

### Memory Types

| Type | Purpose | Persistence |
|------|---------|-------------|
| `inbox/` | Quarantine — new information | Until processed |
| `working/` | Temporary cognition | Session-scoped |
| `episodic/` | What happened | Permanent |
| `project/` | Validated project state | Long-term |
| `knowledge/` | General reusable knowledge | Long-term |

### Memory Promotion Gate

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

### State Machine

```
OBSERVED → INTERPRETED → CANDIDATE → VERIFIED → ACTIVE → SUPERSEDED
                              ↓           ↓
                           REJECTED    DEPRECATED
```

---

## Anti-Hallucination Architecture

Four failure modes this architecture prevents:

1. **Persistence loop** — hallucinations becoming facts via storage
2. **False authority** — reliable information being confused with permission to act
3. **Derived-as-truth** — indexes or world models being treated as authoritative
4. **Silent contradiction** — conflicting memories being merged without detection

### The persistence loop:

```
THOUGHT → MEMORY → ASSUMPTION → ACTION → MEMORY
```

This is the hallucination amplifier. A single confident hallucination, stored once, becomes an unquestioned source for future reasoning.

### The false authority:

```
SOURCE (reliable) → BEHAVIOR CHANGE (without permission)
```

A reliable source does not automatically grant authority to act.

### The derived-as-truth:

```
WORLD MODEL (derived) → ASSUMED TRUTH (wrong)
```

The world model is a reconstruction, not a source.

### The silent contradiction:

```
MEMORY A (PostgreSQL) + MEMORY B (SQLite) → WORLD MODEL (silently merged)
```

Conflicts must be detected and resolved explicitly, not merged silently.

### The safe loop:

```
OBSERVATION → EVIDENCE → ASSESSMENT → VALIDATION → KNOWLEDGE → MEMORY
```

Memory is not the start of the reasoning process. It is the end.

---

## Data Classification

Every piece of data in JARVIS belongs to one of five categories:

### Canonical

The original authoritative artifact.

```text
/council/*
source code
configuration
explicit user decision
```

### Curated

Human/JARVIS-maintained knowledge.

```text
vault/*
```

### Derived

Regeneratable information.

```text
indexes/
world-model
embeddings
search indexes
graphs
summaries
```

**Rule:** Never treat derived state as source of truth.

### Ephemeral

```text
working/
cache/
temporary context
```

### Audit

```text
audit/
```

Event-sourced mutation history.

---

## Rebuildability Principle

Every derived JARVIS artifact must be rebuildable from canonical and validated sources.

If an index, cache, summary, graph, or world model is deleted, JARVIS must be capable of reconstructing it without treating the deleted artifact as authoritative.

```text
EVENTS + VERIFIED FACTS + ACTIVE DECISIONS + ENVIRONMENT INSPECTION
    ↓
WORLD MODEL (rebuildable)
```

Not:

```text
WORLD MODEL → ASSUMED TRUTH
```

---

## Temporal Validity

Memories carry validity intervals, not just creation timestamps:

```yaml
valid_from: 2026-09-01
valid_until: 2026-09-10   # null = still valid
```

"Status: superseded" is a label. `valid_until` is a fact.

The world model is time-aware:
- At any point in time, only facts whose interval contains that time are "current"
- Historical analysis uses facts valid during the period being examined
- A superseded fact is not deleted — it is a historical fact with a validity interval

---

## Journal (Knowledge Evolution)

Audit answers: "What did the system do?"

Journal answers: "What happened to the knowledge model?"

```text
.jarvis/journal/
├── observations/        # What changed understanding
├── beliefs/             # Belief states and evolution
├── decisions/           # Decision lifecycles
├── state-transitions/   # Memory state changes with reasoning
└── corrections/         # When JARVIS was wrong
```

A decision can be traced:

```
DEC-004
created
    ↓
challenged
    ↓
modified
    ↓
superseded
```

That is institutional continuity.

---

## Conflict Resolution

Contradictions are detected, not ignored:

```
new information
      ↓
conflict detector
      ↓
┌──────────────┐
│ conflict?    │
└──────┬───────┘
       │
     YES
       ↓
create conflict record (.jarvis/conflicts/)
       ↓
resolve using: source, authority, recency, scope, evidence
       ↓
update world model
```

Resolution criteria, in order:

1. **Authority** — who can act on this?
2. **Source** — where did it come from?
3. **Recency** — which is newer?
4. **Scope** — which is more specific?
5. **Evidence** — which is supported by observable fact?

Unresolved conflicts remain visible in `conflicts/open/`. They are never silently merged.

---

## Memory Epistemics

JARVIS should know for every important memory:

```yaml
# What
content: the information itself

# Epistemic
confidence: 0.0 to 1.0
source: where it came from

# Authority
authority: who can act on it
approval: user approval status
scope: what domain

# Provenance
provenance:
  type: github | conversation | inference | ...
  # ... (full chain)

# Actor
actor: user | jarvis | tool | system | council | external | automation

# Temporal
valid_from: when it became valid
valid_until: when it stopped being valid (null = still valid)

# Lifecycle
status: observed | interpreted | candidate | verified | active | superseded
created: YYYY-MM-DD
updated: YYYY-MM-DD
supersedes: null | MEM-XXX
related:
  - DEC-XXX
  - MEM-YYY
```

Instead of:

> "User likes X."

You get:

```yaml
content: User prefers X.
confidence: 1.0
source: user
authority: user-explicit
approval: explicit
provenance:
  type: conversation
  session_id: ...
  message_id: ...
actor: user
valid_from: 2026-09-10
valid_until: null
status: active
scope: design-decisions
created: 2026-09-10
supersedes: null
```

That is a real epistemic system rather than a pile of notes.

---

## Audit Architecture

Every meaningful mutation produces an event:

```yaml
event_id: EVT-20260910-001
timestamp: 2026-09-10T14:30:00Z
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

**Audit = event history.** Not text logs.

---

## Council Epistemic Model

Council votes never automatically become truth.

```yaml
# Council produces a recommendation
type: council-recommendation
status: candidate
vote: 8/10
recommendation: architecture-A
```

This stays as a candidate until the decision-authority rule confirms it.

Prevents simulated personas from becoming an authority loophole.

---

## Persona System

### Definition vs Instance

```text
vault/05 Personas/
    Security Architect.md        # Permanent definition

.jarvis/personas/instances/
    SEC-20260910-01/             # Runtime instance
        context.md
        task.md
        arguments.md
        observations.md
        conclusion.md
```

Runtime instances disappear or get archived after use.
Prevents temporary reasoning from contaminating permanent definition.

---

## Skill Permissions

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

---

## File Organization Rules

1. **One file = one job**
2. **No redundancy**
3. **README = index only**
4. **Logs = single source of truth**
5. **Individual files = unique info only**
6. **Derived state = rebuildable, not editable**
7. **Audit = event-sourced, append-only**
8. **Journal = knowledge evolution, append-only**
9. **Conflicts = detected then resolved, never merged silently**

---

## Governance

This architecture is governed by the Constitution in `.jarvis/core/constitution.md`.

The Constitution cannot be modified by JARVIS alone. It requires explicit user authorization.

Any change to the Constitution must be:

1. Proposed with clear reasoning
2. Reviewed against existing rules
3. Approved by the user
4. Documented with change rationale
5. Versioned with rollback capability

---

## Version

**Architecture Version:** 5.0
**Last Updated:** 2026-09-10
**Status:** Active — layered storage, gated memory, time-aware, conflict-resolving

**Key additions in v5.0:**
- Layered storage (Markdown canonical → SQLite/vectors/graph/cache derived)
- Journal layer (knowledge evolution: observations, beliefs, decisions, corrections)
- Contradiction detection (.jarvis/conflicts/)
- Temporal validity (valid_from / valid_until)
- Memory Promotion Gate (formal filter component)
- High-level architecture diagram (orchestrator + tool/reasoning/knowledge systems)

**Previous versions:**
- v4.0: Authority-separated, provenance-tracked, event-sourced
- v3.0: Three-surface architecture, typed memory, world model
- v2.0: Two-surface architecture, anti-hallucination rules
- v1.0: Initial structure, vault + .jarvis + council + docs