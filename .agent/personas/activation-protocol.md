# Persona Activation Protocol

## Overview
How personas are activated, switched, and composed within the ORION pipeline.
Each persona is a reasoning overlay — NOT a separate agent instance.

## Activation Modes

### 1. Explicit Activation (User-Directed)
```
User: "Act as researcher and investigate X"
→ ORION loads researcher identity + memory + skills
→ Pipeline executes with researcher context
→ On completion: researcher experience updated
```

### 2. Implicit Activation (Domain Match)
```
Task classification matches persona domain
→ ORION auto-activates best-fit persona
→ User notified: "[Activating researcher for deep-dive]"
```

### 3. Council Activation (Multi-Perspective)
```
Complex decision → ORION sequences personas
→ Each persona analyzes independently (PRIVATE context)
→ Positions saved to .jarvis/council/meetings/
→ ORION synthesizes → decision
```

## Context Loading Sequence

When activating a persona:

```
1. LOAD identity.md          → role, boundaries, authority, principles
2. LOAD memory.md            → private durable facts
3. LOAD knowledge/index      → domain knowledge files
4. LOAD skills/              → available skills
5. LOAD experience/recent    → last 5 task records (pattern recognition)
6. BUILD context package     → merged into pipeline INSPECT stage
```

## Context Isolation Rules

| Layer | Visibility |
|-------|------------|
| ORION core memory | All personas (read-only) |
| ORION shared knowledge | All personas (read-only) |
| Persona private memory | ONLY that persona |
| Persona private knowledge | ONLY that persona |
| Persona private experience | ONLY that persona |
| Promotion candidates | ORION + target personas |
| Shared knowledge (post-promotion) | All personas |

## Pipeline Integration

Modified INSPECT stage when persona active:

```
INSPECT (with persona):
├── Retrieve ORION shared context (existing)
├── Retrieve persona private memory (NEW)
├── Retrieve persona private knowledge (NEW)
├── Retrieve persona relevant skills (NEW)
├── Retrieve persona recent experience (NEW)
└── Synthesize → planning context
```

## State Persistence

**On task completion**:
1. Persona writes to own `experience/task-records.md`
2. Persona updates own `memory.md` (selective)
3. Persona may propose promotion candidate
4. ORION records which persona handled task

**On persona switch**:
1. Current persona state saved (memory, position)
2. New persona context loaded
3. No cross-contamination

## Council Mode Details

For decisions requiring multiple perspectives:

```
ORION creates meeting: .jarvis/council/meetings/MEETING-YYYYMMDD-SEQ/
├── agenda.md              # decision frame, criteria
├── positions/
│   ├── researcher.md      # researcher's independent analysis
│   ├── developer.md       # developer's independent analysis
│   ├── designer.md        # designer's independent analysis
│   └── analyst.md         # analyst's independent analysis
├── votes/
│   └── <persona>.vote.md  # APPROVE|REQUEST_CHANGES|REJECT + rationale
└── conclusion.md          # ORION synthesis + final decision
```

Each persona in council:
- Runs full pipeline independently with own context
- Produces position paper (saved to positions/)
- Votes without seeing other votes (blind)
- ORION reveals all positions after voting closes

## Deactivation

- Automatic on task completion
- Explicit: "Exit researcher mode"
- Context saved, not destroyed
- Next activation resumes from saved state