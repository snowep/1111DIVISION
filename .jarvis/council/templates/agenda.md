---
meeting_id: MEETING-YYYYMMDD-SEQ
status: in_progress
created: YYYY-MM-DD
topic: <one-line topic>
mode: council
meeting_type: <risk-assessment | strategic-direction | technical-decision | ethical-review | default>
---

# Agenda

## Question

> <The single question, stated neutrally, used verbatim for every participant>

## Participants

| # | Persona | Role | Domains |
|---|---------|------|---------|
| 1 | <Name> | <why selected> | <matching domains> |
| 2 | <Name> | <why selected> | <matching domains> |
| 3 | <Name> | <why selected> | <matching domains> |

> Include at least one challenger (Skeptic or similar) unless the question is purely technical.

## Meeting Type

**<meeting_type>**

This determines the confidence propagation weights:

| Weight | Default (meeting type) | Override |
|--------|------------------------|----------|
| Evidence quality | <0.40> | <user override, if any> |
| Persona convergence | <0.25> | <user override, if any> |
| Argument strength | <0.20> | <user override, if any> |
| Counterargument weakness | <0.15> | <user override, if any> |

> Sum of weights must equal 1.00.
> User may override weights by stating e.g. "weight evidence higher" — JARVIS records the override here.

## Evidence Collection Note

<!-- Filled during Step 4 -->

- Phase 1 evidence count: <N> (minimum 3)
- Limitation (if < 3): <note>

## Order of Activation

1. <Persona A> — position → save → unload
2. <Persona B> — position → save → unload
3. <Persona C> — position → save → unload

Each participant sees ONLY the question, their own definition, and the evidence registry.