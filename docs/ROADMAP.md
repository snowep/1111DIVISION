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
| P5 | Web crawl (structured traversal) | 🔲 Next |
| P6 | GitHub skill importer | 🔲 |
| P7 | Self-learn (lesson consolidation) | 🔲 |
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
  structured lessons (wrong assumption, corrected understanding) stored as
  `kind: learned` notes.

### P10 — Deterministic runtime kernel ✅

The kernel is the deterministic, inspectable substrate the intelligence
layer (JARVIS in Open WebUI) runs on. Everything is pure Python over the
existing Markdown architecture — no vector search, no web UI, no autonomous
execution, no LLM-as-authority:

- `errors/` — typed, inspectable error hierarchy with stable `code` values
  (`PATH_ESCAPE`, `MISSING_FIELD`, `DUPLICATE_ID`, `INVALID_STATUS`,
  `BROKEN_REF`, `MUTATION_DENIED`, `CORRUPT_STATE`, `IDENTITY_ERROR`, ...).
  The kernel **never silently repairs corrupted state** — it raises.
- `models/` — `OperationResult` (success, operation_id, data, warnings,
  errors, provenance) returned by every kernel operation; deterministic
  serialization.
- `runtime/` — `resolve_root()` finds the canonical workspace root
  (explicit arg → `JARVIS_ROOT` env → walk up from cwd to `.jarvis/`);
  `build_runtime()` constructs the full `Runtime` (roots + resolver + io +
  identity) eagerly, failing fast with a typed error.
- `io/` — `WorkspaceResolver` (safe path resolution: traversal, absolute
  paths, symlink/UNC escapes blocked; semantic aliases `vault/ council/
  skills/ core/ learn/` resolve to their canonical `.jarvis/` locations)
  and `SafeIO` (reads always allowed; **writes require an `Authority`
  in-scope or raise `MUTATION_DENIED`**).
- `core/` — `load_identity()` reads identity **only from `.jarvis/core`
  (identity.json or identity.md)**. Open WebUI config / env vars are never
  an identity source.
- `validation/` — `load_document()` / `load_all()` parse frontmatter into
  typed `LoadedDocument`s and enforce required fields, duplicate IDs,
  allowed statuses, and broken reference checks.
- `context/` — `ContextBuilder` assembles the ordered prompt context
  (`platform → constitution → system → world_model → memory → skills →
  task → persona → user`; index 0 = highest). Lower layers never override
  higher ones — `apply_override(caller=...)` raises `CONTEXT_ERROR` on a
  priority violation. Assembly is deterministic.

### P3b — Sandboxed terminal skill

- `jarvis/exec/safe.py` — `safe_exec()`: blocklist-first (dangerous
  prefixes refused before any shell), cwd pinned inside workspace
  (else `CWD_ESCAPE`), timeout (else `TIMEOUT`), stdout/stderr size caps
  (`STDOUT_TRUNCATED`/`STDERR_TRUNCATED`), requires an `Authority`
  granting `terminal: execute` (else `PermissionError`). Deterministic
  `ExecResult` (success, returncode, stdout, stderr, warnings, blocked,
  duration_ms) + `to_dict()`.
- `.jarvis/skills/terminal/` — manifest + impl wiring the P3b engine as a
  JARVIS skill (`terminal=execute` permission; scans `active`).

### P4 — Web reader (controlled HTTP)

- `jarvis/io/http_client.py` — stdlib-only bounded fetch: http/https only
  (`SCHEME_BLOCKED`), IPv4 private/reserved literal block (`SSRF_BLOCKED`),
  blocked ports (`PORT_BLOCKED`), redirect-count cap (`TOO_MANY_REDIRECTS`),
  response size cap, missing-host guard (`BAD_URL`). Requires `network:
  read` authority (else `PermissionError`). No external deps.
- `.jarvis/skills/web/skill.md` — manifest (`network=read`); impl follows
  in the skill wrapper.

### P3b — Sandboxed terminal skill ✅

Executes user-authorized shell commands with the kernel's authority model:

- `exec/safe.py` — `safe_exec()` returns a typed `OperationResult`; guards
  run **before** any shell: blocklist-first (`rm -rf`, `sudo`, `dd`, `shutdown`…),
  cwd pinned inside the workspace (`CWD_ESCAPE`), timeout (`TIMEOUT`),
  output cap (`STDOUT_TRUNCATED`). No authority → `PermissionError`.
- `skill run terminal` + `jarvis exec` both invoke it; the skill manifest
  declares `terminal: execute, filesystem: read, network: none`.
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

## Planned

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

### P11 — Autonomy + governance

- Global permission gates, confirmation dialogs, full audit log, eval harness.

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

---

*Updated: 2026-09-13 — P1+P2+P3+P10+P3b+P4 implemented.*