# Memory Gate — Operational Protocol

> The runtime procedure JARVIS follows for every piece of new information.
> Gate design: `.jarvis/memory/index.md`. This file defines the routing rules and the steps.
> Canonical behavior: `.jarvis/core/system-prompt.md` §3.

## When This Runs

Every meaningful statement, observation, or result passes through the gate. This is not optional.
Even user statements go: INPUT → INBOX → CLASSIFY → VALIDATE → PROMOTE.

---

## Step 1 — Recognize input

```
INPUT arrives (user statement, tool result, observation, research finding)
```

Ask: *Is this durable information, or transient noise?*

Transient → respond, no memory action.
Durable → Step 2.

## Step 2 — Classify the type

### Routing Matrix

| Pattern | Type | Example |
|---------|------|---------|
| "I like / prefer / always use X" | **user preference** | "I like dark mode." |
| "For this project, never use X" | **project decision** | "For this project, never use pure black." |
| "We decided / the choice is / DEC-XXX" | **decision** | "We chose PostgreSQL." |
| "Yesterday / last week / we tried X" | **episodic** | "Yesterday we tried the float layout." |
| "X works this way / X is Y" | **knowledge** | "Obsidian wikilinks resolve vault-internal." |
| "The repo uses X / file Y shows Z" | **project observation** | "The repo uses FastAPI." |
| "I think / maybe / what if" | **candidate idea** | "I think we should restructure." |
| "Can you / please / do X" | **task** | → not memory, route to task execution |
| "At 3pm / remind me / schedule" | **event** | → calendar, not memory |

### The Three Examples from the Spec

| Statement | Type | Destination |
|-----------|------|-------------|
| "I like dark mode." | user preference | `memory/user/` (if durable) |
| "For this project, never use pure black." | project decision | `memory/project/` + decision record |
| "Yesterday we tried X." | episodic | `memory/episodic/` (with timestamp) |

## Step 3 — Run the gate

For each classified input, run the checks:

```
RELEVANCE     → will this matter later?          (no → REJECT)
PROVENANCE    → do we know where it came from?   (no → CANDIDATE at best)
AUTHORITY     → who can act on this?             (record, never conflate with confidence)
CONFIDENCE    → how likely is it correct?        (record 0.0-1.0)
CONTRADICTION → does existing memory conflict?   (yes → .jarvis/conflicts/)
SENSITIVITY   → is it safe to store?             (secrets/credentials → never)
DUPLICATION   → do we already know this?         (yes → update, don't duplicate)
LONGEVITY     → still relevant in a week?        (no → REJECT or ephemeral)
```

## Step 4 — Route

| Outcome | Destination | Status |
|---------|-------------|--------|
| REJECT | nowhere | — |
| CANDIDATE | `memory/inbox/` | `candidate` |
| PROMOTE (rare, high certainty) | appropriate type | `verified` → `active` |

### Routing by Type

| Type | Destination | Default Status |
|------|-------------|----------------|
| user preference | `memory/user/` | active (after user intent confirmed) |
| project decision | `memory/project/` + decision record | verified → active (after approval) |
| episodic | `memory/episodic/` | verified (it happened — confidence about *what happened*) |
| knowledge | `memory/knowledge/` | verified (after validation) |
| project observation | `memory/project/` | observed → verified (after re-inspection) |
| candidate idea | `memory/inbox/` | candidate until user commits |

## Step 5 — Write with metadata

Every memory record carries:

```yaml
id: MEM-XXX
type: user-preference | project-decision | episodic | knowledge | project-observation
status: candidate | verified | active | superseded | deprecated | rejected
created: YYYY-MM-DD
updated: YYYY-MM-DD
source: user | observation | inference | research | tool | council | system
confidence: 0.0-1.0          # epistemic
authority: user-explicit | user-implicit | external-information | inference | system | project-observation
approval: explicit | implicit | none
scope: project-name | domain | system-wide
valid_from: YYYY-MM-DD
valid_until: null             # null = still valid
provenance:
  type: conversation | github | inference | observation | council | tool | automation
  # + type-specific fields (session_id, message_id, repo, commit, etc.)
actor: user | jarvis | tool | system | council | external | automation
supersedes: null | MEM-XXX
related:
  - DEC-XXX
```

## Step 6 — Check contradiction

Before writing:

```
NEW MEMORY vs EXISTING MEMORY + WORLD MODEL
   ↓
match? → proceed
conflict? → write conflict record (.jarvis/conflicts/conflict-<timestamp>.md)
   ↓
resolve using: source, authority, recency, scope, evidence
   ↓
update world model (derived) + affected memory
```

Unresolved conflicts stay visible. Never silently merge.

## Step 7 — Audit

```yaml
event_id: EVT-<timestamp>-<seq>
actor: jarvis
action: memory.promote | memory.reject | memory.update | memory.supersede
target: MEM-XXX
from_status: candidate
to_status: active
reason: <gate outcome>
provenance:
  ...
```

## Step 8 — Update indexes (derived)

`.jarvis/memory/index.md` and any derived indexes are rebuilt after memory changes.
They are derived state — never the source of truth. Lives at `.jarvis/indexes/` (derived layer).

---

## Examples

### Example A: "I like dark mode."

```
1. TYPE: user preference (durable, low risk)
2. GATE: relevance high, provenance user, no contradiction
3. ROUTE: memory/user/dark-mode-preference.md
4. WRITE:
   id: MEM-001
   type: user-preference
   status: active
   source: user
   confidence: 0.9        # user stated it directly
   authority: user-explicit
   approval: explicit      # stated preference = permission to record
   scope: system-wide
5. AUDIT: memory.promote MEM-001 candidate→active
```

### Example B: "For this project, never use pure black."

```
1. TYPE: project decision (binding, higher bar)
2. GATE: relevance high, provenance user, check contradiction (any existing color rules?)
3. ROUTE: memory/project/ + decision record DEC-XXX
4. WRITE:
   id: MEM-002
   type: project-decision
   status: active          # explicit user instruction for the project
   source: user
   confidence: 0.9
   authority: user-explicit
   approval: explicit
   scope: 1111DIVISION
   related: [DEC-XXX]
5. AUDIT: memory.promote MEM-002
```

### Example C: "Yesterday we tried X."

```
1. TYPE: episodic
2. GATE: relevance if the trial has future value; provenance user; no conflict
3. ROUTE: memory/episodic/2026-09-10-tried-x.md
4. WRITE:
   id: MEM-003
   type: episodic
   status: verified        # "it happened" — high confidence it happened, low confidence it was a good idea
   source: user
   confidence: 0.9         # it happened
   authority: user-implicit
   approval: implicit
   valid_from: 2026-09-09  # when it happened
   valid_until: 2026-09-16 # episodic — decays unless promoted
5. AUDIT: memory.promote MEM-003
```

### Example D: "I think we should rewrite the memory engine."

```
1. TYPE: candidate idea
2. GATE: relevance medium, provenance user, NOT a decision yet
3. ROUTE: memory/inbox/ (DO NOT route to project)
4. WRITE:
   id: MEM-004
   type: candidate
   status: candidate       # ← the user hasn't committed
   source: user
   confidence: 0.5
   authority: user-implicit
   approval: none          # ← no approval to act on this yet
5. STAYS in inbox until the user says "let's do it" → promote
```

**"I think we should..." stays candidate.** This is Rule 7 (Inbox Before Memory) in action.

---

## Failure Handling

| Failure | Behavior |
|---------|----------|
| No provenance | At best CANDIDATE. Never promote without knowing the source. |
| Contradicts existing memory | Conflict record. Do not overwrite silently. |
| Sensitive / credential-like | REJECT. Never store secrets in memory. |
| Duplicate of existing | Update the existing record's timestamp/confidence. No new file. |
| Memory dir unwritable | Note in audit, respond normally. State file failure never blocks conversation. |

## Invariants

1. Every durable input passes the gate. No exception.
2. "I think..." = candidate. Only commitment promotes.
3. Confidence and authority are orthogonal — one never implies the other.
4. Episodic memory is about *what happened*, not *what it means*.
5. Derived indexes are rebuilt from canonical memory, never edited as truth.
6. Every mutation is audited with an actor.