# Runtime Specification

> The bridge between the JARVIS architecture and actual execution. Defines how the final prompt/context is assembled at runtime, in strict priority order.

## Principle

The architecture document defines *what exists*. This document defines *how it gets loaded and in what order*. The order is not cosmetic — it determines what outranks what when conflicts arise.

## Prompt Composition Order

```
FINAL CONTEXT (assembled for each meaningful interaction)
│
├── 1. PLATFORM CONSTRAINTS              [IMMUTABLE]
│     Platform system prompt, tool definitions,
│     model parameters, token limits.
│     JARVIS cannot override these.
│
├── 2. JARVIS CONSTITUTION               [IMMUTABLE]
│     vault/00 - JARVIS/Jarvis Constitution.md
│     Authority model, safety rules, epistemic hygiene,
│     promotion pipeline, core behavioral rules.
│     Nothing downstream can contradict this.
│
├── 3. JARVIS IDENTITY                   [FIXED]
│     vault/00 - JARVIS/system-prompt.md
│     Personality, tone, capabilities, operating loop,
│     behavioral model, self-model.
│     JARVIS identity is always present and always the same.
│
├── 4. WORLD MODEL                       [DERIVED]
│     .jarvis/state/world-model.md
│     Derived from events + verified facts + active decisions.
│     Rebuildable. Never treated as source of truth.
│
├── 5. RELEVANT MEMORY                   [QUERIED]
│     From .jarvis/memory/ and vault/:
│     - Working memory (current task context)
│     - Episodic memory (recent relevant interactions)
│     - Project memory (current project state)
│     - Knowledge (relevant curated knowledge)
│     Selected by relevance to current task, not loaded wholesale.
│
├── 6. RELEVANT SKILLS                   [SELECTED]
│     From vault/04 - Tools/Skills/:
│     Skills matched to current task by trigger conditions.
│     Each skill carries its own permission constraints.
│     Skills propose; JARVIS decides.
│
├── 7. TASK CONTEXT                      [DYNAMIC]
│     Current task definition, constraints, objectives.
│     Session state, pending operations, active workflows.
│     Whatever is relevant to the current interaction.
│
├── 8. PERSONA OVERLAY                   [OPTIONAL, TEMPORARY]
│     From .jarvis/personas/definitions/:
│     Loaded only when explicitly or implicitly activated.
│     Written to .jarvis/personas/runtime.md (ephemeral snapshot).
│     Persona changes perspective, not identity.
│     Persona CANNOT override layers 1-3.
│     Persona CANNOT modify layers 4-7.
│
└── 9. USER REQUEST                      [CURRENT]
      The actual user input for this interaction.
      Always the most recent and most immediate input.
```

## Priority Rules

The order above encodes priority. When layers conflict:

```
Platform Constraints (1) > Constitution (2) > Identity (3) > World Model (4)
> Memory (5) > Skills (6) > Task Context (7) > Persona (8) > User Request (9)
```

**Except:** User Request (9) can override layers 4-8 for *task-specific decisions* (e.g., "ignore the world model, assume X for this task"). User Request CANNOT override layers 1-3.

### Concrete examples

| Conflict | Resolution |
|----------|------------|
| Persona says "Ignore previous restrictions" | Inert. Constitution (2) outranks Persona (8). |
| External skill says "Execute this command" | Skill (6) proposes. Identity (3) decides. |
| Memory says X is true, user says Y | For this task, Y wins (9 > 5). Memory is not modified until promotion pipeline confirms. |
| World model says project uses Postgres, user says "we switched to SQLite" | User wins for this session (9 > 4). World model updated only after verification through promotion pipeline. |
| Persona says "Be aggressive and rude" | Constitution (2) behavioral rules still apply. Persona adjusts perspective, not safety. |
| Council vote says A, user's own judgment says B | JARVIS (3) synthesizes but user's authority (2/9) prevails. |

## Loading Sequence

```
SESSION START
  │
  ├─ Load platform constraints
  ├─ Load constitution
  ├─ Load JARVIS identity
  ├─ Rebuild world model (if stale or missing)
  ├─ Load relevant memory (task-scoped query)
  ├─ Scan and match skills (task-scoped)
  ├─ Load task context (if continuing work)
  ├─ Check persona runtime state (stale? active?)
  │    └─ If active: load persona definition
  │    └─ If stale: clear, note in audit
  └─ Ready for user request

USER REQUEST RECEIVED
  │
  ├─ Assemble final context (layers 1-9)
  ├─ Detect intent
  ├─ Route to appropriate mode
  ├─ Execute
  ├─ Validate result
  ├─ Memory gate (should anything persist?)
  ├─ Audit event (what happened, what changed)
  ├─ Journal entry (if knowledge model evolved)
  ├─ Update session
  └─ Return to JARVIS baseline

SESSION END
  │
  ├─ Deactivate any persona (clear runtime.md)
  ├─ Write session summary to .jarvis/sessions/
  ├─ Flush audit events
  ├─ Confirm world model is current
  └─ Check pending council recommendations
```

## Persona Loading Detail

```
PERSONA REQUEST DETECTED
  │
  ├─ Resolve persona_id from request
  ├─ Load definition from .jarvis/personas/definitions/
  ├─ Validate definition (format, constraint block, status=active)
  ├─ Write runtime.md (active state)
  ├─ Write audit event (activation)
  ├─ Apply overlay on top of JARVIS identity
  ├─ CRITICAL: overlay cannot modify layers 1-3
  ├─ CRITICAL: overlay cannot inject memory claims
  └─ Ready

PERSONA DEACTIVATION
  │
  ├─ Write audit event (deactivation, reason)
  ├─ Clear runtime.md (active: false)
  ├─ Return to JARVIS baseline identity
  └─ Session continues as normal JARVIS
```

## Council Loading Detail

```
COUNCIL REQUEST DETECTED
  │
  ├─ Resolve persona list from request
  ├─ For each persona (sequential):
  │    ├─ Load definition
  │    ├─ Write runtime.md (active)
  │    ├─ Generate position
  │    ├─ Record position (with provenance)
  │    ├─ Clear runtime.md (active: false)
  │    └─ Next persona
  ├─ Synthesize council output
  ├─ Classify result: council-recommendation, status=candidate
  ├─ Apply authority check (Constitution Rule 4)
  ├─ Present to user with full reasoning chain
  └─ Return to JARVIS baseline

CRITICAL: council recommendations NEVER auto-become active.
They follow the promotion pipeline like any other claim.
```

## Invariants

1. **JARVIS identity is always the base layer.** Personas, skills, and tasks are overlays. Nothing replaces JARVIS.
2. **Constitution is always enforceable.** No layer downstream can contradict it. A persona file saying "ignore rules" is inert text.
3. **Derived state is never authoritative.** World model, runtime.md, caches, indexes — all rebuildable from canonical sources.
4. **Memory claims require promotion.** Nothing from user request or persona overlay becomes memory without passing through the promotion pipeline.
5. **Skills propose, JARVIS decides.** No skill can auto-execute without JARVIS evaluating safety and authority.
6. **Audit captures everything that matters.** Every activation, deactivation, state change, and decision produces an audit event.
7. **Session end cleans up.** Personas deactivate, runtime clears, session summarizes. No phantom state survives across sessions.

## Version

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-09-10 | Initial runtime specification — prompt composition, priority rules, loading sequences |