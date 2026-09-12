# JARVIS — Development Roadmap

> **Living document.** Every architectural decision is written down before it
> is acted on (see R6 in `docs/STRUCTURE.md`). This roadmap is the plan of
> record for turning the minimal Markdown manager into a personal
> intelligence operating system. Order is dependency-first: each phase builds
> on the substrate of the ones before it.

## Status

| Phase | Title | Status |
|-------|-------|--------|
| P1 | Obsidian-compatible long-term memory | ✅ Implemented (vault routing, provenance, phases) |
| P2 | Skill manager + permission model | ✅ Implemented (manifest, registry, permission checks) |
| P3 | Sandboxed terminal | 🔲 Next |
| P4 | Web reader (controlled HTTP) | 🔲 |
| P5 | Web crawl (structured traversal) | 🔲 |
| P6 | GitHub skill importer | 🔲 |
| P7 | Self-learn (lesson consolidation) | 🔲 |
| P8 | Self-adaptation (preference learning) | 🔲 |
| P9 | Self-evolution (code + UI changes) | 🔲 |
| P10 | Autonomy + governance layer | 🔲 |

## Completed

### P1 — Obsidian-compatible long-term memory ✅

The docstore was renamed `notes/` → `vault/` and extended into a memory
system:

- `vault/{episodic,semantic,procedural,decisions,learned}/` subdirectories.
- YAML frontmatter schema: `id, type, tags, created, updated, source,
  confidence, valid_until, provenance, phase`.
- Routing matrix: memory type → vault subdirectory, extensible via
  `update_routing()`.
- Provenance chains: notes carry `provenance.based_on` links; `provenance_chain()`
  resolves them.
- Lifecycle phases: `OBSERVED → INTERPRETED → CANDIDATE → VERIFIED → ACTIVE → SUPERSEDED`
  (+ `REJECTED`, `DEPRECATED`), enforced by `VALID_TRANSITIONS`.
- Temporal pruning: `valid_until`; `forget_expired()` archives (SUPERSEDED,
  never deletes) expired notes.
- `observe()`: heuristic transcript → vault routing pass (proposal stage).

### P2 — Skill manager + permission model ✅

- Skill = directory with `skill.md` manifest + implementation file.
- Manifest schema: `name, version, description, trigger, params, permissions,
  entry, source, status`.
- Permission model: `filesystem: read|write`, `terminal: execute`, `network:
  read|write`, `memory: read|write`. `check_permission()` enforces at
  invocation; `allowed_permissions()` returns what a skill may do.
- `skills/registry.md` + `skills/registry.json` are **derived** — rebuilt
  deterministically from `skills/*/skill.md` on scan (`rebuild_registry()`).
  Never hand-edited, never authoritative.
- Invalid manifests (missing/invalid skill.md, missing entry file) are
  recorded as `status: invalid` in the registry, keeping the scan
  deterministic.

## Planned

### P3 — Sandboxed terminal

- Spawn shell with cwd pinned in workspace; stream via SSE.
- Blocklist-first commands; timeout + memory cap; audit to
  `vault/episodic/terminal/`.
- Unexpands P9 (running tests).

### P4 — Web reader

- Server-side `fetch`, http/https only, redirect limit, size cap, SSRF guard.
- `@web(url)` chat injection (mirrors `@file()`).

### P5 — Web crawl

- Depth/domain/robots/dedupe caps; output derived into `vault/semantic/`.

### P6 — GitHub skill importer

- Pipeline: DISCOVER → INSPECT → VALIDATE manifest → ISOLATE → ADAPT → TEST →
  INTEGRATE, with human approval gate for permission requests.
- Never blindly imports "all skills" (credential-harvester risk).

### P7 — Self-learn

- Post-task review → `vault/failures/` + `vault/procedural/`, dedupe heuristic.

### P8 — Self-adaptation

- Correction/preference detection → `vault/semantic/preferences.md`; supersede
  not ghost.

### P9 — Self-evolution

- Propose diff → structure check + pytest → show diff → on approval apply +
  commit + push; no silent edits, rollback = `git revert`.

### P10 — Autonomy + governance

- Global permission gates, confirmation dialogs, full audit log, eval harness.

## Principles

1. **Canonical vs derived.** Vault notes are canonical. `learn/`, registry,
   indexes, summaries are derived — always rebuildable, never authoritative.
2. **Provenance.** Every important memory answers "why do I believe this?"
   with a resolvable chain.
3. **Authority ≠ confidence.** Who may act on a note (authority) is orthogonal
   to how likely it is correct (confidence).
4. **Lifecycle over deletion.** Knowledge is archived (phases), not destroyed.
5. **Dependency chain.**

```
P1 Memory ──┬──► P7 Self-Learn ──► P8 Self-Adapt
            └──► P2 Skills ──┬──► P3 Terminal ──────┐
                             └──► P4 Web ──► P5 Crawl / P6 GitHub ──► P9 Self-Evolve
P3 + P6 + P1 ───────────────────────────────────────────────────────► P9 ──► P10
```

---

*Updated: 2026-09-12 — P1+P2 implemented.*