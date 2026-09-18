# ORION Memory — Long-Term Context

## Purpose
Stable project context that persists across sessions. Not a log — a reference frame.

---

## Project Identity
- **Name:** 1111DIVISION
- **Repository:** github.com/snowep/1111DIVISION
- **Local root:** D:\Project\1111DIVISION
- **Primary branch:** main
- **Development branch:** phase2/memory-architecture (current)

## Architecture Overview
```
.agent/
  orion/
    core.py              # ORION orchestrator (Phase 1 complete)
    memory/              # What ORION remembers (this dir)
    knowledge/           # What ORION knows (reference)
    experience/          # What ORION did (audit trail)
    identity.md          # System identity & purpose
    evolution/           # System evolution proposals
    skills/              # Discovered/integrated capabilities
  personas/              # Specialist reasoning perspectives
  shared/                # Cross-persona knowledge/memory/experience
  system/                # Config, permissions, version
  tasks/                 # Task queue & completed records
  sessions/              # Session continuity
```

## Phase Status
- **Phase 0:** Filesystem contract ✅ (commit 44131f3)
- **Phase 1:** ORION core pipeline ✅ (commit 06e393d)
- **Phase 2:** Memory architecture 🔄 (current branch)
- **Phase 3:** Retrieval engine ⏳
- **Phase 4:** Persona activation protocol ⏳
- **Phase 5:** Council meeting protocol ⏳
- **Phase 6:** Skill discovery protocol ⏳
- **Phase 7:** Memory gate protocol ⏳
- **Phase 8:** Deterministic runtime kernel ⏳
- **Phase 9:** Gateway rollout ⏳
- **Phase 10:** Production hardening ⏳

## Key Components
| Component | Location | Status |
|-----------|----------|--------|
| ORION Orchestrator | .agent/orion/core.py | ✅ Operational |
| Task Classification | core.py:_classify_task_type() | ✅ Fixed |
| Pipeline Stages | 8 stages (U→I→P→E→V→C→C→R) | ✅ Verified |
| Verification Logic | core.py:_verify_task_completion() | ✅ Fixed |
| Execution Logging | core.py:ExecutionLog | ✅ JSON-serialized |
| Memory Stores | .agent/orion/memory/ | 🔄 Building |
| Knowledge Stores | .agent/orion/knowledge/ | 🔄 Building |
| Experience Stores | .agent/orion/experience/ | 🔄 Building |
| Retrieval Engine | TBD | ⏳ Next |

## Active Constraints
1. **Never dump full vault into context** — Retrieval-first architecture
2. **No fabricated tool use** — Every claim verifiable
3. **No auto-destructive ops** — Explicit authorization required
4. **Memory hygiene** — Selective, update-in-place, provenance-tracked
5. **Decision permanence** — Record rationale, prevent re-litigation

## Current Task
**Phase 2: Memory Architecture**
- [x] Create memory/ directory with user-preferences.md, decisions.md, long-term-context.md
- [ ] Create knowledge/ directory with topic-based references
- [ ] Create experience/ directory with task records
- [ ] Implement retrieval engine (search → retrieve small sections → reason → act)
- [ ] Integrate with ORION core pipeline

## Important Files
- **System prompt:** JARVIS_SYSTEM_PROMPT.md (78 rules, this persona)
- **Vault protocol:** MEMORY.md (session log), KNOWLEDGE.md (reference commons)
- **ORION core:** .agent/orion/core.py (~31KB, 8-stage pipeline)
- **Task records:** .agent/tasks/completed/task-*.json

## Known Issues / Technical Debt
1. `__pycache__` not gitignored in .agent/orion/ (covered by root .gitignore)
2. No automated test suite for ORION pipeline
3. Retrieval engine not yet implemented
4. Persona system not yet integrated
5. Council protocol not yet implemented
6. Skill discovery not yet implemented