---
meeting_id: MEETING-YYYYMMDD-SEQ
status: in_progress
phase: 1  # Phase 1 = pre-meeting (JARVIS-collected), Phase 2 = in-meeting (persona-generated)
---

# Evidence Registry

> Every piece of evidence cited during the meeting is registered here.
> Enforces provenance: every claim traces to a source and a confidence grade.
> Protocol: `.jarvis/council/meeting-protocol-v2.md` Step 4 (Phase 1) and Step 5 (Phase 2).

---

## Phase 1 — Pre-Meeting Evidence (JARVIS-Collected)

> Collected by JARVIS before any persona is activated.
> Personas consume this evidence; they do not create it in Phase 1.

| ID | Source | Type | Description | Confidence | Verified | Based On |
|----|--------|------|-------------|------------|----------|----------|
| EVD-001 | <where JARVIS found it> | <class> | <what it says> | <0.0–1.0> | <yes/no> | <evidence IDs, if inference> |
| EVD-002 | | | | | | |
| EVD-003 | | | | | | |

### Evidence Classes

| Class | Default Confidence | Definition | Example |
|-------|-------------------|-----------|---------|
| `user-testimony` | 0.90 | Direct user statement | "I prefer Söhne for 11:11 Division." |
| `direct-observation` | 0.95 | JARVIS observed from filesystem or tool | Inspected repo: uses FastAPI |
| `project-artifact` | 0.95 | From repo or vault files | `design-system.md` specifies palette |
| `research-synthesis` | 0.75 | JARVIS combined multiple sources into a conclusion | "8/10 top streetwear brands use limited drops" |
| `external-article` | 0.75 | Specific named external source | ComplexCon 2025 attendance data (The Verge) |
| `web-search` | 0.60 | Unverified search result | Generic search snippet |
| `historical` | 0.75 | From past meetings or memory | CM-001 conclusion on logo |
| `inference` | 0.65 | Logical reasoning from other evidence | Supply/demand logic (MUST reference based_on) |
| `council-vm` | 0.70 | Generated during council by a persona | Virgil Abloh's 3% rule applied (Phase 2 only) |

---

## Phase 2 — In-Meeting Evidence (Persona-Generated)

> Appended during Step 5 as personas generate positions.
> Personas may register NEW evidence of type `council-vm` or `inference` only.
> These are cited ONLY by the registering persona — no cross-citation.

| ID | Source | Type | Description | Confidence | Verified | Based On | Registered By |
|----|--------|------|-------------|------------|----------|----------|---------------|
| EVD-010 | persona.<id> | council-vm | | 0.70 | no | | <Persona Name> |
| EVD-011 | persona.<id> | inference | | 0.65 | no | | <Persona Name> |

### Phase 2 Rules

1. Personas may only register evidence of type `council-vm` or `inference`.
2. `inference` type MUST list `based_on` evidence IDs (pre-existing only, not other Phase 2 entries).
3. Phase 2 evidence carries lower base confidence — it is reasoning, not observation.
4. Phase 2 evidence is cited ONLY by the registering persona. Other personas cannot cite it.
5. If a persona wants to cite another persona's reasoning, it must reference the underlying evidence, not the persona's output.

---

## Evidence Summary

| Total Registered | Phase 1 | Phase 2 | Verified | Unverified |
|-----------------|---------|---------|----------|------------|
| <count> | <count> | <count> | <count> | <count> |

### Verification Status

| ID | Verified | Notes |
|----|----------|-------|
| EVD-001 | yes | Direct observation from filesystem |
| EVD-004 | no | Web search result — needs verification |

---

## Rules

1. Evidence is registered BEFORE positions are generated (Phase 1) or during position generation (Phase 2).
2. Every claim in a position must reference an evidence ID.
3. Evidence confidence is assessed at registration, not at citation.
4. Unverified evidence is flagged but not excluded — personas may use it, but it affects confidence.
5. Evidence IDs are scoped to the meeting (EVD-001 in MEETING-A is different from EVD-001 in MEETING-B).
6. Minimum 3 pieces of Phase 1 evidence before proceeding to Step 5. If fewer are available, note the limitation and proceed with what exists.
