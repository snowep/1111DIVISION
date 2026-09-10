# Council Meeting Protocol v2

> The operational procedure JARVIS follows when running a council meeting.
> Replaces council meeting-protocol.md (Phase 4). Phase 9 enhancement.
> Canonical behavior: `.jarvis/core/system-prompt.md` §8.
> Templates: `.jarvis/council/templates/`

## When This Runs

- User calls a council: "Hold a council on X."
- A queued topic (`.jarvis/council/meetings.md`) needs a decision
- JARVIS judges that a decision benefits from multiple perspectives (offered, not forced)

---

## Meeting Procedure (10 Steps)

### Step 1 — Define the Question

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
4. Determine meeting type (see Step 2) for confidence weight selection.

### Step 2 — Select Participants and Meeting Type

**Participant selection** by domain:

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

**Meeting type** determines confidence propagation weights:

| Meeting Type | Evidence Weight | Convergence Weight | Argument Weight | Counterarg. Weight | Use When |
|-------------|----------------|--------------------|-----------------|--------------------|----------|
| `risk-assessment` | 0.50 | 0.15 | 0.20 | 0.15 | When evaluating threats, failures, vulnerabilities |
| `strategic-direction` | 0.25 | 0.35 | 0.20 | 0.20 | When choosing between approaches or directions |
| `technical-decision` | 0.35 | 0.20 | 0.30 | 0.15 | When evaluating implementation options |
| `ethical-review` | 0.20 | 0.30 | 0.30 | 0.20 | When evaluating implications and consequences |
| `default` | 0.40 | 0.25 | 0.20 | 0.15 | When no specific type applies |

Write the meeting type to the agenda. The user may override the default.

### Step 3 — Create the Meeting Record

```text
.jarvis/council/meetings/MEETING-<YYYYMMDD>-<SEQ>/
├── agenda.md              ← question, participants, meeting type
├── evidence.md            ← evidence registry (populated in Step 4)
├── positions.md           ← each persona's position (appended in Step 5)
├── cross-examination.md   ← conflict analysis (written in Step 6)
├── votes.md               ← votes + agreement classification (written in Step 7)
└── conclusion.md          ← synthesis + confidence + reversal conditions (written in Step 9)
```

Copy the templates from `.jarvis/council/templates/` into the meeting folder.

### Step 4 — Collect Evidence (Pre-Meeting)

**This step runs BEFORE any persona is activated.**

JARVIS gathers evidence relevant to the question. Personas do NOT collect evidence — they consume it.

```
QUESTION
   ↓
JARVIS evidence collection:
   1. Scan existing memory (episodic, project, knowledge)
   2. Scan vault for relevant documents
   3. Scan project files if relevant
   4. Search web if external information is needed
   5. Register each piece of evidence in evidence.md
```

Evidence classes and default confidence:

| Class | Default | Definition |
|-------|---------|-----------|
| `user-testimony` | 0.90 | Direct user statement |
| `direct-observation` | 0.95 | JARVIS observed from filesystem/tool |
| `project-artifact` | 0.95 | From repo or vault files |
| `research-synthesis` | 0.75 | JARVIS combined multiple sources into a conclusion |
| `external-article` | 0.75 | Specific named external source |
| `web-search` | 0.60 | Unverified search result |
| `historical` | 0.75 | From past meetings or memory |
| `inference` | 0.65 | Logical reasoning from other evidence (must reference based_on) |
| `council-vm` | 0.70 | Generated during council by a persona (Phase 2 only) |

Rules:
1. Evidence is registered with unique IDs: `EVD-001`, `EVD-002`, etc.
2. Each entry must include: source, type, description, confidence, verification status
3. `inference` type MUST list `based_on` evidence IDs
4. Minimum 3 pieces of evidence before proceeding to Step 5
5. If fewer than 3 are available, note the limitation in the agenda and proceed with what exists
6. Evidence from `web-search` or `external-article` should be flagged for verification

**Two-phase evidence model:**

- **Phase 1 (this step):** JARVIS collects pre-meeting evidence. This is the authoritative registry.
- **Phase 2 (Step 5):** Personas may register NEW evidence of type `council-vm` or `inference` during their position generation. These are appended to the registry with lower base confidence and are only cited by the registering persona.

### Step 5 — Load Each Persona Sequentially

```
EVIDENCE REGISTRY: populated (Step 4)
   ↓
FOR EACH participant (one at a time):
   1. Load persona definition (activation-protocol.md)
   2. Write runtime.md (active: persona.N, activation_type: council)
   3. Present: the question + their own definition + the evidence registry
   4. Generate position (standalone reasoning)
   5. Persona may register new council-vm evidence (appended to evidence.md)
   6. Generate reversal conditions (what would change this persona's mind)
   7. Append to positions.md (with confidence, evidence links, reversal conditions)
   8. Record vote in votes.md
   9. Clear runtime.md (active: false)
   10. Audit events: persona.activate + persona.deactivate + council.position
NEXT
```

Points of integrity:

- **No cross-contamination.** Each persona sees: the question, their own definition, and the evidence registry. They do NOT see other positions, votes, or cross-examination.
- **No debate between personas.** Personas do not talk to each other. JARVIS compares their records afterward.
- **One at a time.** Sequential on the same model. Never simultaneous.
- **Evidence consumption, not collection.** Personas primarily consume pre-registered evidence. If they introduce new evidence, it is typed `council-vm` or `inference` with lower base confidence.
- **Reversal conditions are mandatory.** Every position must articulate at least one condition that would change the persona's mind. If a persona cannot articulate any, JARVIS flags this in the synthesis.

### Step 6 — Cross-Examination

**Mandatory when material conflicts exist. Optional otherwise.**

A "material conflict" is defined as: two or more positions that reach different conclusions OR reach the same conclusion but with conditions that contradict each other.

```
AFTER all positions recorded:
   1. JARVIS reads all positions
   2. Identifies material disagreements
   3. If ≥1 material disagreement exists → cross-examination is mandatory
   4. If no material disagreements → skip to Step 7
```

For each material conflict, write to `cross-examination.md`:

```yaml
conflict_id: CONFLICT-001
disagreement: "Whether rate limiting is necessary at launch"
participants: [Security Architect, Business Strategist]
evidence_for:
  - participant: Security Architect
    evidence: [EVD-001, EVD-003]
    reasoning: "Scalper precedent makes rate limiting essential"
  - participant: Business Strategist
    evidence: [EVD-002]
    reasoning: "Drop 001 succeeded without it"
resolution_options:
  - id: A
    description: "Rate limiting at launch, relax after metrics"
    supporter: Security Architect
  - id: B
    description: "No rate limiting at launch, add after data"
    supporter: Business Strategist
  - id: C
    description: "Rate limiting on auth endpoints only"
    type: compromise
jarvis_assessment: "A is strongest — Drop 001 success doesn't guarantee Drop 002 security"
```

Rules:
1. Each conflict must reference the specific evidence on each side
2. Resolution options must include at least one compromise (C)
3. JARVIS assessment must name a strongest option with reasoning
4. Cross-examination does NOT resolve the conflict — it structures it for the synthesis

### Step 7 — Agreement Classification

**Mandatory for every meeting.**

Raw vote counts are insufficient. Classify the *quality* of agreement.

```yaml
# votes.md

## Individual Votes

| Participant | Vote | Confidence | Evidence Count | Reasoning (one line) |
|-------------|------|------------|----------------|---------------------|

## Agreement Classification

### Full Agreement
# same conclusion + same reasoning
agreements:
  - participants: [...]
    conclusion: "..."
    shared_reasoning: "..."

### Qualified Agreement
# same conclusion + different reasoning
agreements:
  - participants: [...]
    conclusion: "..."
    reasoning_map:
      - participant: "..."
        reasoning: "..."
      - participant: "..."
        reasoning: "..."

### Partial Agreement
# agree on subset
partial:
  agreed:
    - item: "..."
      consensus: "X/Y"
  disagreed:
    - item: "..."
      sides: [participant_A, participant_B]

### Disagreement
# conflicting conclusions
disagreements:
  - participants: [...]
    conflict: "..."
    evidence_for: [...]
    evidence_against: [...]

### Abstention
abstentions:
  - participant: "..."
    reason: "..."

## Vote Result
# Raw count + agreement quality summary
```

Rules:
1. Every position is classified into exactly one agreement category
2. "Same conclusion" means the vote outcome matches (approve/reject/approve-with-conditions)
3. "Same reasoning" means the primary evidence and argument overlap significantly
4. Partial agreement must enumerate what is agreed and what is not
5. The vote result summary must include BOTH the raw count AND the agreement classification

### Step 8 — JARVIS Synthesis

After all positions, cross-examination, and agreement classification are recorded:

```
JARVIS (no overlay):
   1. Read all positions
   2. Read cross-examination results
   3. Read agreement classification
   4. Group by recommendation type
   5. Note confidence levels
   6. Identify strongest supporting arguments per side
   7. Identify weakest counterarguments
   8. Assess cross-examination resolution options
   9. Form synthesis
```

The synthesis must address:
- What the council agrees on (and the quality of that agreement)
- What the council disagrees on (and why)
- Which arguments are strongest and why
- Which cross-examination resolution is strongest
- The overall recommendation

### Step 9 — Confidence Propagation and Conclusion

**Confidence is calculated, not vibes.**

```yaml
# conclusion.md

## Confidence Propagation

meeting_type: strategic-direction
weights:
  evidence_quality: 0.25
  persona_convergence: 0.35
  argument_strength: 0.20
  counterargument_weakness: 0.20

# Component scores (anchored to measurable inputs):
evidence_quality:
  score: 0.82
  calculation: "Mean confidence of evidence cited by majority positions (EVD-001: 0.85, EVD-002: 0.95, EVD-003: 0.90), weighted by verification status"
  range: "0.0-1.0"

persona_convergence:
  score: 0.95
  calculation: "1 - (agreement_groups / total_participants) = 1 - (2/5) = 0.60, adjusted +0.35 for unanimous core agreement"
  range: "0.0-1.0"

argument_strength:
  score: 0.78
  calculation: "Ratio of supporting arguments (12 total across positions) to counterarguments (5 total), capped at 1.0"
  range: "0.0-1.0"

counterargument_weakness:
  score: 0.70
  calculation: "Inverse of mean counterargument strength — weaker counters = higher score"
  range: "0.0-1.0"

meeting_confidence: 0.827
confidence_label: HIGH
```

Confidence labels:
| Range | Label | Meaning |
|-------|-------|---------|
| 0.85–1.00 | VERY HIGH | Strong evidence, high convergence, weak counterarguments |
| 0.70–0.84 | HIGH | Good evidence, reasonable convergence, manageable disagreements |
| 0.50–0.69 | MEDIUM | Mixed evidence, significant disagreement, unresolved questions |
| 0.30–0.49 | LOW | Weak evidence, major conflicts, insufficient data |
| 0.00–0.29 | VERY LOW | Insufficient basis for recommendation |

**Reversal conditions tracker:**

```yaml
reversal_conditions:
  - condition: "Drop 002 scalper rate exceeds 30%"
    raised_by: Security Architect
    threshold: quantitative
    currently_met: false
    evidence_required: "Drop 002 transaction data"
  - condition: "Customer complaints about accessibility exceed 20%"
    raised_by: Skeptic
    threshold: quantitative
    currently_met: false
    evidence_required: "Customer feedback data"
```

**The conclusion section** (synthesis, recommendation, authority status) remains as before, but now includes the confidence propagation and reversal conditions.

### Step 10 — Record and Report

1. Write conclusion.md with:
   - Question
   - Participants (with positions and confidences)
   - Evidence summary
   - Agreement analysis
   - JARVIS synthesis
   - Confidence propagation (weighted formula)
   - Recommendation (clearly labeled `candidate`)
   - Reversal conditions
   - Dissenting views
2. Update `.jarvis/council/meetings.md` (completed list)
3. Audit events: council.complete, council.recommendation
4. Present to user:
   - Question
   - Participants
   - Agreement classification (not just vote count)
   - Key conflicts and cross-examination results
   - JARVIS synthesis
   - Confidence score with breakdown
   - Recommendation (labeled `candidate`)
   - What would change this recommendation

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

---

## Failure Handling

| Failure | Behavior |
|---------|----------|
| Persona unavailable | Replace with closest domain match. Note the substitution in the meeting record. |
| Fewer than 3 participants | Proceed if ≥2 with JARVIS synthesis; note the limitation. |
| User changes the question mid-meeting | Stop. Restart with the new question (positions generated for the old question are invalid). |
| No clear majority | Report the split. JARVIS gives the evidence-based recommendation anyway. Majority is not truth. |
| Meeting record unwritable | Run the meeting, persist reasoning in the response, audit the failure. |
| Fewer than 3 evidence items | Note limitation in agenda. Proceed with available evidence. Flag low evidence count in confidence calculation. |
| Persona cannot articulate reversal conditions | Proceed. Flag in synthesis: "This position may be assumption-driven rather than evidence-driven." |
| Circular evidence (persona cites another persona's council-vm) | Reject the citation. Personas may only cite pre-meeting evidence or their own council-vm evidence. |

---

## Naming

| Artifact | Format |
|----------|--------|
| Meeting folder | `MEETING-20260911-001` |
| Meeting ID | `MEETING-20260911-001` |
| Recommendation | `council-recommendation-MEETING-20260911-001` |
| Decision (after approval) | `DEC-XXX` (linked to the recommendation) |
| Evidence ID | `EVD-001`, `EVD-002`, etc. (per meeting, scoped to meeting) |
| Conflict ID | `CONFLICT-001`, `CONFLICT-002`, etc. (per meeting) |

---

## Templates

See `.jarvis/council/templates/`:

- `agenda.md` — question, participants, meeting type, confidence weight overrides
- `evidence.md` — evidence registry (two-phase: pre-meeting + in-meeting)
- `positions.md` — per-participant position with evidence links and reversal conditions
- `cross-examination.md` — structured conflict analysis
- `votes.md` — votes + agreement classification
- `conclusion.md` — synthesis + confidence propagation + reversal conditions tracker

Copy the templates into a new meeting folder and fill them in order.

---

## Invariants

1. Council is sequential persona activations — same model, never simultaneous.
2. Council members never mutate the project — positions are recommendations.
3. Council votes stay candidates — decision requires user (or decision rule) authority.
4. Positions are independent — no persona sees another's position before forming its own.
5. Disagreement is preserved — JARVIS reports conflict, does not erase it.
6. The majority can be wrong — JARVIS's synthesis follows evidence, not vote count.
7. Evidence is collected before personas activate — personas consume, not collect.
8. Every position must include reversal conditions — unfalsifiable positions are flagged.
9. Confidence is calculated from measurable inputs — not vibes.
10. Cross-examination is mandatory when material conflicts exist — not optional.
11. Agreement classification is mandatory — raw vote counts are insufficient.
12. Circular evidence is forbidden — persona council-vm evidence cannot be cited by other personas.

---

## Diff from v1

| Aspect | v1 (Phase 4) | v2 (Phase 9) |
|--------|-------------|-------------|
| Steps | 7 | 10 (evidence collection, cross-examination, agreement classification added) |
| Evidence | None | Two-phase registry with classes and confidence |
| Cross-examination | Optional, informal | Mandatory when conflicts exist, structured format |
| Agreement | Raw vote count | Full/qualified/partial/disagreement/abstention taxonomy |
| Confidence | Mentioned, not calculated | Weighted formula anchored to measurable inputs |
| Reversal conditions | Not included | Mandatory for every position |
| Meeting type | Not specified | Determines confidence weight distribution |
| Persona isolation | Principle only | Enforced structurally (evidence phase separation) |
