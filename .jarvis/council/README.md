# Council

> Recommendations, never mutations. Votes stay candidates.

## Three Surfaces

```text
/council/                    # Canonical configuration
├── config.yaml              # Meeting settings
├── seats/                   # Seat definitions
│   ├── fixed/               # Permanent seats
│   ├── rotating/            # Topic-specific seats
│   └── reserved/            # Future expansion
└── decisions/               # Active decisions

.jarvis/council/             # Live meeting state
├── meetings/                # Current/recent meetings
│   └── MEETING-20260910-001/
│       ├── agenda.md
│       ├── participants.md
│       ├── arguments.md
│       ├── votes.md
│       └── conclusion.md
└── README.md

vault/                       # Summarized institutional knowledge
└── 06 - Methodology/
    └── council/             # Meeting summaries
```

## Non-Mutation Flow

Council members **cannot directly change the project**.

```
PERSONA
   ↓
ARGUMENT
   ↓
COUNCIL RECOMMENDATION
   ↓
JARVIS
   ↓
AUTHORITY CHECK
   ↓
USER / DECISION RULE
   ↓
ACTION
```

Even:

```
Steve Jobs: "Delete the existing architecture."
Virgil:     "Replace it with X."
Security:   "Block Y."
```

Those are **recommendations**. They never directly mutate:

```
source/
vault/
.jarvis/core/
```

## Epistemic Model

### Council produces recommendations, not truth

```yaml
# Council vote
type: council-recommendation
status: candidate
vote: 8/10
recommendation: architecture-A
```

**This stays as a candidate.** It does not automatically become active.

### Promotion requires decision-authority rule

```yaml
# Only when decision-authority confirms
type: decision
status: active
authority: user-explicit
approval: explicit
based_on: council-recommendation-MEETING-001
```

### Why this matters

Simulated personas (Security Architect, Systems Engineer, etc.) are **reasoning perspectives**, not authorities.

If council votes auto-became truth:

```
Council vote: 8/10 → architecture A
    ↓
status: active  ← WRONG
    ↓
JARVIS acts on this as truth
```

This is an authority loophole. The council is a reasoning tool, not a decision-maker.

## Council Members Are Agent Instances

Each council member is an **agent instance** with explicit boundaries:

```yaml
instance_id: AGT-MEET-20260910-001-SEC
persona_id: security-architect
parent: jarvis
task: review the proposed architecture
scope: security
independent_context: true
can_write_project: false
can_modify_memory: false
can_modify_constitution: false
can_execute_terminal: false
```

A council is a **coordinated collection of agent instances**.
Each works in isolation (context, evidence, reasoning, arguments), then votes. JARVIS synthesizes.

## Meeting Format

### Agenda

```yaml
meeting_id: MEETING-20260910-001
topic: Authentication Architecture Review
scheduled: 2026-09-10T14:00:00Z
seats:
  - Security Architect
  - Systems Engineer
  - Creative Director
  - User Advocate
mode: council
```

### Arguments

Each seat produces independent analysis:

```yaml
seat: Security Architect
arguments:
  - "Current auth lacks rate limiting"
  - "JWT tokens have no expiration"
counterarguments:
  - "Rate limiting adds latency"
  - "Short expiration hurts UX"
recommendation: Implement rate limiting with progressive delays
```

### Votes

```yaml
seat: Security Architect
vote: approve
confidence: 0.9
reasoning: "Rate limiting is critical for security"
```

### Conclusion

```yaml
meeting_id: MEETING-20260910-001
status: complete
vote_result: 8/10 approve rate limiting
recommendation: Implement rate limiting with progressive delays
type: council-recommendation
status: candidate  ← NOT active
```

## Rules

1. **Council votes stay candidates** — never auto-become truth
2. **Council members never mutate the project** — recommendations only
3. **Decision-authority required** — user must approve to make active
4. **Reasoning preserved** — arguments and counterarguments are kept
5. **Audit trail** — meeting events are logged
6. **Seats are perspectives** — not separate consciousnesses
7. **Disagreement is healthy** — fake consensus is worse than disagreement