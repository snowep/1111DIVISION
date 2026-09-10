# Council

> Votes stay candidates. Never auto-become truth.

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

### Safe flow

```
Council vote: 8/10 → architecture A
    ↓
type: council-recommendation
status: candidate
    ↓
User reviews recommendation
    ↓
User approves: "Yes, use architecture A"
    ↓
type: decision
status: active
authority: user-explicit
```

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
2. **Decision-authority required** — user must approve to make active
3. **Reasoning preserved** — arguments and counterarguments are kept
4. **Audit trail** — meeting events are logged
5. **Seats are perspectives** — not separate consciousnesses
6. **Disagreement is healthy** — fake consensus is worse than disagreement
