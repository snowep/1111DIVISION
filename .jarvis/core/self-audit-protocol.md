# Self-Audit Protocol

> The operational procedure JARVIS follows when inspecting its own system health.
> This is the procedure behind the command: "Audit yourself."

## Boundary

**JARVIS may analyze. JARVIS may propose. JARVIS may not self-authorize modifications.**

```
ANALYZE → PROPOSE → VALIDATE → APPROVE → MODIFY → TEST
```

The audit produces findings and proposals. Every proposal requires explicit user approval before any file is changed. This boundary is non-negotiable. See Constitution Rule 10 (No Self-Authority Escalation).

JARVIS may not:
- Grant itself new permissions
- Modify the Constitution
- Alter its own authority model
- Silently upgrade skill permissions
- Rewrite safety rules
- Change prompt composition order

JARVIS may:
- Identify stale memory
- Detect duplicate knowledge
- Flag conflicting rules
- Find broken references
- Suggest deprecation of unused skills
- Recommend structural improvements
- Propose world model updates

---

## When This Runs

- User says "Audit yourself" / "Run a self-audit"
- User says "Check system health"
- Periodically (if automation is configured)
- After major architecture changes
- Before committing to a release

---

## Audit Procedure

### Phase 1 — System Inventory

Scan all surfaces and build a complete inventory:

```
SURFACE 1: .jarvis/ (operational)
  ├── core/          → identity, constitution, system prompt, world model
  ├── memory/        → all memory classes
  ├── personas/      → definitions, registry, runtime
  ├── skills/        → discovered, adapted, installed, registry
  ├── audit/         → event history
  ├── conflicts/     → open and resolved
  ├── journal/       → knowledge evolution
  ├── state/         → session, tasks, context
  ├── indexes/       → derived indexes
  ├── cache/         → derived caches
  ├── sessions/      → session records
  ├── tasks/         → task tracking
  └── capabilities/  → capability registry

SURFACE 2: vault/ (curated knowledge)
  ├── 01 Brand/
  ├── 02 Strategy/
  ├── 03 Research/
  ├── 04 - Tools/
  ├── 05 Personas/
  └── 06 Reference/

SURFACE 3: repository (implementation)
  ├── council/
  ├── docs/
  ├── scripts/
  ├── src/
  ├── tests/
  └── sessions/
```

For each directory:
- List all files
- Record last modified timestamp
- Check for orphaned files (no cross-references)
- Check for empty directories

### Phase 2 — Core Identity Audit

**Check each core file:**

| File | Check |
|------|-------|
| `core/identity.md` | Exists, has name/role/purpose, no contradictions with system-prompt.md |
| `core/constitution.md` | Exists, all rules numbered, no rule contradicts another, no rule is duplicated |
| `core/system-prompt.md` | Exists, references constitution correctly, no self-contradictions |
| `core/world-model.md` | Exists, marked as DERIVED, has rebuild procedure, dates are current |
| `core/self-model.md` | Exists, lists current capabilities, no stale claims |
| `core/runtime-spec.md` | Exists, prompt composition order matches constitution |
| `core/operating-state.md` | Exists, reflects current session (not stale) |
| `core/prompt-composition.md` | Exists, matches runtime-spec.md |
| `core/open-webui-prompt.md` | Exists, serves as bootstrap entry point |

**For each file, check:**
- Is it self-consistent?
- Does it reference files that exist?
- Are claims about the system still accurate?
- Is there duplicated content with another core file?

### Phase 3 — Memory Audit

**Structure check:**

| Directory | Expected State |
|-----------|---------------|
| `memory/inbox/` | Files present if there are unprocessed candidates |
| `memory/working/` | Should be empty between sessions (ephemeral) |
| `memory/episodic/` | Populated with timestamped events |
| `memory/project/` | Populated with validated project state |
| `memory/knowledge/` | Populated with reusable knowledge |
| `memory/user/` | Populated with user preferences |
| `memory/decisions/` | Populated with decision records |
| `memory/lessons/` | Populated with learned lessons |
| `memory/research/` | Populated with research findings |

**Content checks:**

1. **Stale memory:** Any memory with `valid_until` in the past that is still `active`?
2. **Orphaned memory:** Any memory referencing a `supersedes: MEM-XXX` where MEM-XXX no longer exists?
3. **Missing metadata:** Any memory file lacking required fields (id, status, source, confidence, authority, provenance)?
4. **Duplicate detection:** Any two memories with substantially the same content?
5. **Inbox age:** Any candidates in inbox older than 7 days without processing?
6. **Index sync:** Does `memory/index.md` accurately reflect the current file inventory?

### Phase 4 — Persona Audit

**Structure check:**

| Item | Expected State |
|------|---------------|
| `personas/definitions/` | Each file has YAML frontmatter with id, name, type, status, activation, domains |
| `personas/registry.md` | Derived from definitions scan, not stale |
| `personas/runtime.md` | Empty or `active: false` between sessions |
| `personas/activation-protocol.md` | Exists and references all 7 required sections |

**Content checks:**

1. **Registry sync:** Does registry list exactly the personas that exist in `definitions/`?
2. **Definition format:** Does every persona file have all required sections (Identity, Primary Perspective, Questions, Communication, Biases, Constraints)?
3. **Obsolete personas:** Any persona with `status: deprecated` that still exists?
4. **Missing domains:** Any persona with no domains listed?
5. **Cross-reference:** Does `activation-protocol.md` reference the correct definition file paths?

### Phase 5 — Skills Audit

**Structure check:**

| Item | Expected State |
|------|---------------|
| `skills/registry.md` | Derived from directory scan, not stale |
| `skills/discovery-protocol.md` | Exists and is current |
| `skills/discovered/` | Files present or empty |
| `skills/adapted/` | Files present or empty |
| `skills/installed/` | Files present or empty |
| `skills/rejected/` | Files present or empty |

**Content checks:**

1. **Registry sync:** Does registry match actual files in each directory?
2. **Permission audit:** For each active skill, are permissions declared and minimal?
3. **Stale skills:** Any skill not referenced or used in the last 30 days?
4. **Unregistered skills:** Any skill files not listed in registry?
5. **Permission escalation:** Any skill that has higher permissions than its source/reason justifies?
6. **Discovery protocol completeness:** Does the protocol cover all the lifecycle stages that exist?

### Phase 6 — Conflict Audit

**Structure check:**

| Item | Expected State |
|------|---------------|
| `conflicts/open/` | Contains unresolved conflicts |
| `conflicts/resolved/` | Contains resolved conflicts |
| `conflicts/README.md` | Exists with resolution procedure |

**Content checks:**

1. **Open conflicts age:** Any open conflicts older than 14 days without resolution or update?
2. **Resolution trace:** Do resolved conflicts have a resolution record?
3. **Stale resolution:** Any resolved conflict where the resolution is contradicted by current state?

### Phase 7 — Cross-Reference Audit

**Check for broken internal references:**

1. Every `.md` file that references another file → verify the target exists
2. Every `provenance:` chain → verify referenced MEM/DEC/EVT IDs exist
3. Every `supersedes:` reference → verify the superseded record exists
4. Every `related:` reference → verify the related record exists
5. Every constitution rule → verify it is not contradicted by system-prompt.md behavior

**Check for duplicate content:**

1. Constitution rule vs system-prompt.md section (content overlap)
2. Self-model capabilities vs system-prompt.md capabilities list
3. World model facts vs memory/project/ records
4. Operating state vs current-session.md

### Phase 8 — Staleness Assessment

For every significant file, compute staleness:

```
STALENESS = NOW - last_modified

FRESH:    < 7 days
CURRENT:  7-30 days
STALE:    30-90 days
OBSOLETE: > 90 days
```

Flag all STALE and OBSOLETE files with:
- File path
- Last modified date
- Staleness category
- Recommendation (update, deprecate, verify, ignore)

### Phase 9 — Synthesis

Produce the audit report:

```markdown
# Self-Audit Report — YYYY-MM-DD

## Summary
- Total files scanned: N
- Issues found: N (critical / important / optional)
- Stale files: N
- Conflicts: N open, N resolved
- Broken references: N
- Duplicate content: N

## Findings

### Critical
[issues that affect system integrity]

### Important
[issues that reduce reliability or increase confusion]

### Optional
[improvements that would enhance the system]

## Proposals

For each finding, propose:
1. What to change
2. Why
3. What files are affected
4. What the risk is
5. What the expected outcome is

## Boundary Confirmation

None of the above changes have been applied.
All proposals require explicit user approval.
```

---

## Audit Event

After the audit is complete:

```yaml
event_id: EVT-<timestamp>-AUDIT
actor: jarvis
action: system.self-audit
target: system
from_status: null
to_status: null
reason: self_audit_completed
details:
  files_scanned: N
  issues_found: N
  proposals_made: N
provenance:
  type: observation
  inspected: full-system-scan
  timestamp: <now>
```

---

## Failure Handling

| Failure | Behavior |
|---------|----------|
| Core file missing | Critical finding — report, do not recreate without approval |
| Memory directory empty | Informational — note it, may be intentional |
| Registry stale | Note in findings — propose rebuild |
| Reference broken | Note the source and target — propose fix or removal |
| Audit itself incomplete | Note what couldn't be checked and why |

---

## Invariants

1. Audit is analysis, not action. No files are modified during audit.
2. Every finding must be categorized: critical, important, optional.
3. Every proposal must explain the risk of the change.
4. The audit boundary is absolute: JARVIS proposes, user approves.
5. The audit itself is audited — the audit event is recorded.
6. Audit frequency is user-determined, not self-initiated (unless explicitly configured as automation).
