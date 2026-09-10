---
meeting_id: MEETING-YYYYMMDD-SEQ
status: in_progress
---

# Votes & Agreement Classification

> Raw votes are insufficient. We classify the QUALITY of agreement.
> Every position is classified into exactly one agreement category.
> Protocol: `.jarvis/council/meeting-protocol-v2.md` Step 7.

---

## Individual Votes

| Participant | Vote | Confidence | Evidence Count | Reasoning (one line) |
|-------------|------|------------|----------------|----------------------|
| <Name> | <approve/reject/approve-with-conditions/abstain> | 0.9 | 3 | <key reason> |
| <Name> | | | | |

---

## Agreement Classification

### Full Agreement

Same conclusion + same reasoning.

```yaml
full_agreement:
  items:
    - conclusion: "<conclusion>"
      participants: [<Name>, <Name>]
      shared_reasoning: "<the reasoning both share>"
```

<!-- List each full agreement group. If none, leave empty. -->

### Qualified Agreement

Same conclusion + different reasoning.

```yaml
qualified_agreement:
  items:
    - conclusion: "<conclusion>"
      reasoning_map:
        - participant: <Name>
          reasoning: "<their unique reasoning>"
        - participant: <Name>
          reasoning: "<their unique reasoning>"
```

### Partial Agreement

Agree on a subset, disagree on the rest.

```yaml
partial_agreement:
  agreed:
    - item: "<point they agree on>"
      consensus: "X/Y participants"
  disagreed:
    - item: "<point they disagree on>"
      sides: [<Name>, <Name>]
```

### Disagreement

Conflicting conclusions.

```yaml
disagreement:
  items:
    - participants: [<Name>, <Name>]
      conflict: "<what they disagree on>"
      evidence_for:
        - <EVD-ID>  # supports one side
      evidence_against:
        - <EVD-ID>  # supports the other side
```

### Abstention

```yaml
abstentions:
  items:
    - participant: <Name>
      reason: "<why no position was taken>"
```

---

## Agreement Summary

| Category | Count | Participants |
|----------|-------|-------------|
| Full agreement | 0 | — |
| Qualified agreement | 0 | — |
| Partial agreement | 0 | — |
| Disagreement | 0 | — |
| Abstention | 0 | — |

---

## Vote Result

```
X / N <approve | reject | approve-with-conditions | split>
Core question: <unanimous/qualified/partial/split>
Implementation: <conditions and disagreements summary>
```

---

## Note

A split vote is not a failure. Majority is not truth. The synthesis weighs evidence, not count.

Unanimous agreement on the core question does NOT mean implementation is settled — conditions and disagreements are material.