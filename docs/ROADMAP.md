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
| P3 | Memory filter + self-critique | ✅ Implemented (importance scoring, temporal decay, structured lessons) |
| P10 | Deterministic runtime kernel | ✅ Implemented (roots, identity, validation, context priority, IO boundary) |
| P3b | Sandboxed terminal skill | ✅ Implemented (safe-exec: blocklist, cwd-pin, timeout, cap, authority) |
| P4 | Web reader (controlled HTTP) | ✅ Implemented (SSRF/IP/port/scheme/redirect/size guards, authority) |
| P5 | Web crawl (structured traversal) | ✅ Implemented (depth/domain/robots/dedupe caps, output to vault/semantic/) |
| P6 | GitHub skill importer | ✅ Implemented (DISCOVER→INSPECT→VALIDATE→ISOLATE→ADAPT→TEST→INTEGRATE, approval gate) |
| P7 | Self-learn (lesson consolidation) | 🔲 Next |
| P8 | Self-adaptation (preference learning) | 🔲 |
| P9 | Self-evolution (code + UI changes) | 🔲 |
| P11 | Autonomy + governance layer | 🔲 |

## Completed

### P1 — Obsidian-compatible long-term memory ✅

The docstore was renamed `notes/` → `vault/` and extended into a memory
system:

- `vault/{episodic,semantic,procedural,decisions,learned}/` subdirectories.
- YAML frontmatter schema: `id, type, tags, created, updated, source,
  confidence, valid_until, provenance, phase, importance`.
- Routing matrix: memory type → vault subdirectory, extensible via
  `update_routing()`.
- Provenance chains: notes carry `provenance.based_on` links;
  `provenance_chain()` resolves them.
- Lifecycle phases: `OBSERVED → INTERPRETED → CANDIDATE → VERIFIED →
  ACTIVE → SUPERSEDED` (+ `REJECTED`, `DEPRECATED`), enforced by
  `VALID_TRANSITIONS`.
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

### P3 — Memory filter + self-critique ✅

Adds the JARVIS Master Prompt Section 10 (Memory Filter) and Section 68
(Self-Critique) directly into the P1 substrate:

- `memory/assess.py` — `assess_importance()` scores every memory candidate
  (0.0–1.0) from structural kind + utility keywords; `calculate_decay()`
  assigns ephemeral `valid_until` boundaries (24h / 7d) to low-importance
  notes so they self-expire and get archived.
- `memory/engine.py` — `MemoryNote.importance`; `list_active()` ranks by
  importance desc, then updated date.
- `memory/observe.py` — harvested statements are auto-weighted + decayed.
- `memory/critique.py` — `critique_task()` turns a failed task into
  structured lessons (wrong assumption, corrected understanding) stored
  under `vault/learned/` with provenance.

### P10 — Deterministic runtime kernel ✅

The runtime substrate every capability runs on:

- `core/roots.py` — canonical workspace root (workspace marker + `src/`,
  `tests/`, `docs/`); `resolve_path()` confines any user path under the
  root; `authority_for()` binds an `Authority` (kind/name/scope/permissions)
  and `permits()` checks scope containment — traversal is refused before
  any IO.
- `core/identity.py` — JARVIS identity is loaded ONLY from `.jarvis/core/`
  files (identity.md, constitution.md, platform.md, system.md); never from
  Open WebUI config; missing/duplicate files raise typed errors.
- `io/workspace.py` — `WorkspaceResolver` maps semantic aliases (`vault`,
  `council`, `skills`) to canonical `.jarvis/` locations.
- `models/records.py` — `MemoryRecord` (id, kind, content, tags, source,
  status, importance, provenance, timestamps, links) with typed validation;
  `ValidationError` for any malformed input.
- `validation/` — `load_document()` / `load_all()` parse frontmatter into
  typed `LoadedDocument`s and enforce required fields, duplicate IDs,
  allowed statuses, and broken reference checks.
- `context/` — `ContextBuilder` assembles the ordered prompt context
  (`platform → constitution → system → world_model → memory → skills →
  task → persona → user`; index 0 = highest). Lower layers never override
  higher ones — `apply_override(caller=...)` raises `CONTEXT_ERROR` on a
  priority violation. Assembly is deterministic.
- `errors/` — typed, inspectable errors (`JarvisError` hierarchy, codes,
  structured `.to_dict()`); never silent repair.

### P3b — Sandboxed terminal skill ✅

Executes user-authorized shell commands with the kernel's authority model:

- `exec/safe.py` — `safe_exec()` returns a typed `OperationResult`; guards
  run before any shell: blocklist-first (dangerous prefixes refused),
  cwd pinned inside workspace (`CWD_ESCAPE`), timeout (`TIMEOUT`),
  stdout/stderr size caps (`STDOUT_TRUNCATED`/`STDERR_TRUNCATED`),
  authority required (`terminal: execute`).
- `.jarvis/skills/terminal/` — manifest + impl wiring the P3b engine as a
  JARVIS skill (`terminal=execute` permission; scans `active`).
- 6 guard tests: no-authority, blocklist-before-shell, cwd escape, benign
  run, timeout, output cap.

### P4 — Web reader (controlled HTTP) ✅

Server-side bounded `fetch` with guards that run **before** any connect:

- `io/http_client.py` — `HttpClient.fetch()` requires `network.read`
  authority (`PermissionError` otherwise); rejects non-http(s) schemes
  (`SCHEME_BLOCKED`), IPv4 literals / loopback/link-local (`SSRF_BLOCKED`),
  non-standard ports (`PORT_BLOCKED`), redirect loops (`TOO_MANY_REDIRECTS`),
  missing host (`BAD_URL`); caps response size.
- `skill run web` + `jarvis web` both invoke it; manifest declares
  `network: read, filesystem: none, terminal: none`.
- 6 guard tests: authority gate, IPv4 block, scheme block, port block,
  redirect cap, missing host.

### P5 — Web crawl (structured traversal) ✅

Crawls web pages starting from a seed URL, respecting depth, domain, and
robots.txt. Each fetched page is stored as a markdown file in
`vault/semantic/` with frontmatter (source URL, fetch timestamp, depth,
content type) and a deterministic URL-hash filename.

- `src/jarvis/crawl/crawler.py` — `Crawler`: breadth-first,
  depth-limited (`max_depth`), page-limited (`max_pages`), domain-locked
  (`stay_on_domain`), robots.txt respect (`obey_robots`), URL dedupe
  (`visited`), per-domain robots cache. Fetch reuses the P4 guard set
  (via `HttpClient`); the write boundary is enforced against the
  authority scope (`MUTATION_DENIED` if out of scope).
- Skill manifest `.jarvis/skills/web_crawl/` declares
  `network: read, filesystem: write`; the wrapper adapts params to the
  tracked `Crawler` engine.
- 11 tests in `tests/test_phase10_crawl.py` — depth limit, domain lock,
  robots respected/optional, dedupe, max-pages, write gate, invalid seed,
  frontmatter output, URL normalization. The fetch layer is injected
  (deterministic fake HTTP client); the real P4 guards are covered by
  `test_phase10_web_exec.py`. Loopback SSRF is deliberately blocked by
  design (no production vulnerability), so crawl tests avoid real network.

### P6 — GitHub skill importer ✅

- `src/jarvis/skills/import_github.py` — full pipeline: DISCOVER (GitHub
  API tree scan for `skill.md`) → INSPECT (fetch + parse manifest with the
  P2 parser) → VALIDATE (required fields + permissions mapping) → ISOLATE
  (copies only manifest + entry into `.jarvis/skills/<name>/`, never
  overwrites, never executes remote code) → ADAPT (best-effort `$REPO`
  rewrite) → TEST (manifest reloads) → INTEGRATE (registry rebuilt).
- Human approval gate: imports default to `needs-approval`; permissions
  are surfaced in the report, nothing is auto-granted.
- 10 tests in `tests/test_phase10_p6.py`: manifest parse/validate, tree
  discovery, no-manifest rejection, bad-manifest rejection, $REPO adapt,
  approval gate (nothing installed without approval), approved install,
  overwrite refusal. All network is monkeypatched — hermetic.

## Planned

### P7 — Self-learn

- Post-task review → `vault/failures/` + `vault/procedural/`, dedupe
  heuristic.

### P8 — Self-adaptation

- Correction/preference detection → `vault/semantic/preferences.md`;
  supersede not ghost.

### P9 — Self-evolution

- Propose diff → structure check + pytest → show diff → on approval apply +
  commit + push; no silent edits, rollback = `git revert`.

### P11 — Autonomy + governance

- Global permission gates, confirmation dialogs, full audit log, eval
  harness.

## Principles

1. **Canonical vs derived.** Vault notes are canonical. `learn/`, registry,
   indexes, summaries are derived — always rebuildable, never authoritative.
2. **Provenance.** Every important memory answers "why do I believe this?"
   with a resolvable chain.
3. **Authority ≠ confidence.** Who may act on a note (authority) is orthogonal
   to how likely it is correct (confidence).
4. **Lifecycle over deletion.** Knowledge is archived (phases), not destroyed.
5. **Deterministic kernel.** The runtime resolves, reads, validates, and
   assembles the same inputs to the same outputs; every failure is a typed,
   inspectable error.
6. **Dependency chain.**

```
P1 Memory ──┬──► P7 Self-Learn ──► P8 Self-Adapt
            └──► P2 Skills ──┬──► P3 Terminal ──────┐
                             └──► P4 Web ──► P5 Crawl / P6 GitHub ──► P9 Self-Evolve
P3 + P6 + P1 ───────────────────────────────────────────────────────► P9 ──► P10 Kernel ──► P11
```