# ORION Memory — Decisions

## Purpose
Architectural and operational decisions with rationale. Prevents re-litigation.

---

## Decision Record Format
```
[DATE] [CATEGORY] [STATUS]
Decision: [what was decided]
Rationale: [why]
Alternatives considered: [what else was evaluated]
Consequences: [trade-offs, follow-ups]
Ref: [commit, issue, discussion]
```

---

## Current Decisions

### 2025-09-18 | ARCHITECTURE | ACCEPTED
**Decision:** Three-tier memory architecture (memory/, knowledge/, experience/) with retrieval-based access
**Rationale:** Full-vault context dumping is unscalable and leaks irrelevant information. Task → relevance → search → retrieve → reason → act mirrors human expert workflow.
**Alternatives:** Single flat vault; vector-only retrieval; no persistent memory
**Consequences:** Requires retrieval engine; adds query latency; enables scaling
**Ref:** Phase 2 spec; commit 06e393d

### 2025-09-18 | ARCHITECTURE | ACCEPTED
**Decision:** ORION core pipeline: Understand → Inspect → Plan → Execute → Verify → Critique → Correct → Report
**Rationale:** Linear pipelines miss feedback loops. Critique and Correct stages catch hallucination and drift before Report.
**Alternatives:** ReAct; Plan-and-execute; pure LLM tool use
**Consequences:** More steps per task; higher reliability; explicit verification gates
**Ref:** .agent/orion/core.py; Phase 1 completion

### 2025-09-18 | TOOLING | ACCEPTED
**Decision:** Word-boundary keyword matching for task classification (not substring)
**Rationale:** Substring matching caused false positives ("findings" → "find", "understanding" → "understand")
**Alternatives:** Regex with boundaries; ML classifier; LLM classification
**Consequences:** Simpler, deterministic, zero-dependency
**Ref:** core.py `_classify_task_type()` fix

### 2025-09-18 | TOOLING | ACCEPTED
**Decision:** JSON serialization for execution log results (not Python repr)
**Rationale:** Python repr (`"result"`) is not valid JSON; breaks downstream parsing
**Alternatives:** `json.dumps()`; custom encoder; msgpack
**Consequences:** Interoperable logs; standard tooling works
**Ref:** core.py `ExecutionLog.add_result()`

### 2025-09-18 | PROCESS | ACCEPTED
**Decision:** Verification extracts handler actions from result strings, not step descriptions
**Rationale:** Step descriptions are intent; result strings are evidence. Previous logic verified intent, not outcome.
**Alternatives:** Separate verification pass; LLM-as-judge; formal specification
**Consequences:** Verification now reflects actual work done
**Ref:** core.py `_verify_task_completion()`

### 2025-09-18 | PROCESS | ACCEPTED
**Decision:** Objective-specific verification keywords (analyze/create/fix)
**Rationale:** Generic "completed/done/success" matches too broadly. Task-type-specific verbs discriminate better.
**Alternatives:** Embedding similarity; rule-based per-type; LLM verification
**Consequences:** More precise verification; maintain keyword lists per type
**Ref:** core.py `_check_verification_keywords()`