# ORION Knowledge — Pipeline Architecture

## Overview
The ORION pipeline is an 8-stage deterministic execution model for task processing. Each stage has a specific purpose, input, output, and verification gate.

---

## Stage Definitions

### 1. UNDERSTAND
**Purpose:** Parse the task, identify true objective, detect ambiguity
**Input:** Raw task string + context (memory, project state)
**Output:** Structured task object with:
- `objective`: What actually needs to happen
- `task_type`: analysis | creation | fix | research | delegation
- `constraints`: Hard limits (time, tools, permissions)
- `ambiguities`: Questions needing clarification
**Gate:** Objective clarity ≥ threshold OR user clarification received

### 2. INSPECT
**Purpose:** Gather evidence from available sources
**Input:** Structured task from UNDERSTAND
**Operations:**
- File system scan (grep, glob, read)
- Code inspection (AST, symbols, dependencies)
- Web search (if external facts needed)
- Memory query (relevant past decisions, preferences)
- Knowledge base lookup (documentation, specs)
**Output:** Evidence bundle — facts, not opinions
**Gate:** Sufficient evidence for planning OR explicit gap acknowledged

### 3. PLAN
**Purpose:** Decompose into minimal, verifiable steps
**Input:** Task objective + evidence bundle
**Output:** Execution plan:
- Ordered steps with single responsibility
- Each step: action, tool, expected outcome, verification method
- Dependencies between steps marked
- Rollback points identified
**Gate:** Plan covers objective; steps are atomic and verifiable

### 4. EXECUTE
**Purpose:** Run the plan, capturing all outputs
**Input:** Execution plan
**Operations:** For each step:
- Invoke tool with parameters
- Capture stdout, stderr, return code, files changed
- Record in execution log (JSON)
- On failure: attempt correction (stage 7) or halt
**Output:** Execution log with results per step
**Gate:** All steps attempted; failures logged with context

### 5. VERIFY
**Purpose:** Confirm objective actually achieved
**Input:** Execution log + original objective
**Methods:**
- Keyword matching (task-type-specific verbs in results)
- Output inspection (file exists, test passes, value matches)
- Regression check (nothing else broken)
- Evidence vs. claim comparison
**Output:** Verification result: PASS | PARTIAL | FAIL + evidence
**Gate:** PASS → REPORT; PARTIAL/FAIL → CRITIQUE

### 6. CRITIQUE
**Purpose:** Adversarial review of the work
**Input:** Verification result + execution log + objective
**Personas invoked (internal):**
- Skeptic: What could be wrong?
- Security: What attack surface opened?
- Maintainer: What breaks in 6 months?
- User: Does this solve the real problem?
**Output:** Critique report: issues found, severity, recommendations
**Gate:** No CRITICAL issues → REPORT; else → CORRECT

### 7. CORRECT
**Purpose:** Fix issues found in CRITIQUE
**Input:** Critique report + execution log
**Operations:**
- Targeted fixes for each issue
- Re-run VERIFY on corrected steps
- Update execution log
**Output:** Corrected execution log
**Gate:** Re-verification PASS → REPORT; max 3 correction cycles

### 8. REPORT
**Purpose:** Communicate result to user
**Input:** Final execution log + verification + critique summary
**Output:** Structured response:
- Status: COMPLETE | PARTIAL | FAILED
- What was done (concise)
- Evidence of completion
- Known limitations / follow-ups
- Memory updates proposed
**Gate:** Response delivered; memory persistence triggered

---

## Task Type Classification

| Type | Keywords (verification) | Typical Stages |
|------|------------------------|----------------|
| analysis | analyze, inspect, examine, audit, review, assess | U→I→V→R |
| creation | create, write, generate, build, implement, add | U→I→P→E→V→R |
| fix | fix, repair, debug, resolve, patch, correct | U→I→P→E→V→C→C→R |
| research | research, search, investigate, explore, find | U→I→V→R |
| delegation | delegate, assign, route, dispatch | U→P→E→V→R |

---

## Execution Log Schema (JSON)
```json
{
  "task_id": "task-20250918-001",
  "objective": "string",
  "task_type": "analysis|creation|fix|research|delegation",
  "stages": {
    "understand": {...},
    "inspect": {...},
    "plan": [...],
    "execute": [
      {"step": 1, "action": "...", "tool": "...", "result": "...", "status": "ok|error"}
    ],
    "verify": {"status": "pass|partial|fail", "evidence": [...], "details": "..."},
    "critique": {"issues": [...], "severity": "none|low|medium|high|critical"},
    "correct": {"cycles": 0, "actions": [...]},
    "report": {"status": "complete|partial|failed", "summary": "..."}
  },
  "memory_updates": [...],
  "timestamp": "ISO8601"
}
```

---

## Verification Keywords by Task Type

### Analysis
Primary: `analyzed`, `inspected`, `examined`, `audited`, `reviewed`, `assessed`, `found`, `identified`, `discovered`
Secondary: `evidence`, `conclusion`, `finding`, `observation`, `pattern`

### Creation
Primary: `created`, `written`, `generated`, `built`, `implemented`, `added`, `saved`, `file created`
Secondary: `output`, `result`, `artifact`, `delivered`

### Fix
Primary: `fixed`, `repaired`, `resolved`, `patched`, `corrected`, `debugged`, `test passed`
Secondary: `root cause`, `regression`, `verified`, `working`

### Research
Primary: `researched`, `found`, `located`, `discovered`, `retrieved`, `sourced`
Secondary: `reference`, `documentation`, `specification`, `authoritative`

---

## Failure Modes & Mitigations

| Failure Mode | Detection | Mitigation |
|--------------|-----------|------------|
| Hallucinated file read | VERIFY: file not in execution log | Require tool trace evidence |
| Wrong tool used | CRITIQUE: Skeptic persona | Tool selection in PLAN stage |
| Incomplete objective | VERIFY: keyword mismatch | Objective-specific keywords |
| Silent data loss | EXECUTE: diff tracking | Pre-mutation backup |
| Infinite correction loop | CORRECT: cycle counter | Max 3 cycles, then escalate |
| Context overflow | UNDERSTAND: token estimate | Retrieval-first, not dump-first |