# Persona Promotion Protocol

## Overview
Mechanism for controlled knowledge transfer from private persona stores to shared knowledge.
Prevents contamination while allowing valuable insights to propagate.

## Flow: PRIVATE → CANDIDATE → VALIDATE → SHARED

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│   PRIVATE   │ ──▶ │  CANDIDATE   │ ──▶ │  VALIDATE   │ ──▶ │  SHARED  │
│  (persona)  │     │  (staging)   │     │  (review)   │     │ (global) │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────┘
     │                    │                    │                   │
   Auto on task        Persona proposes    ORION + peers      Merge to
   completion          promotion           review & vote      shared/
                                                     │
                                              Reject = back to PRIVATE
```

## Stage 1: PRIVATE (Persona-Local)
- Each persona maintains own memory/, knowledge/, experience/
- No visibility to other personas
- Auto-updated on task completion via experience log

## Stage 2: CANDIDATE (Staging)
**Trigger**: Persona identifies potentially-shareable insight
**Location**: `.agent/personas/_promotion/candidates/<persona>/<timestamp>-<topic>.md`

**Candidate Format**:
```markdown
# Candidate: <topic>

## Source
Persona: <name>
Date: <ISO timestamp>
Task: <task-id>
Confidence: HIGH|MEDIUM|LOW

## Proposed Knowledge
<the insight, fact, pattern, or procedure>

## Evidence
- Experience ref: <experience entry>
- Memory ref: <memory entry>
- External refs: <urls, files>

## Applicability
- Relevant to: [persona1, persona2, ORION, all]
- Domain: <domain tags>
- Expiry: <when this might become stale>

## Risk if Wrong
<what breaks if this is incorrect>
```

## Stage 3: VALIDATE (Review)
**Reviewers**: ORION + affected personas
**Process**:
1. ORION receives candidate notification
2. ORION routes to relevant personas for comment
3. Each reviewer votes: APPROVE | REQUEST_CHANGES | REJECT
4. Quorum: ORION + ≥1 affected persona = APPROVE
5. On REJECT: returns to PRIVATE with feedback
6. On REQUEST_CHANGES: persona revises, re-submits

**Validation Criteria**:
- Verifiable: can be independently confirmed
- Durable: not task-specific ephemera
- Generalizable: useful beyond single persona
- Non-contaminating: doesn't leak private context
- Attributed: clear provenance chain

## Stage 4: SHARED (Global Knowledge)
**Location**: `.agent/orion/knowledge/` (existing shared knowledge)
**Format**: Standard knowledge file with provenance header
```markdown
# <topic>

## Provenance
Origin: <persona>
Promoted: <date>
Validators: <list>
Confidence: <level>

## Content
<validated knowledge>
```

## Automation Rules
- Auto-promote on: repeated independent discovery (3+ personas)
- Auto-reject on: confidence LOW without corroboration
- TTL: candidates expire after 30 days → auto-reject
- Max candidates per persona: 10 active

## Emergency Override
ORION can direct-promote with audit trail:
```
ORION_DIRECT: <reason>
Approved by: ORION
Date: <timestamp>
```