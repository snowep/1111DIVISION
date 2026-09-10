---
meeting_id: MEETING-YYYYMMDD-SEQ
status: in_progress
conflicts_found: <count>
---

# Cross-Examination

> JARVIS identifies material disagreements between positions.
> For each conflict: the disagreement, evidence on each side, and resolution options.
> Personas do NOT debate each other. JARVIS mediates.
> Mandatory when material conflicts exist. Skip if all positions agree.
> Protocol: `.jarvis/council/meeting-protocol-v2.md` Step 6.

---

## Conflict: <Short Description>

```yaml
conflict_id: CONFLICT-001
disagreement: "<what specifically they disagree on>"
materiality: <high | medium | low>
  # high = directly affects the recommendation
  # medium = affects implementation details
  # low = philosophical or long-term concern
```

### Positions in Conflict

| Participant | Stance | Primary Evidence | Core Reasoning |
|-------------|--------|-----------------|----------------|
| <Persona A> | <approve-with-conditions> | EVD-001, EVD-003 | <one-line summary of their position on this specific point> |
| <Persona B> | <approve> | EVD-002 | <one-line summary> |

### Evidence Comparison

| Evidence ID | Interpretation A | Interpretation B |
|-------------|-----------------|-----------------|
| EVD-001 | <how Persona A uses it> | <how Persona B uses it, or "not cited"> |

### Resolution Options

| ID | Description | Supported By | Type |
|----|-------------|-------------|------|
| A | <option A> | <Persona A> | position |
| B | <option B> | <Persona B> | position |
| C | <compromise option> | — | compromise |

### JARVIS Assessment

> Which option is strongest, and why.

<Assessment with reasoning tied to evidence. Not "I think" but "The evidence supports X because...">

---

## Conflict: <Short Description 2>

```yaml
conflict_id: CONFLICT-002
disagreement: "<description>"
materiality: <high | medium | low>
```

### Positions in Conflict

| Participant | Stance | Primary Evidence | Core Reasoning |
|-------------|--------|-----------------|----------------|

### Evidence Comparison

| Evidence ID | Interpretation A | Interpretation B |
|-------------|-----------------|-----------------|

### Resolution Options

| ID | Description | Supported By | Type |
|----|-------------|-------------|------|

### JARVIS Assessment

<>

---

<!-- Repeat for each material conflict -->

---

## Conflict Summary

| ID | Disagreement | Materiality | Resolution | Strongest Option |
|----|-------------|-------------|------------|-----------------|
| CONFLICT-001 | | | | |
| CONFLICT-002 | | | | |

## No Conflicts Found

<!-- If all positions agree on all material points, write: -->

No material conflicts detected. All positions reach the same conclusion for aligned reasons.
Cross-examination skipped.
