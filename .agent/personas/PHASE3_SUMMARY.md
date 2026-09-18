# Phase 3 — Personas Architecture: Complete

## Overview
Implemented the persona system as specified: each persona gets identity, private memory, private knowledge, skills, and experience. The critical innovation is the **PRIVATE → CANDIDATE → VALIDATE → SHARED** promotion pipeline that prevents cross-contamination while enabling valuable insights to propagate.

## Directory Structure

```
.agent/personas/
├── _template/                    # Template for new personas
│   ├── identity.md
│   ├── memory.md
│   ├── knowledge/README.md
│   ├── skills/README.md
│   └── experience/README.md
├── _promotion/
│   ├── candidates/
│   │   ├── researcher/
│   │   ├── developer/
│   │   ├── designer/
│   │   └── analyst/
├── promotion-protocol.md         # PRIVATE→CANDIDATE→VALIDATE→SHARED
├── activation-protocol.md        # How personas load/switch/compose
├── registry.md                   # Persona catalog + activation keywords
├── researcher/                   # Deep-dive investigation
│   ├── identity.md
│   ├── memory.md
│   ├── knowledge/
│   ├── skills/
│   └── experience/
├── developer/                    # Code implementation
│   ├── identity.md
│   ├── memory.md
│   ├── knowledge/
│   ├── skills/
│   └── experience/
├── designer/                     # UX/UI design
│   ├── identity.md
│   ├── memory.md
│   ├── knowledge/
│   ├── skills/
│   └── experience/
└── analyst/                      # Strategic analysis
    ├── identity.md
    ├── memory.md
    ├── knowledge/
    ├── skills/
    └── experience/

.jarvis/council/meetings/
├── templates/
│   ├── agenda.md
│   ├── position.md
│   ├── vote.md
│   └── conclusion.md
├── positions/
└── votes/
```

## Four Core Personas (Operational)

| Persona | Role | Key Boundaries |
|---------|------|----------------|
| **researcher** | Deep-dive investigation, fact-finding | No code, no design, no strategy |
| **developer** | Implementation, refactoring, testing | No research, no design, no architecture |
| **designer** | UX/UI, accessibility, design systems | No code, no research, no backend |
| **analyst** | Trade-offs, risk, decision frameworks | No implementation, no visual design |

## The Promotion Pipeline (Key Differentiator)

```
PRIVATE (persona-local)
    │ Auto on task completion
    ▼
CANDIDATE (staging) — Persona proposes, writes to _promotion/candidates/
    │ ORION routes to reviewers
    ▼
VALIDATE (review) — ORION + affected personas vote: APPROVE/REQUEST_CHANGES/REJECT
    │ Quorum = ORION + ≥1 affected persona
    ▼
SHARED (global) — Merged to .agent/orion/knowledge/ with provenance header
```

**Prevents contamination**: Persona A's failed experiment never pollutes Persona B's context.
**Enables propagation**: Persona A's discovered pattern becomes shared knowledge after validation.

## Activation Modes

1. **Explicit**: "Act as researcher and investigate X"
2. **Implicit**: Task classification → auto-activate best-fit persona
3. **Council**: Multi-perspective decision → sequential independent analysis → blind voting → ORION synthesis

## Pipeline Integration

Modified INSPECT stage loads persona context:
- ORION shared memory/knowledge (read-only)
- Persona private memory/knowledge/skills/experience (read-write)
- Synthesized into planning context

## Council Templates Ready

- `agenda.md` — Decision frame, criteria, required perspectives
- `position.md` — Independent analysis per persona (private until reveal)
- `vote.md` — Blind voting with rationale
- `conclusion.md` — ORION synthesis, trade-offs, dissent recorded

## Next: ORION Integration

The persona system is now **structurally complete**. Next steps for full integration:

1. **ORION pipeline hook**: Modify INSPECT stage to load active persona context
2. **Activation CLI**: `orion activate <persona>` / `orion council <decision>`
3. **Auto-promotion monitor**: Background task checking candidate TTL, quorum
4. **Experience→Memory automation**: On task completion, update persona memory.md
5. **Registry CLI**: `orion persona list|create|archive`

## Verification

All four personas have:
- ✅ identity.md (role, boundaries, authority, principles)
- ✅ memory.md (private, categorized, provenance-tracked)
- ✅ knowledge/ (directory for domain files)
- ✅ skills/ (directory for reusable skills)
- ✅ experience/ (directory for task logs)

Promotion infrastructure:
- ✅ promotion-protocol.md (full spec)
- ✅ _promotion/candidates/ per persona
- ✅ activation-protocol.md (loading, switching, council)
- ✅ registry.md (catalog, keywords, council rules)
- ✅ council templates (agenda, position, vote, conclusion)