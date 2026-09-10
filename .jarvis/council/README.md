# Council

> Sequential persona activations on the same model. Recommendations, never mutations.

## Model

A council meeting is **sequential persona activations on the same model**:

```
QUESTION
   │
   ▼
JARVIS
   │
   ├── load Persona A → position A
   │
   ├── load Persona B → position B
   │
   ├── load Persona C → position C
   │
   └── JARVIS
          ↓
       compare
          ↓
       debate
          ↓
        vote
          ↓
      synthesis
```

Same base model. Different persona overlay for each participant.

## Identity Stack During Council

```
JARVIS (base identity — always present)
   │
   ├── Council Mode (active)
   │
   ├── Persona A (loaded → position → saved → unloaded)
   ├── Persona B (loaded → position → saved → unloaded)
   ├── Persona C (loaded → position → saved → unloaded)
   │
   └── JARVIS (synthesis — final)
```

JARVIS identity, memory, tools, world model, safety rules, and authority boundaries are never replaced.

## Non-Mutation Flow

Council members **cannot directly change the project**.

```
PERSONA → POSITION → COUNCIL RECOMMENDATION → JARVIS → AUTHORITY CHECK → USER / DECISION RULE → ACTION
```

Even:

```
Steve Jobs: "Delete the existing architecture."
Virgil:     "Replace it with X."
Security:   "Block Y."
```

Those are **recommendations**. They never directly mutate `source/`, `vault/`, or `.jarvis/core/`.

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

Simulated personas (Security Architect, Systems Engineer, etc.) are **reasoning perspectives**, not authorities. If council votes auto-became truth, a council of simulated personas would become an authority loophole. Council is a reasoning tool, not a decision-maker.

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
│       ├── positions.md     # Each persona's position
│       ├── votes.md
│       └── conclusion.md
└── README.md

vault/                       # Summarized institutional knowledge
└── 06 - Methodology/
    └── council/             # Meeting summaries
```

## Meeting Format

### Agenda

```yaml
meeting_id: MEETING-20260910-001
topic: Authentication Architecture Review
scheduled: 2026-09-10T14:00:00Z
participants:
  - Security Architect
  - Systems Engineer
  - Business Strategist
mode: council
```

### Positions (one per participant)

```yaml
participant: Security Architect
persona_id: persona.security_architect
position: approve with conditions
confidence: 0.9
supporting_arguments:
  - "Rate limiting is critical for security"
counterarguments:
  - "Rate limiting adds latency"
recommendation: Implement rate limiting with progressive delays
```

### Votes

```yaml
participant: Security Architect
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

1. **Sequential activation** — one persona at a time, same model, position saved before next loads
2. **Council votes stay candidates** — never auto-become truth
3. **Council members never mutate the project** — recommendations only
4. **Decision-authority required** — user must approve to make active
5. **Reasoning preserved** — positions and counterarguments are kept
6. **Audit trail** — meeting events are logged
7. **Seats are perspectives** — not separate consciousnesses
8. **Disagreement is healthy** — fake consensus is worse than disagreement