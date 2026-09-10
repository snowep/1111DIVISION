# Status Protocol

> The operational procedure behind: "JARVIS, status."
> Produces a real-time health snapshot of the entire system.

## Purpose

One command shows whether the system is healthy, degraded, or broken.
No deep analysis — just a current-state read.

---

## Procedure

### Step 1 — Scan each subsystem

For each component, check: **exists? populated? current?**

### Step 2 — Classify health

| Indicator | Meaning |
|-----------|---------|
| ✓ | Healthy — exists, populated, current |
| ⚠ | Degraded — exists but stale, empty, or partially broken |
| ✗ | Missing — does not exist or is critically broken |
| — | Not applicable or not configured |

### Step 3 — Render status output

---

## Status Output Format

```
JARVIS STATUS
═══════════════════════════════════════════════════════

IDENTITY
  Identity spec       ✓  .jarvis/core/identity.md
  Constitution        ✓  .jarvis/core/constitution.md (32 rules)
  System prompt       ✓  .jarvis/core/system-prompt.md
  Self-model          ✓  .jarvis/core/self-model.md

WORLD MODEL
  World model         ✓  .jarvis/core/world-model.md
  Last rebuilt        ⚠  2026-09-10 (1 days ago)

MEMORY
  Inbox               ✓  0 candidates
  Working             ✓  empty (correct between sessions)
  Episodic            ✓  N records
  Project             ✓  N records
  Knowledge           ✓  N records
  User                ✓  N records
  Decisions           ✓  N records
  Lessons             ✓  N records
  Index               ✓  current

SKILLS
  Active              1  (github-analysis)
  Adapted             0
  Discovered          0
  Registry            ✓  current
  Permissions OK      ✓  all active skills have declared permissions

PERSONAS
  Available           7
  Active              0
  Registry            ✓  current
  Definitions OK      ✓  all 7 have required sections
  Runtime state       ✓  clear (correct between sessions)

COUNCIL
  Seats               7 defined
  Meetings held       N
  Pending recs        0

CAPABILITIES
  Terminal            ✓  available
  Web research        ✓  available
  File system         ✓  available
  Memory              ✓  available
  Knowledge bases     ✓  available
  Notes               ✓  available
  Calendar            ✓  available
  Automations         ✓  available

VAULT
  Structure           ✓  6 sections present
  Last modified       ⚠  2026-09-10 (1 days ago)

REPOSITORY
  Git status          ✓  clean / N uncommitted
  Remote              ✓  snowep/1111DIVISION (main)
  Last commit         ⚠  <hash> <date> <message>

CONFLICTS
  Open                0
  Resolved            0

AUDIT
  Last audit          —  never / 2026-09-10
  Events recorded     N

PENDING
  Tasks               0
  Memory candidates   0
  Stale files         N
  Broken references   0

═══════════════════════════════════════════════════════
HEALTH: [GREEN / YELLOW / RED]
```

---

## Health Classification

| Score | Color | Meaning |
|-------|-------|---------|
| All subsystems ✓ | GREEN | System healthy — no action needed |
| Any ⚠ present | YELLOW | Degraded — review flagged items |
| Any ✗ present | RED | Broken — critical issue requires attention |

---

## What Each Check Actually Does

### Identity
- `ls` or check existence of each core file
- Count rules in constitution.md
- Verify system-prompt.md is non-empty and > 5KB

### World Model
- Verify file exists and has `DERIVED STATE` marker
- Check `### Date:` field for freshness
- Verify rebuild procedure section exists

### Memory
- Count files in each memory subdirectory
- Check inbox for candidate age
- Verify index.md exists and has correct metadata block
- Check working/ is empty between sessions

### Skills
- Count files in each skill directory
- Verify registry matches file counts
- Check each active skill has `permissions:` block

### Personas
- Count .md files in definitions/
- Verify registry matches file count
- Check runtime.md has `active: false` or is empty

### Council
- Check .jarvis/council/ for meeting records
- Count any pending recommendations

### Vault
- Verify each vault section directory exists
- Check last modified timestamp

### Repository
- `git status --short` for uncommitted changes
- `git remote -v` for remote
- `git log --oneline -1` for last commit

### Conflicts
- Count files in conflicts/open/
- Count files in conflicts/resolved/

### Audit
- Check last audit event
- Count events across audit subdirectories

### Pending
- Count tasks in tasks/ or .jarvis/state/active-tasks.md
- Count candidates in inbox/
- Count stale files (last modified > 30 days)
- Count broken cross-references

---

## When This Runs

- User says "JARVIS, status" / "Status check" / "System health"
- Start of a new session (lightweight version)
- After completing a major task
- Before a self-audit

---

## Invariants

1. Status is read-only — no files are modified.
2. Status is fast — should complete in a single scan pass.
3. Status never lies — if something is broken, it shows ✗.
4. Status is a snapshot — it reflects the moment it was run.
5. Status does not replace the self-audit — it's a lighter check.
