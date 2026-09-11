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

Those are **recommendations**. They never directly mutate `src/`, `vault/`, or `.jarvis/core/`.

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
/council/                    # Canonical configuration (future)
└── decisions/               # Active decisions (see decisions.md)

.jarvis/council/             # Live meeting state
├── meeting-protocol.md      # 10-step operational procedure (v2, Phase 9)
├── meetings.md              # Completed + queued meetings
├── state.md                 # Operational state
├── decisions.md             # Council-derived decisions
├── templates/               # Meeting templates (v2)
│   ├── agenda.md            # Question, participants, meeting type, weights
│   ├── evidence.md          # Two-phase evidence registry
│   ├── positions.md         # Positions with evidence links + reversal conditions
│   ├── cross-examination.md # Structured conflict analysis
│   ├── votes.md             # Votes + agreement classification
│   └── conclusion.md        # Synthesis + confidence propagation + reversal tracker
└── README.md

vault/                       # Summarized institutional knowledge
└── 08 - Logs/Council Meetings/  # Meeting summaries
```

## Meeting Structure (v2, Phase 9)

Each meeting is a folder with six files:

```text
.jarvis/council/meetings/MEETING-YYYYMMDD-SEQ/
├── agenda.md              ← question, participants, meeting type, confidence weights
├── evidence.md            ← evidence registry (populated in Step 4)
├── positions.md           ← each persona's position (appended in Step 5)
├── cross-examination.md   ← conflict analysis (written in Step 6)
├── votes.md               ← votes + agreement classification (written in Step 7)
└── conclusion.md          ← synthesis + confidence + reversal conditions (Step 9)
```

### Agenda

```yaml
meeting_id: MEETING-20260911-001
status: in_progress
created: 2026-09-11
topic: Authentication Architecture Review
mode: council
meeting_type: risk-assessment
```

### Evidence Registry

```yaml
id: EVD-001
source: project-artifact
type: project-artifact
description: <what it says>
confidence: 0.95
verified: yes
```

Two-phase model: Phase 1 (JARVIS-collected, before any persona activates) + Phase 2 (persona-generated `council-vm`/`inference`, cited only by the registering persona).

### Positions (one per participant)

```yaml
participant: Security Architect
persona_id: persona.security_architect
position: approve-with-conditions
confidence: 0.9
evidence_used: [EVD-001, EVD-003]
supporting_arguments: [...]
counterarguments: [...]
conditions: ["Rate limiting at launch"]
reversal_conditions:
  - condition: "Scalper rate > 30%"
    threshold: quantitative
    currently_met: false
```

### Cross-Examination (mandatory when material conflicts exist)

```yaml
conflict_id: CONFLICT-001
disagreement: "Whether rate limiting is necessary at launch"
participants: [Security Architect, Business Strategist]
resolution_options: [A, B, C]
jarvis_assessment: "A is strongest..."
```

### Votes + Agreement Classification

```yaml
full_agreement: 0
gualified_agreement: 2 groups
partial_agreement: 1 item
abstentions: 0
vote_result: "5/5 approve (with varying conditions)"
```

### Conclusion

```yaml
meeting_id: MEETING-20260911-001
status: complete
meeting_type: strategic-direction
recommendation: <best defensible option>
type: council-recommendation
status: candidate  ← NOT active
confidence_propagation:
  evidence_quality: 0.82
  meeting_confidence: 0.827
  confidence_label: HIGH
reversal_conditions: [...tracker...]
```

## Meeting Protocol

Full 10-step procedure: `.jarvis/council/meeting-protocol.md`

1. Define the question
2. Select participants and meeting type
3. Create the meeting record
4. Collect evidence (pre-meeting, JARVIS-only)
5. Load each persona sequentially
6. Cross-examination (mandatory when conflicts exist)
7. Agreement classification
8. JARVIS synthesis
9. Confidence propagation and conclusion
10. Record and report

## Rules

1. **Sequential activation** — one persona at a time, same model, position saved before next loads
2. **Council votes stay candidates** — never auto-become truth
3. **Council members never mutate the project** — recommendations only
4. **Decision-authority required** — user must approve to make active
5. **Reasoning preserved** — positions and counterarguments are kept
6. **Audit trail** — meeting events are logged
7. **Seats are perspectives** — not separate consciousnesses
8. **Disagreement is healthy** — fake consensus is worse than disagreement