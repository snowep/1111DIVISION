---
meeting_id: MEETING-YYYYMMDD-SEQ
status: in_progress
---

# Positions

> Each persona generates their position independently.
> They see: the question, their own definition, and the evidence registry.
> They do NOT see other positions, votes, or cross-examination.
> Protocol: `.jarvis/council/meeting-protocol-v2.md` Step 5.

---

## Position: <Persona Name>

```yaml
participant: <Persona Name>
persona_id: <persona.id>
activated_at: <ISO timestamp>
position: <approve | reject | approve-with-conditions | abstain>
confidence: <0.0–1.0>
```

### Evidence Used

| Evidence ID | How Used |
|-------------|----------|
| EVD-001 | <how this persona interprets or applies the evidence> |
| EVD-002 | |

### Supporting Arguments

- <argument 1 — linked to evidence if applicable>
- <argument 2>

### Counterarguments

- <counter 1>
- <counter 2>

### Conditions

<!-- Required if position is approve-with-conditions. Remove section if position is approve or reject. -->

- <condition 1 — what must be true for this persona to fully endorse>
- <condition 2>

### Assumptions

- <what this persona took for granted — premises not in evidence>

### Reversal Conditions

> What would change this persona's mind? Every position must articulate at least one.
> If none exist, JARVIS flags this position as potentially assumption-driven.

| Condition | Threshold | Currently Met |
|-----------|-----------|---------------|
| <specific, observable condition> | <quantitative/qualitative threshold> | <yes/no> |
| <another condition> | | |

---

## Position: <Persona Name 2>

```yaml
participant: <Persona Name 2>
persona_id: <persona.id>
activated_at: <ISO timestamp>
position: <approve | reject | approve-with-conditions | abstain>
confidence: <0.0–1.0>
```

### Evidence Used

| Evidence ID | How Used |
|-------------|----------|
| EVD-001 | |
| EVD-003 | |

### Supporting Arguments

- <argument 1>

### Counterarguments

- <counter 1>

### Conditions

- <condition 1>

### Assumptions

- <assumption 1>

### Reversal Conditions

| Condition | Threshold | Currently Met |
|-----------|-----------|---------------|
| | | |

---

<!-- Repeat the block for each additional participant -->

---

## New Evidence Registered (Phase 2)

> Personas may register new evidence during position generation.
> Type must be `council-vm` or `inference` only.
> Cited ONLY by the registering persona.

| ID | Type | Description | Confidence | Based On | Registered By |
|----|------|-------------|------------|----------|---------------|
| EVD-010 | council-vm | | 0.70 | | <Persona Name> |

<!-- Remove this section if no Phase 2 evidence was registered -->
