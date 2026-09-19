# ORION Architecture Design

> **ORION** — Orchestrated Reasoning & Intelligence Operating Network  
> A self-evolving, persona-driven, memory-persistent agent runtime with gamified EXP progression.

---

## Vision

ORION is a **playground for building, exploring, and evolving AI agents**. It mirrors JARVIS's capabilities but with:
- **Multi-persona support** — each persona has individual memory/knowledge, merging into shared ORION memory
- **Persistent .md-based storage** — human-readable, version-controllable, token-efficient
- **Self-critique loop** — Builder → Evaluator → Correct → Verify (Phase 5)
- **EXP gamification** — only verified useful work earns EXP, levels unlock capabilities
- **Controlled evolution** — proposals require evidence, testing, approval (Phase 7)
- **Version tracking** — semantic versioning tied to evolution milestones

---

## Core Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ORION CORE                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  PERSONA    │  │  MEMORY     │  │  KNOWLEDGE  │             │
│  │  ROUTER     │──│  GATEWAY    │──│  STORE      │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                     │
│  ┌──────▼────────────────▼────────────────▼──────┐             │
│  │           RETRIEVAL ENGINE                    │             │
│  │  (query → rank → budget → token-aware)        │             │
│  └──────┬────────────────────────────────────┬───┘             │
│         │                                    │                 │
│  ┌──────▼──────┐  ┌────────────┐  ┌──────────▼────────┐       │
│  │  EVALUATOR  │  │    EXP     │  │   EVOLUTION       │       │
│  │  (Phase 5)  │  │  (Phase 6) │  │   (Phase 7)       │       │
│  └──────┬──────┘  └──────┬─────┘  └────────┬──────────┘       │
│         │                │                 │                   │
│  ┌──────▼────────────────▼─────────────────▼──────┐           │
│  │           TOOL ENGINE + PERMISSIONS            │           │
│  │  (FILE, CODE, WEB, TERMINAL, GIT, API, DB)     │           │
│  └────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PERSISTENCE LAYER (.md files)                │
│  .agent/orion/                                                  │
│  ├── memory/          # ORION shared memory                     │
│  ├── knowledge/       # ORION shared knowledge (reference)      │
│  ├── experience/      # Verified task records                   │
│  ├── exp/             # EXP state + records (JSON)              │
│  ├── evolution/       # Proposals + versions                    │
│  ├── personas/        # Per-persona: memory/, knowledge/, etc.  │
│  └── tasks/           # Completed task logs                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Persona System

### Structure
```
.agent/orion/personas/
├── definitions/              # Persona definition .md files
│   ├── researcher.md
│   ├── developer.md
│   ├── analyst.md
│   ├── designer.md
│   └── [custom].md
├── researcher/
│   ├── identity.md
│   ├── memory/
│   │   ├── decisions.md
│   │   ├── preferences.md
│   │   └── long-term-context.md
│   ├── knowledge/
│   │   └── domain-specific.md
│   └── experience/
└── developer/
    ├── identity.md
    ├── memory/
    ├── knowledge/
    └── experience/
```

### Persona Definition Format (.md)
```markdown
# Persona: Researcher

## Role
Deep investigation, synthesis, and knowledge extraction specialist.

## Purpose
Transform raw information into verified understanding.

## Boundaries
- Does not write production code
- Does not make architectural decisions
- Does not execute deployments

## Style
Methodical, citation-heavy, uncertainty-aware.

## Tools
- web_search
- file_read
- knowledge_query

## Memory
[Auto-loaded from memory/ directory]

## Knowledge
- research-methodology
- synthesis-techniques
- source-evaluation

## Skills
- literature-review
- gap-analysis
- hypothesis-formation

## Experience
[Auto-loaded from experience/ directory]

## Evaluation Criteria
- source-credibility
- synthesis-depth
- gap-identification
- uncertainty-honesty

## Level
1
```

### Context Loading Hierarchy (Token-Aware)
```
PERSONA (individual) → SHARED (cross-persona) → ORION (global) → PROJECT (workspace)
```
- Each layer loaded with **token budget** (micro=500, standard=2000, deep=4000, full=8000)
- Relevance-ranked sections, truncated to fit budget
- Shared memory/knowledge = "commons" accessible to all personas

### Activation Flow
```
TASK → PersonaRouter.select_persona() → PersonaRouter.activate_persona()
     → Load identity + memory + knowledge + skills + experience + shared
     → Return PersonaContext (with token estimate)
     → ORION.run_task() with persona context
```

---

## 2. Memory & Knowledge System

### Philosophy
- **Memory** = what happened/changed (episodic, mutable, append-only logs)
- **Knowledge** = what is true/reference (semantic, stable, updated only when facts change)
- Both stored as `.md` files — human-readable, git-diffable, token-efficient

### Storage Layout
```
.agent/orion/
├── memory/
│   ├── decisions.md          # Key decisions with rationale
│   ├── long-term-context.md  # Cross-session context
│   ├── user-preferences.md   # User preferences
│   └── failures.md           # Failed attempts + lessons
├── knowledge/
│   ├── brand-bible.md        # Project identity, vocabulary
│   ├── architecture.md       # System design reference
│   ├── governance.md         # Rules, permissions, workflows
│   └── vocabulary.md         # Domain terminology
├── experience/
│   └── task-records.md       # Verified task summaries (EXP-awarded)
└── shared/
    ├── memory/
    └── knowledge/
```

### Retrieval Engine (Token-Aware)
```python
retrieve(task, budget="standard") → {
    "memory": [...],      # ranked, truncated to budget
    "knowledge": [...],
    "experience": [...],
    "total_tokens": int,
    "gaps": [...]         # query terms not found
}
```
- **Section-based** extraction (by markdown headings)
- **Relevance scoring**: heading hits (0.4) + content hits (0.3) + file path (0.1) + priority bonuses (0.2)
- **Budget enforcement**: hard token limits with truncation notice
- **Gap detection**: identifies missing query terms for explicit follow-up

### Write Path
- **Memory writes**: append to appropriate `.md` (auto-create dirs)
- **Knowledge writes**: require explicit "fact change" confirmation
- **Experience writes**: only Evaluator-verified tasks (auto on PASS)

---

## 3. Versioning System

### Semantic Versioning + Evolution Tiers
```
v<MAJOR>.<MINOR>.<PATCH>-<TIER>.<BUILD>

MAJOR: Breaking architecture changes (evolution Tier 3)
MINOR: New capabilities, personas, tools (evolution Tier 2)
PATCH: Fixes, improvements (evolution Tier 1)
TIER:  evolution tier (0=stable, 1=proposed, 2=testing, 3=integrated)
BUILD: monotonically increasing build counter
```

### Version File
```
.agent/orion/evolution/version.json
{
  "version": "1.2.0-0.47",
  "major": 1, "minor": 2, "patch": 0,
  "tier": 0, "build": 47,
  "codename": "SYNTHESIS",
  "released_at": "2026-01-15T10:30:00Z",
  "evolution_milestones": [
    {"version": "1.0.0", "milestone": "Core pipeline operational"},
    {"version": "1.1.0", "milestone": "Persona system integrated"},
    {"version": "1.2.0", "milestone": "Self-evaluation loop active"}
  ]
}
```

### Version Bumping Rules
- **PATCH**: Auto-increment on successful task completion (EXP awarded)
- **MINOR**: When evolution proposal Tier 2 passes testing
- **MAJOR**: When evolution proposal Tier 3 integrates (breaking change)
- **TIER**: Reflects highest active proposal tier

---

## 4. EXP & Gamification System

### Core Rule
> **EXP measures verified useful experience, not activity volume.**

### EXP Events & Awards
| Event | Base EXP | Condition |
|-------|----------|-----------|
| `simple_verified` | 10 | Simple task, passed evaluation |
| `normal_verified` | 25 | Standard task, passed evaluation |
| `complex_verified` | 50 | Complex task, passed evaluation |
| `major_contribution` | 100 | Architectural/strategic contribution |
| `recovery` | 10 | Corrected critical failure |
| `reusable_improvement` | 10 | Codified pattern/tool |
| `important_discovery` | 10 | Novel insight documented |
| `exceptional_verification` | 10 | Score > 0.95 |

### Level Progression
```
Level 0: Novice        (0 EXP)     — Beginning to build verified experience
Level 1: Experienced   (100 EXP)   — Consistently produces verified useful work
Level 2: Reliable      (500 EXP)   — Dependable across repeated task types
Level 3: Specialized   (1500 EXP)  — Deep verified experience in specific domains
Level 4: Advanced      (5000 EXP)  — Highly experienced with strong verification history
Level 5: Master        (15000 EXP) — Recognized authority, guides evolution
Level 6: Architect     (50000 EXP) — Shapes system architecture, proposes evolution
```

### Level Unlocks (Future)
- Level 1: Access to basic personas
- Level 2: Create custom personas
- Level 3: Propose evolution changes
- Level 4: Vote on evolution proposals
- Level 5: Approve Tier 2 evolutions
- Level 6: Approve Tier 3 (breaking) evolutions

### EXP Persistence
```
.agent/orion/exp/
├── state.json    # {total_exp, level, tasks_verified, last_awarded_at, records[]}
└── records.json  # Full history of EXPRecord objects
```

---

## 5. Self-Critique / Evaluation System (Phase 5)

### Pipeline
```
BUILDER executes → VERIFIER checks → CRITIQUER finds issues → EVALUATOR scores
                                                            ↓
                                            PASS (≥0.8, no CRITICAL) → DONE + EXP
                                                            ↓
                                            FAIL (<0.6 or CRITICAL) → CORRECTION LOOP
                                                            ↓
                                            WARNING (0.6-0.8) → OPTIONAL CORRECTION
```

### Evaluator Configuration
```python
EvaluatorConfig(
    criteria=DEFAULT_EVALUATION_CRITERIA,  # 8 criteria
    pass_threshold=0.8,
    warning_threshold=0.6,
    max_correction_cycles=3,
    require_verification=True,
    require_no_critical_findings=True
)
```

### Default Criteria (Weighted)
| Criterion | Weight | Description |
|-----------|--------|-------------|
| `objective_met` | 1.0 | Task objective fully satisfied |
| `verification_evidence` | 1.0 | Concrete proof of completion |
| `no_critical_issues` | 1.5 | No CRITICAL findings |
| `code_quality` | 0.8 | Lint, types, patterns pass |
| `test_coverage` | 0.8 | Tests exist and pass |
| `documentation` | 0.5 | Changes documented |
| `security_safety` | 1.2 | No security/safety issues |
| `performance` | 0.5 | Meets performance targets |

### Correction Loop
1. EVALUATOR produces findings (CRITICAL/WARNING/INFO)
2. BUILDER attempts corrections for CRITICAL findings
3. Re-verify → Re-critique → Re-evaluate
4. Max 3 cycles (configurable), then final FAIL if unresolved

---

## 6. Evolution System (Phase 7)

### Proposal Lifecycle
```
DRAFT → PROPOSED (Tier 1) → TESTING (Tier 2) → INTEGRATED (Tier 3) → RELEASED
  ↓         ↓                  ↓                  ↓
  │         │                  │                  └─ Version bump (MAJOR/MINOR)
  │         │                  └─ Automated tests + human review
  │         └─ Evidence required, risk assessed
  └─ Anyone with Level 3+ can propose
```

### Proposal Structure
```markdown
# Evolution Proposal: EP-0042

## Title
Add streaming tool results to ModelAdapter

## Problem
Current ModelAdapter waits for full tool completion before returning,
causing perceived latency on long operations.

## Evidence
- 12 tasks had >30s tool latency
- User feedback: "feels unresponsive"
- Competitors (Cursor, Windsurf) stream results

## Proposed Change
Modify ModelAdapterInterface.invoke() to support async generator
yielding partial results. Update SimpleModelAdapter and stub adapters.

## Expected Benefit
- Perceived latency reduction: ~60%
- Better UX for long-running tools

## Risk
- Breaking change for custom adapters (Tier 3)
- Stream handling complexity

## Test Plan
1. Unit tests for streaming interface
2. Integration test with 5s+ tool
3. UX comparison: streaming vs non-streaming

## Tier
2 (MINOR version bump on integration)

## Author
developer persona (Level 3, 2400 EXP)

## Status
TESTING
```

### Approval Gates
- **Tier 1 (PATCH)**: Level 3+ author, auto-merge on test pass
- **Tier 2 (MINOR)**: Level 4+ author, 2 Level 4+ approvals
- **Tier 3 (MAJOR)**: Level 5+ author, 3 Level 5+ approvals + EXP cost

---

## 7. Token-Efficient Design

### Strategies
1. **Section-based retrieval** — only load relevant markdown sections
2. **Budget tiers** — explicit token limits per operation
3. **Progressive disclosure** — summary first, expand on demand
4. **Shared commons** — deduplicate memory/knowledge across personas
5. **Truncation markers** — `"... [truncated, 1200 tokens remaining]"`
6. **Gap-driven queries** — explicitly fetch missing info instead of over-loading

### Token Estimates
| Operation | Budget | Typical Tokens |
|-----------|--------|----------------|
| Persona activation | standard (2000) | 800-1500 |
| Task understanding | micro (500) | 200-400 |
| Planning | standard (2000) | 1000-1800 |
| Execution (per step) | micro (500) | 100-300 |
| Evaluation | deep (4000) | 2000-3500 |
| Full context (all) | full (8000) | 5000-7500 |

---

## 8. API Endpoints (Next.js)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/orion/task` | POST | Submit task to ORION pipeline |
| `/api/orion/task/<id>` | GET | Get task status/result |
| `/api/orion/personas` | GET | List available personas |
| `/api/orion/personas/<name>/activate` | POST | Activate persona |
| `/api/orion/memory` | GET/POST | Query/write memory |
| `/api/orion/knowledge` | GET/POST | Query/write knowledge |
| `/api/orion/exp` | GET | Get EXP progress |
| `/api/orion/evolution` | GET/POST | Evolution proposals |
| `/api/orion/version` | GET | Current version |
| `/api/workspace` | GET | Scan workspace |
| `/api/workspace/file` | GET | Read file |

---

## 9. UI Dashboard Integration

### OrionDashboard.tsx Enhancements
- **Persona Panel**: Show active persona, switch personas, view context tokens
- **EXP Bar**: Visual progress, level, recent awards
- **Version Badge**: Current version + codename
- **Task History**: List completed tasks with verdict/EXP
- **Evolution Tracker**: Active proposals, voting status
- **Memory/Knowledge Browser**: Search, view, edit .md files
- **Live Event Stream**: Pipeline stages in real-time

---

## 10. Implementation Phases

### Phase 0: Foundation (Current)
- [x] Next.js + Material UI dashboard
- [x] Workspace scanner API
- [x] Basic memory write API
- [x] ORION core pipeline (Python)
- [x] Persona router, evaluator, EXP, evolution (Python)

### Phase 1: TypeScript Runtime Bridge
- [ ] Port ORION core to TypeScript (or Node.js bridge)
- [ ] Unified API layer for all ORION operations
- [ ] WebSocket for real-time pipeline events

### Phase 2: Memory/Knowledge API
- [ ] Retrieval engine as API endpoint
- [ ] Token-budgeted context loading
- [ ] Memory/knowledge write endpoints with validation

### Phase 3: Persona Management UI
- [ ] Persona library browser
- [ ] Activation/deactivation controls
- [ ] Context token visualization
- [ ] Custom persona creator

### Phase 4: EXP & Gamification UI
- [ ] EXP progress bar with level
- [ ] Achievement log
- [ ] Level unlock notifications
- [ ] Leaderboard (local)

### Phase 5: Evolution Dashboard
- [ ] Proposal browser
- [ ] Voting interface
- [ ] Version history timeline
- [ ] Changelog generator

### Phase 6: Self-Critique Visualization
- [ ] Evaluation score breakdown
- [ ] Findings list with severity
- [ ] Correction loop visualization
- [ ] Before/after comparison

---

## 11. Naming

**ORION** — Orchestrated Reasoning & Intelligence Operating Network

Alternative considerations:
- **NEXUS** — Neural Executive & Unified System
- **CORTEX** — Cognitive Orchestration & Reasoning Engine
- **SYNAPSE** — System for Yielding Networked Autonomous Processing
- **HELIX** — Hierarchical Evolutionary Learning Intelligence

**Decision**: ORION — evokes constellation (guidance), hunter (pursuit), and "on" (active).

---

## 12. Success Metrics

| Metric | Target |
|--------|--------|
| Task pass rate (1st eval) | > 70% |
| Correction loop resolution | > 80% within 2 cycles |
| EXP per verified task | 25 avg |
| Token efficiency (context) | < 2000 tokens standard |
| Persona switch latency | < 500ms |
| Evolution proposal → integration | < 7 days (Tier 2) |
| Memory retrieval relevance | > 85% precision@5 |

---

*Document version: 1.0.0-draft*  
*Next: Implementation begins with Phase 1 — TypeScript Runtime Bridge*