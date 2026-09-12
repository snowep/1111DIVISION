# app/

The **JS/Node application** — the user-facing interface and the bridge to the
LLM. This directory is one of the repo's top-level contract directories
(`app/` per `docs/STRUCTURE.md` R3/R4).

```
app/
├── server/            zero-dependency Node bridge
│   ├── server.js      /api/health + /api/chat (streams NIM SSE, auto-routing)
│   ├── fsroom.js      sandboxed read-only filesystem layer (FS_ROOT)
│   ├── package.json
│   └── .env.example   copy to .env, add NIM_API_KEY (+ optional FS_ROOT)
└── ui/                Vite + React + Material UI chat
    ├── src/App.jsx    chat + workspace file browser (drawer)
    └── vite.config.js proxies /api -> :3001
```

## Filesystem access (workspace)

Set `FS_ROOT` in `server/.env` to a folder JARVIS may read:

```
FS_ROOT=D:\path\to\your\folder
```

The bridge exposes a **read-only** sandbox:

- `GET /api/fs/root` — sandbox status
- `GET /api/fs/list?path=` — list a directory
- `GET /api/fs/read?path=` — read a text file (256 KiB cap, binary-safe)

Security: traversal impossible (realpath re-check defeats symlinks/junctions),
secrets (`.env`, `*.pem`, `*.key`…) are blocked, node_modules/.git noise is
hidden. No write/move/delete exists.

In the UI, the folder icon opens the **Workspace** drawer. Click a file to
attach it — it inserts `@file(rel/path)` into the input. On send, the bridge
expands that into the file's content (as a `<file …>` block) so the model
actually reads it. Attached chips appear on the user's message.

## Model auto-routing

`NIM_MODEL` + `NIM_FALLBACK_MODELS` (comma-separated) form an ordered chain.
If a model is unavailable (404/network fail), the bridge retries the same
request on the next model. A `meta` SSE event tells the UI which model served.
`NIM_ROUTER=off` disables it. `/api/health` reports per-model availability.

Rules: **no Python files** in `app/` (enforced). The Python side lives in
`src/`; the JS/Node side lives here. Everything under `app/` is application
code — operational scripts belong in `scripts/`.

See the repo [`README.md`](../README.md) for run instructions.