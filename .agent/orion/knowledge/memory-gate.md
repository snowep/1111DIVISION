# ORION Knowledge — Memory Gate Protocol

## Purpose
Govern what enters memory, knowledge, and experience stores. Prevent pollution, enforce provenance, maintain hygiene.

---

## Gate Rules

### Memory Gate (memory/)
**Entry Criteria:**
- Decision with rationale (not opinion)
- User preference explicitly stated
- Architectural fact affecting future work
- Cross-session context required

**Rejection Criteria:**
- Conversation fragments
- Temporary state (runtime, session)
- Persona-private info (unless promoted)
- Speculation without evidence
- Duplicate of existing entry

**Process:**
1. Propose entry with source, confidence, category
2. Check for existing entry (update-in-place)
3. Validate format (date, category, confidence, source, ref)
4. Write to appropriate file
5. Index for retrieval

### Knowledge Gate (knowledge/)
**Entry Criteria:**
- Verified reference information
- Architecture/specification documentation
- External knowledge validated against primary sources
- Reusable patterns, protocols, APIs

**Rejection Criteria:**
- Unverified claims
- Opinion presented as fact
- Transient information
- Project-specific decisions (go to memory/)

**Process:**
1. Source verification (official docs, specs, repos)
2. Cross-reference with existing knowledge
3. Write/update topic file
4. Maintain topic index

### Experience Gate (experience/)
**Entry Criteria:**
- Completed task with verified outcome
- Delegation pattern with success rate
- Failure recovery with root cause
- Tool/workflow discovery with evidence

**Rejection Criteria:**
- In-progress tasks
- Unverified claims
- Subjective assessments without evidence

**Process:**
1. Auto-append on task completion (REPORT stage)
2. Include: task ID, type, status, evidence, lesson
3. Index by task type, outcome, date, keywords

---

## Promotion Protocol

### Persona → Shared → ORION
```
Persona discovers pattern
       ↓
Validates across 3+ tasks
       ↓
Proposes to Shared (cross-persona)
       ↓
Shared validates utility
       ↓
Promotes to ORION memory/knowledge
```

**Criteria for promotion:**
- Reusable across personas
- Verified utility (not anecdotal)
- Documented with examples

---

## Memory Hygiene Operations

### Consolidation (weekly)
- Merge duplicate entries
- Update superseded decisions
- Archive obsolete context
- Re-index

### Pruning (monthly)
- Remove entries with confidence < 0.3
- Archive entries > 1 year old with no references
- Compress verbose entries to summaries

### Audit (quarterly)
- Verify decision records still accurate
- Check knowledge against current reality
- Validate experience lessons still apply
- Report drift to user

---

## Provenance Requirements

Every entry must have:
```
Source: [persona_name | system | user | observation | external:<url>]
Date: [ISO8601]
Confidence: [0.0-1.0]
Ref: [commit_hash | file_path | task_id | issue_url]
```

Entries without provenance are rejected at gate.

---

## Retrieval Integration

Gate writes trigger index update:
- Memory: decision index, preference index, context index
- Knowledge: topic index, cross-reference graph
- Experience: task index, pattern index, failure index

Retrieval queries hit indexes first, then fetch sections.