# Web UI Command Gateway — Design & Proposal

- **Status:** Proposal (needs `evolve check` → your review → `evolve apply`)
- **Constraint lifted:** "no web UI execution surface" (previously a hard design rule). This is a **deliberate**, scoped lift. The runtime (`src/`) remains the sole authority; the web gateway is an **input/output channel**, never a trust boundary.
- **Scope of this doc:** architecture, security model, endpoints, approval gates, and a concrete change proposal. **No code is written yet.** This is the design you review before any `evolve apply`.

---

## 1. What problem this solves

Currently the **full P1–P10 loop** (memory, skills, terminal, web reader, crawl, GitHub import, self-evolution) is reachable **only from the CLI / Python API**. The web layer (`app/`) is deliberately read-only:

- chat → LLM (SSE, auto-routing)
- workspace file browser → read-only sandbox (`fsroom.js`), traversal-proof, secrets-blocked
- no command execution, no write, no approval flow

That means a user living in the browser **cannot** run `crawl`, `exec`, `import-gh`, `evolve`, `skill run`, or verify/supersede memory. The purpose of this gateway is to bring the **whole loop** into the web UI — **without weakening the runtime's authority model**, and without turning the browser into a blind RCE surface.

---

## 2. Non-negotiable constraints (inherited from the architecture)

These are **not** relaxed by this proposal:

| Constraint | Why it holds |
|---|---|
| **Identity comes ONLY from `.jarvis/core/`** (`core/identity.py`). Never from web config, env, or the browser. | Identity is repo truth; the gateway **reads** it, never overrides it. **Verified: this repo currently has NO `.jarvis/core/` — `build_runtime()` raises `IdentityError` until it is seeded (see §7.1).** |
| **No Python in `app/`** (structure rule R3). | `app/` = JS/Node only. The gateway runs in Node; it talks to the Python runtime over a **subprocess bridge** (`jarvis` CLI), not by importing Python. |
| **Authority ≠ confidence.** | Who may act (authority) stays orthogonal to how likely true (confidence). The gateway carries *authority* grants; it never recomputes *confidence*. |
| **Read-only by default.** | Every command that can mutate requires an explicit, logged authority path. The gateway never grants write implicitly. |
| **No LLM as authority.** | The LLM may *suggest* an action; only the user (via the approval gate) may *authorize* it. |
| **Deterministic kernel.** | `build_runtime()` resolves/reads/validates identically every time. The gateway calls this same kernel; it adds no magic. |
| **No invented data.** | Every response is an `OperationResult` (typed, inspectable, with `operation_id` + provenance). The gateway never fabricates a result. |
| **Full audit.** | Every web-originated mutation writes an audit event (actor ⇒ `user` via web session). Consistency with the event-sourced audit model. |

---

## 3. Architecture

### 3.1 What stays

```
app/server/server.js          (unchanged — chat + fsroom bridge)
app/ui/                       (unchanged — chat + workspace drawer)
src/jarvis/                   (unchanged — the runtime, the only authority)
```

### 3.2 What gets added

```
app/server/gateway.js          NEW — the command gateway (zero-dependency Node)
app/server/gateway-auth.js     NEW — session auth, CSRF origin check, rate limit
app/server/gateway-runner.js   NEW — spawns `python -m jarvis` subprocess
app/server/gateway-store.js    NEW — in-memory approval tokens + audit forwarding
app/server/gateway-ops.js      NEW — allowlist + permission mapper (command → Authority)
app/server/server.js           MODIFIED — mount `/api/gateway/*` (and gate behind auth)
app/server/server.test.js      NEW — Node-side tests (auth, allowlist, subprocess errors)
src/jarvis/audit/              NEW (Python) — event-sourced audit writer (EVT-*)
                                  consumed by the gateway for provenance/audit
tests/test_gateway_subprocess.py  NEW (Python) — hermetic subprocess bridge tests
app/ui/                        MODIFIED — Command panel: form → approval chip → run
```

The gateway is a **new directory of Node modules** under `app/server/` (R3-compliant: it is JS/Node application code, no Python).

### 3.3 The trust diagram

```
Browser (untrusted)
   │  HTTPS + session token + origin check
   ▼
gateway.js  (thin, zero-dependency, nothing imports Python)
   │  maps command → {command, args, required Authority}
   │  allowlist check → permission mapper → approval gate
   ▼
gateway-runner.js  (spawns `python -m jarvis <subcommand>`)
   │  passes the *validated* argv only
   ▼
Python runtime (src/jarvis — THE authority)
   │  resolves paths, bounds IO, checks Authority, runs the op
   ▼
OperationResult (typed, with operation_id + provenance)
   ▼
audit (event-sourced, actor=user-via-web) + response back to browser
```

The **browser never passes raw shell**. The gateway only accepts **allowlisted, structured subcommands**; everything else is refused before any process spawn.

---

## 4. Security model

### 4.1 The gateway is a **command gateway, not a terminal emulator**

It does **not** expose `exec` as "type any shell command." It exposes **allowlisted subcommands** with **typed parameters**, each mapping to a required `Authority`. This is the single most important design decision: **it keeps the browser one level removed from the shell.**

### 4.2 Command surface (allowlist)

| Command | Args (typed) | Required Authority | Approve needed? | Notes |
|---|---|---|---|---|
| `status` / `list` / `read` | kind/path | **read** (identity) | no | read-only |
| `learn` | — | **identity** (rebuild derived; canonical untouched) | no | deterministic |
| `remember` | text, kind, tags, confidence | **memory.write** | **yes** (create) | goes through `verify` later |
| `verify` / `supersede` | path, reason | **memory.write** | **yes** (state change) | provenance recorded |
| `forget` | — (dry-run flag) | **memory.write** | **yes** when not dry-run | archives, never deletes |
| `skill scan` / `skill list` | — | read | no | registry rebuild is derived |
| `skill run <name>` | name, params | **skill's manifest permissions** | **yes** if the skill requests any write/execute/network | **requires the missing `check_permission` fix** (see §6.3) |
| `exec <command>` | command, timeout, cwd | **terminal.execute** + workspace pinning | **yes** (high risk) | blocklist + output cap + workspace-confined — as in `safe_exec` |
| `web <url>` | url | **network.read** | no | SSRF/port/size guards already server-side |
| `crawl <seed>` | seed, depth, pages, robots, domain | **network.read + filesystem.write** | **yes** (writes to vault) | bounded crawl |
| `import-gh <repo>` | repo, token | **network.read + filesystem.write** | **yes** (two-step: inspect → approve install) | never executes remote code |
| `evolve check` | title, desc, changes | read (proposal only) | no | pure validation on scratch mirror |
| `evolve apply` | title, desc, changes, **--approve** | **filesystem.write + git authority** | **yes** (double gate: `--approve` + web approval) | never silent |
| `evolve revert` | commit | **git authority** | **yes** | reversible history |
| `seed` | — | **memory.write** | no (creates placeholders) | dev-only, keep off in prod |

Everything **not** on this list → `404 {"error":"command not allowed"}` with an audit event.

### 4.3 Approval gate

Writing/executing commands require a **two-factor-style approval**, not just the HTTP request:

1. **Pre-flight** — gateway computes the required `Authority` + risk class (read-only / low-write / high-write / execute / network-write / git).
2. **Approval token** — a short-lived, single-use token (UUID, TTL ~120s, bound to the session + the exact command+args hash) is created and returned to the browser.
3. **The browser must POST the approval token back** with the same command+args. The gateway re-checks the token (session-bound, single-use, hash-match, TTL) **before** spawning anything.
4. **Dry-run preview** where available (e.g. `evolve check`, `forget --dry-run`).

This means an accidental button click, a CSRF'd request, or a stolen session **cannot** trigger a write/execute silently: it must confirm a fresh, session-bound token for that exact command.

### 4.4 Sessions & transport

- **No cookies** (avoids CSRF-by-cookie entirely). **Bearer token** in `Authorization: Bearer <token>`.
- Token minted at login (or by an operator-provided env `JARVIS_WEB_TOKEN`), stored **hashed** server-side.
- **Origin check** on every request (`req.headers.origin` must equal the configured `JARVIS_WEB_ORIGIN`); mismatches are rejected pre-route.
- **Rate limit** (e.g. 60 req/min per token; stricter on `exec`/`apply`).
- **HTTPS required** in production; no auth keys in the browser.
- All of this is **zero-dependency** (Node built-in `crypto`/`http`), consistent with the existing bridge.

### 4.5 Risk classes & who may authorize

| Risk class | Example | Required to approve |
|---|---|---|
| `readonly` | `status`, `list`, `read`, `learn`, `skill list` | none |
| `low_write` | `remember` | user |
| `state_change` | `verify`, `supersede`, `forget` | user |
| `execute` | `exec` | user, with visible command + workspace pinning |
| `network_write` | `crawl`, `import-gh` | user (two-step for import) |
| `git` | `evolve apply`, `evolve revert` | user, **with `--approve` in the payload** (double gate) |

There is **no auto-approval** for anything beyond read-only. No "remember my choice for 10 minutes."

### 4.6 No LLM authority

The gateway's `/api/gateway` is **not** an LLM endpoint. A "suggest a command" flow may exist **only** as a separate, clearly-labeled chat suggestion — the user still clicks the command + approvals themselves. The model never holds an approval token.

---

## 5. API (what the UI calls)

All under `/api/gateway/*`, JSON in/out. `OperationResult` is the response envelope for every command:

```ts
interface GatewayResponse {
  success: boolean
  operation: string      // e.g. "crawl"
  operation_id: string   // stable, audit-linked
  data: any              // typed payload
  warnings: string[]
  errors: { code: string; message: string }[]
  provenance: { ... }    // type/source/session_id/message_id/based_on
}
```

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/api/gateway/commands` | GET | Bearer | list allowlisted commands + required Authority (drives the UI) |
| `/api/gateway/run` | POST | Bearer + origin + rate-limit | pre-flight, then run **read-only** ops; returns result |
| `/api/gateway/run/approve` | POST | Bearer + origin | returns an approval token for a write/execute op (preview/dry-run first) |
| `/api/gateway/run/confirm` | POST | Bearer + origin + **token** | executes the same op with the matching token; single-use |
| `/api/gateway/audit` | GET | Bearer (admin) | recent audit events (EVT-*) from the web session |
| `/api/gateway/auth/info` | GET | Bearer | current identity (from `.jarvis/core`, never the browser) + granted surface |

The `confirm` endpoint is the ONLY path that can trigger a write/execute mutation. Read-only ops never need `confirm`.

---

## 6. Mapping to the existing code (what changes where)

### 6.1 New Node modules (`app/server/`)

- `gateway.js` — route mounting, allowlist dispatch, `OperationResult` envelope.
- `gateway-auth.js` — Bearer token (hashed), origin check, rate limit, approval-token generation/validation (single-use, TTL, hash-bound).
- `gateway-runner.js` — spawns `python -m jarvis <allowlisted subcommand>` with argv built only from validated typed inputs; parses stdout JSON → `OperationResult`; captures non-JSON errors as typed errors.
- `gateway-store.js` — in-memory approval tokens (TTL + single-use) + forwarding of audit events to the Python audit writer.
- `gateway-ops.js` — the allowlist table (command → args schema → required Authority → risk class). This is the **single source of truth** for what the browser may do.
- `server.test.js` — tests: unknown command refused, missing token refused, origin mismatch refused, approval token single-use, subprocess error → typed error, no raw shell passthrough.

### 6.2 New Python modules (`src/jarvis/audit/`)

- `writer.py` — event-sourced append-only audit (event_id `EVT-<ts>-<seq>`, actor, action, target, from_status, to_status, reason, provenance). Actor enum includes `user` (web-via-user), `tool`, `system`, `jarvis`, `external`, `automation`, `council`.
- `README.md` — the audit spec (already exists conceptually; wire the writer).
- This becomes the **source the gateway's `/api/gateway/audit` reads**, and the durable trail for every web-originated mutation.

### 6.3 Required fix in `src/jarvis/cli.py` (finding surfaced during design)

`skill run` currently does **not** call `check_permission()` before executing `impl.py` — the permission helper exists but is not wired into the CLI path. The gateway must not make this worse by adding a web path that also skips the check.

**Proposal includes:** wire `check_permission()` into `_cmd_skill` (and the new audit writer) so `skill run` honors manifest permissions exactly as documented. This is a small, safe, correctness fix already implied by P2; the gateway then inherits the enforcement.

### 6.4 `app/ui/` (Vite + React + MUI)

A **Command panel** (drawer/section) that:

1. lists allowlisted commands from `/api/gateway/commands`,
2. renders a typed form per command (validates locally + mirrors server schema),
3. for write/execute commands, shows the **risk class + required Authority** and the approval preview,
4. calls `run/approve` → then `run/confirm` with the token (single-use),
5. streams results as `OperationResult` (errors parsed as typed, not raw text),
6. shows the audit trail in a side "Events" view.

This is standard React state — no new dependencies, no web sockets, no polling loops beyond what the chat flow already does.

### 6.5 Bootstrap prerequisite (verified gap — must land before anything else)

**Current state (verified 2026-09-13):** `build_runtime()` fails with
`IdentityError: core directory missing: D:\Project\1111DIVISION\.jarvis\core`
because `.jarvis/` has no `core/` directory. The gateway's kernel path
(`build_runtime()`) cannot boot until identity exists in `.jarvis/core/`.

`.jarvis/` is **gitignored** (R2 — runtime state never committed), so seeding
it is a **local, per-machine step** (like `FS_ROOT` / `.env`), not a repo
change. The seed creates:

```
.jarvis/core/
  identity.md      # YAML-subset frontmatter: name, role, version,
                   # capabilities[] — the canonical identity
  constitution.md  # optional: reference to docs/ … (or the canonical
                   # constitution if you keep one in .jarvis/core)
  platform.md      # description of the host layer (Open WebUI + app/),
                   # explicitly NOT the identity source
  system.md        # system-level notes (optional)
```

`load_identity()` accepts `core/identity.json` **or** `core/identity.md`
(YAML-subset frontmatter). Either works; the `.md` form is Obsidian-native
and matches the repo's Markdown-everything ethos. The gateway's
`/api/gateway/auth/info` endpoint reads this file — it never accepts identity
from the browser or Open WebUI.

**Proposal includes:** a `scripts/seed_identity.py` (operational script,
not app code) that writes the canonical `identity.md` into `.jarvis/core/`
with the name/role/version you specify inline (e.g. your chosen JARVIS
identity). This is step 0 of the rollout (§8) and is required before `evolve
apply` can run any kernel-dependent test.

### 6.6 What is explicitly NOT built

- ❌ A generic terminal/console in the browser.
- ❌ Running Python in the browser or importing `src/` into Node.
- ❌ Any auto-approval, stored credentials in the browser, or cookie-based auth.
- ❌ Any path that lets the LLM approve or execute a command.
- ❌ Any data flow where the gateway "invents" a result (everything is a real `OperationResult` from the runtime).

---

## 7. Testing strategy

| Layer | Test | Coverage |
|---|---|---|
| Node | `server.test.js` | allowlist refusal, auth (no token / bad token / expired token / origin mismatch / rate limit), approval token single-use + hash-bound, subprocess error → typed error, **no raw-shell passthrough** |
| Python | `tests/test_gateway_subprocess.py` | hermetic: gateway-runner argv building from typed inputs is deterministic; unknown command → `404`-style typed error; `OperationResult` envelope round-trips |
| Python | `tests/test_audit_writer.py` | event format, actor enum, append-only, provenance carried on every event |
| Integration | `tests/test_phase10_gateway.py` | a real `python -m jarvis status` over the subprocess bridge returns typed JSON; a gated op without token is refused **before** spawn; approval token is single-use |
| Structure | `check_structure.py` + `test_structure.py` | R3 holds: no Python in `app/`, no JS in `src/` |

---

## 8. Rollout / sequencing (proposal phases)

| Step | Deliverable | Gate |
|---|---|---|
| 0 | **`scripts/seed_identity.py` + local `.jarvis/core/` seed** (verified requirement — kernel cannot boot without it) | manual + `pytest -q` |
| 1 | `audit/` writer (Python) + tests | `pytest -q` + structure gate |
| 2 | `cli.py` `skill run` permission fix + test | same |
| 3 | `gateway-ops.js` allowlist + `gateway-auth.js` + `gateway-runner.js` + `server.test.js` | Node tests + manual |
| 4 | mount `/api/gateway/*` in `server.js` behind auth | integration |
| 5 | `app/ui/` Command panel (run/approve/confirm flow) | manual + CI |
| 6 | docs: `GATEWAY.md` → future `docs/ARCHITECTURE.md` | structure gate |

Each step is independently testable and reversible (`evolve revert`). No step mutates the canonical vault or the repo tree outside its own changes.

---

## 9. Known risks & mitigations

| Risk | Mitigation |
|---|---|
| Browser session compromise → RCE | No raw shell; allowlist + typed args → subprocess; approval token single-use + hash-bound; no cookie/SHIRO-style auth; no stored creds |
| CSRF | No cookies; Bearer token; origin check on every request |
| Skill with malicious `impl.py` | `check_permission` wired into `skill run` (fix in 6.3); skills are untrusted content until user approves their permission request |
| `exec` accident | blocklist + workspace pinning + output cap (already in `safe_exec`); web requires explicit approval token + visible command |
| LLM overreach | `/api/gateway` has no LLM path; suggestions are separate, never authorized |
| Token theft | TTL ~120s, single-use, bound to session+command hash; audit every non-readonly event |
| Log/audit integrity | event-sourced append-only (EVT-*), provenance on every event, actor consistently `user`-via-web |

---

## 10. What I need from you

1. **Approve the constraint lift** (web execution surface) — the rest of the design hangs off this.
2. **Decide the port / exposure** — `app/server` already listens on `:3001`; the gateway mounts on the same server (no new port), or you may want a separate `GATEWAY_PORT`.
3. **Decide on `evolve` sequencing** — Table in §8 is the suggested order; if you want fewer steps, I can collapse 3–4 into one change.
4. **Confirm the skill-permission fix** (§6.3) is in scope — I recommend yes; it is a pre-existing gap the gateway would otherwise inherit.
5. **Pick the audience** — is this localhost-only (default) or intended to be reachable on a LAN? That changes the auth posture (localhost can default to an env token; anything reachable must enforce HTTPS + strict origin + rate limits).

---

## Appendix A — Why not just "expose the CLI in the browser"?

Naive approaches fail the architecture's own rules:

- **Serving a raw terminal** would bypass the allowlist, the structured `Authority`, and the audit trail.
- **Importing Python into Node** violates R3 and the zero-dependency bridge.
- **Auto-approving from the browser** would turn a stolen session into remote execution.
- **Letting the LLM decide** violates "no LLM as authority."

The gateway design above is the *minimal* structure that keeps every existing rule intact while adding the missing command surface. The runtime stays the only authorizing layer; the web becomes a **well-formed remote for it**, not a bypass.

---

## Appendix B — Decision record (proposal)

| Field | Value |
|---|---|
| Decision | Add a web UI command gateway as a deliberate constraint-lift (execution surface) |
| Date | 2026-09-13 |
| Status | **Proposal** — needs `evolve check` + user approval before any code |
| Options | (a) No web command surface (status quo) — safest; (b) allowlisted gateway per this doc — proposed; (c) full terminal emulator — rejected (RCE surface, violates authority model) |
| Reason | Bring the full P1–P10 loop into the browser without weakening the runtime's authority model |
| Trade-offs | + browser access to the whole loop; + audit trail for web actions; + skill-permission fix lands; − new attack surface (mitigated by allowlist+token+origin); − no raw-terminal convenience |
| Consequences | Runtime stays the sole authority; web is an input channel; all web mutations are audited; `app/` stays JS-only |