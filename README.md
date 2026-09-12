# JARVIS — personal intelligence operating system

JARVIS manages your data in an **isolated folder** (`.jarvis/` by default) as
plain Markdown files with frontmatter. It provides CRUD, a **memory vault**
(Obsidian-compatible), a **skill manager** with an explicit permission model,
and deterministic derivation of knowledge from canonical documents.

## Layout

```
.jarvis/                <- isolated data folder (gitignored)
  vault/                <- canonical documents (the source of truth)
    episodic/           <- what happened (events, sessions, terminal history)
    semantic/           <- facts and preferences (world model)
    procedural/         <- how-to knowledge and procedures
    decisions/          <- architecture/project decisions + rationale
    learned/            <- lessons extracted from failures/successes
  skills/               <- skill definitions (skill.md manifest + impl)
    registry.md         <- DERIVED, rebuilt on scan, never hand-edited
    registry.json       <- DERIVED, machine-readable twin
  learn/                <- DERIVED, always rebuildable from vault/
    index.json          <- machine-readable inventory
    lessons.md          <- human-readable summary + extracted lessons
    state.md            <- derived JARVIS state (active memories + skills)
docs/                   <- documentation (STRUCTURE.md = canonical structure)
scripts/                <- operational scripts (check_structure.py)
src/jarvis/             <- implementation
tests/                  <- pytest suite
```

> **Strict structure.** Enforced by `python scripts/check_structure.py` and
> `tests/test_structure.py`. See [`docs/STRUCTURE.md`](docs/STRUCTURE.md).

## Memory (P1)

A memory note is a Markdown file with YAML frontmatter:

```markdown
---
id: 20260912-123000-ab12cd
kind: semantic
type: semantic
title: Project uses PostgreSQL
phase: VERIFIED
confidence: 0.9
tags: [project, database]
created: 2026-09-12T12:30:00+00:00
updated: 2026-09-12T12:30:00+00:00
provenance:
  type: user
  source: conversation
  session_id: sess-123
---

The project uses PostgreSQL for its primary datastore.
```

- **Routing** — `episodic`/`semantic`/`procedural`/`decisions`/`learned` map
  to vault subdirectories (extensible).
- **Provenance** — every note answers "why do I believe this?" via
  `provenance` + resolvable `based_on` chains.
- **Phases** — `OBSERVED → INTERPRETED → CANDIDATE → VERIFIED → ACTIVE →
  SUPERSEDED` (+ `REJECTED`/`DEPRECATED`), enforced by `VALID_TRANSITIONS`.
- **Temporal pruning** — `valid_until` marks expiring knowledge;
  `forget_expired()` archives (SUPERSEDED, never deletes).
- **Observe** — `observe()` routes transcript statements into the vault as
  OBSERVED/CANDIDATE notes (proposal stage).

## Skills (P2)

A skill is a directory under `.jarvis/skills/<name>/`:

```
skills/echo/
  skill.md    # manifest (frontmatter)
  impl.py     # implementation
```

```markdown
---
name: echo
version: 0.1.0
description: Echo back the input.
trigger: echo
params: [text]
permissions:
  filesystem: read
  network: no
entry: impl.py
status: active
---
```

- **Permissions** — `filesystem: read|write`, `terminal: execute`,
  `network: read|write`, `memory: read|write`. Enforced by
  `check_permission()` at invocation.
- **Registry** — `skills/registry.md` + `registry.json` are derived, rebuilt
  deterministically by `rebuild_registry()` from `skills/*/skill.md`.

## Commands

```bash
python -m jarvis seed                      # placeholder docs
python -m jarvis new note "Title"          # create a doc
python -m jarvis list / list --kind note   # list docs
python -m jarvis read note/<id>.md         # show one doc
python -m jarvis edit note/<id>.md --title "New" --body "..."
python -m jarvis delete note/<id>.md --yes
python -m jarvis learn                     # rebuild derived knowledge
python -m jarvis remember "text" --kind semantic --tags a,b --confidence 0.9
python -m jarvis status                    # active memories + skills
python -m jarvis forgot --dry-run          # list expired notes
python -m jarvis verify note/<id>.md       # OBSERVED -> VERIFIED
python -m jarvis supersede note/<id>.md    # -> SUPERSEDED
python -m jarvis skill scan                # rebuild skill registry
python -m jarvis skill list                # show skills + permissions
```

Pass `--root <dir>` to use a different isolated folder than `.jarvis`.

## Design rules

1. **Isolation** — data lives only under the store root; path traversal
   rejected.
2. **Canonical vs derived** — `vault/` is canonical; `learn/`, `skills/registry.*`
   are derived, always rebuilt, never authoritative.
3. **Provenance over vibes** — knowledge carries where it came from.
4. **Authority ≠ confidence** — who may act is separate from how likely true.
5. **Lifecycle over deletion** — knowledge is archived (phases), not destroyed.
6. **No magic** — "learning" is deterministic: routing, phases, and derivation
   are explicit and testable.

## Roadmap

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the 10-phase plan (P1 memory +
P2 skills complete; P3 terminal next).

## Tests

```bash
python -m pytest -q
```