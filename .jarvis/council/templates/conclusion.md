---
meeting_id: MEETING-YYYYMMDD-SEQ
status: complete
completed: YYYY-MM-DD
type: council-recommendation
recommendation_status: candidate
meeting_type: <risk-assessment | strategic-direction | technical-decision | ethical-review | default>
---

# Conclusion

## Question

> <The question, verbatim>

## Participants

<Name (position, confidence), Name (position, confidence), ...>

## Evidence Summary

| Evidence ID | Used By | Verdict |
|-------------|---------|---------|
| EVD-001 | X/Y personas | <support for the recommendation / against / neutral / insufficient> |
| EVD-002 | | |

## Agreement Analysis

- **Core question:** <vote result with agreement classification>
- **Agreement quality:** <full/qualified/partial/disagreement breakdown>
- **Material conflicts resolved in cross-examination:** <summary of CONFLICT IDs and resolutions>

## JARVIS Synthesis

<JARVIS's integrated view — what the positions agree on, where they conflict, which arguments are strongest, which cross-examination resolution is strongest, and why>

## Recommendation

<The best defensible option, per JARVIS's evidence-based assessment>

```yaml
type: council-recommendation
status: candidate
recommendation_id: council-recommendation-MEETING-YYYYMMDD-SEQ
evidence_ids: [EVD-001, EVD-002, ...]
```

## Confidence Propagation

> Calculated per protocol Step 9. Anchored to measurable inputs, not vibes.

```yaml
meeting_type: <type>

weights:
  evidence_quality: <0.00 - e.g. 0.40>
  persona_convergence: <0.00 - e.g. 0.25>
  argument_strength: <0.00 - e.g. 0.20>
  counterargument_weakness: <0.00 - e.g. 0.15>

evidence_quality:
  score: <0.0–1.0>
  calculation: "<mean confidence of evidence cited by majority positions, weighted by verification status>"

persona_convergence:
  score: <0.0–1.0>
  calculation: "<1 - (agreement groups / total participants), adjusted for unanimous core>"

argument_strength:
  score: <0.0–1.0>
  calculation: "<ratio of supporting to counterarguments across positions, capped>"

counterargument_weakness:
  score: <0.0–1.0>
  calculation: "<inverse mean counterargument strength>"

meeting_confidence: <weighted sum = evidence_quality × weight + ...>
confidence_label: <VERY HIGH | HIGH | MEDIUM | LOW | VERY LOW>
```

### Confidence Scale

| Range | Label | Meaning |
|-------|-------|---------|
| 0.85–1.00 | VERY HIGH | Strong evidence, high convergence, weak counterarguments |
| 0.70–0.84 | HIGH | Good evidence, reasonable convergence, manageable disagreements |
| 0.50–0.69 | MEDIUM | Mixed evidence, significant disagreement, unresolved questions |
| 0.30–0.49 | LOW | Weak evidence, major conflicts, insufficient data |
| 0.00–0.29 | VERY LOW | Insufficient basis for recommendation |

## What Would Change This Recommendation

> Aggregated from all positions' reversal conditions.
> These are the falsification conditions for the recommendation.

| Condition | Raised By | Threshold | Currently Met | Evidence Required |
|-----------|-----------|-----------|---------------|------------------|
| <condition> | <persona> | <quantitative/qualitative> | <yes/no> | <what evidence would show it> |
| | | | | |

## Authority Status

**This recommendation is a CANDIDATE. It does not take effect until a user (or pre-approved decision rule) confirms it.**

| Confirmed | Authority | Decision ID | Date |
|-----------|-----------|-------------|------|
| ☐ | user-explicit | DEC-XXX | |

## Dissenting Views

<Preserved disagreements that did not win the recommendation. Reference CONFLICT IDs from cross-examination.md where applicable.>

## Flags

<!-- JARVIS flags any positions that violated protocol integrity: -->

- <Flag: Persona X could not articulate reversal conditions — position may be assumption-driven.>
- <Flag: Evidence count below minimum (N < 3). Confidence is provisional.>
- <Flag: Circular evidence citation rejected for Persona X.>