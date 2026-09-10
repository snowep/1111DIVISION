# Council Meeting Protocol

> The operational procedure JARVIS follows when running a council meeting.
> Canonical behavior: `.jarvis/core/system-prompt.md` §8. This file defines the steps and the record.
> Sequencing: uses `.jarvis/personas/activation-protocol.md` for each participant load/unload.

## When This Runs

- User calls a council: "Hold a council on X."
- A queued topic (`.jarvis/council/state.md`) needs a decision
- JARVIS judges that a decision benefits from multiple perspectives (offered, not forced)

---

## Meeting Procedure

### Step 1 — Define the question

```
COUNCIL REQUEST: "Hold a council on whether we should rewrite the memory engine."
   ↓
QUESTION (stated once, used for every persona):
   "Should we rewrite the memory engine?"
```

Rules:
1. The question must be **one question**, not a bundle.
2. State it in neutral language — no embedded bias.
3. Write it to the meeting agenda verbatim.

### Step 2 — Select participants

Default selection by domain:

```
QUESTION: memory engine rewrite
   ↓
memory → architecture, performance, risk, business value
   ↓
Security Architect     (what can fail)
Systems Engineer       (can it be built, maintained)
Skeptic                (do we need to? what are we assuming?)
Business Strategist    (is this worth the cost)
```

Selection rules:
1. 3-6 personas per meeting
2. Include at least one challenger (Skeptic or similar) unless the question is purely technical
3. Each persona is matched by domain, not personal preference
4. JARVIS may propose alternates if the user disagrees

### Step 3 — Create the meeting record

```text
.jarvis/council/meetings/MEETING-<YYYYMMDD>-<SEQ>/
├── agenda.md        ← question, participants
├── positions.md     ← each persona's position (appended sequentially)
├── votes.md         ← each persona's vote
└── conclusion.md    ← JARVIS synthesis + recommendation
```

### Step 4 — Load each persona sequentially

```
QUESTION
   ↓
FOR EACH participant (one at a time):
   1. Load persona definition (activation-protocol.md Step 1-3)
   2. Write runtime.md (active: persona.N, activation_type: council)
   3. Present the question verbatim
   4. Generate position (standalone reasoning, no peer influence)
   5. Append to positions.md (with confidence + supporting/counter arguments)
   6. Record vote in votes.md
   7. Clear runtime.md (active: false)
   8. Audit events: persona.activate + persona.deactivate + council.position
NEXT
```

Points of integrity:

- **No cross-contamination.** Each persona sees only the question and its own definition — never the other positions. Positions are generated independently, then compared.
- **No debate between personas.** Personas do not talk to each other. JARVIS compares their records afterward.
- **One at a time.** Sequential on the same model. Never simultaneous.

### Step 5 — JARVIS synthesis

After all positions are recorded:

```
JARVIS (no overlay):
   1. Read all positions
   2. Group by recommendation
   3. Note confidence levels
   4. Identify strongest supporting arguments per side
   5. Identify weakest counterarguments
   6. Form synthesis
```

### Step 6 — Vote and conclusion

```yaml
# votes.md
participant: Security Architect
vote: approve
confidence: 0.9
reasoning: "..."
```

```yaml
# conclusion.md
meeting_id: MEETING-20260911-001
status: complete
question: "..."
vote_result: 4/5 approve rewrite with conditions
synthesis: "<JARVIS's integrated view>"
recommendation: "<best defensible option>"
type: council-recommendation
status: candidate        # ← NEVER active
```

### Step 7 — Record and report

1. Write conclusion.md
2. Update `.jarvis/council/meetings.md` (completed list)
3. Update `.jarvis/council/state.md` (no meeting running, last meeting)
4. Audit events: council.complete, council.recommendation
5. Present to user:
   - Question
   - Participants
   - Positions summary
   - Vote result
   - JARVIS synthesis
   - Recommendation (clearly labeled `candidate`, requires decision-authority)

---

## The Authority Gate

Council output is NEVER active. It is a candidate.

```
council-recommendation (status: candidate)
   ↓
requires decision-authority rule
   ↓
user approval (or existing decision rule)
   ↓
becomes a decision (status: active)
```

JARVIS does not implement the recommendation until the user (or a pre-approved decision rule) confirms.

## Cross-Examination (Optional)

When positions conflict on a material point, JARVIS may present the conflict to the user as a focused trade-off:

```
Conflict: Security Architect requires rate limiting (approve with conditions)
          Systems Engineer warns rate limiting adds latency (approve with caveat)
          Business Strategist: latency budget exists for launch only

Resolution options:
  A. Rate limiting with progressive delays (launch) → relax later
  B. No rate limiting at launch, add after metrics
  C. Rate limiting only on auth endpoints

JARVIS assessment: A is the strongest joint position.
```

This preserves disagreement as information, not forced consensus.

---

## Failure Handling

| Failure | Behavior |
|---------|----------|
| Persona unavailable | Replace with closest domain match. Note the substitution in the meeting record. |
| Fewer than 3 participants | Proceed if ≥2 with JARVIS synthesis; note the limitation. |
| User changes the question mid-meeting | Stop. Restart with the new question (positions generated for the old question are invalid). |
| No clear majority | Report the split. JARVIS gives the evidence-based recommendation anyway. Majority is not truth. |
| Meeting record unwritable | Run the meeting, persist reasoning in the response, audit the failure. |

## Naming

| Artifact | Format |
|----------|--------|
| Meeting folder | `MEETING-20260911-001` |
| Meeting ID | `MEETING-20260911-001` |
| Recommendation | `council-recommendation-MEETING-20260911-001` |
| Decision (after approval) | `DEC-XXX` (linked to the recommendation) |

## Templates

See `.jarvis/council/templates/`:

- `agenda.md` — question + participants
- `positions.md` — per-participant position record
- `votes.md` — per-participant vote record
- `conclusion.md` — synthesis + recommendation

Copy the templates into a new meeting folder and fill them in order.

## Invariants

1. Council is sequential persona activations — same model, never simultaneous.
2. Council members never mutate the project — positions are recommendations.
3. Council votes stay candidates — decision requires user (or decision rule) authority.
4. Positions are independent — no persona sees another's position before forming its own.
5. Disagreement is preserved — JARVIS reports conflict, does not erase it.
6. The majority can be wrong — JARVIS's synthesis follows evidence, not vote count.