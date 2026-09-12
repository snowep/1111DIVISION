# app/

The **JS/Node application** — the user-facing interface and the bridge to the
LLM. This directory is one of the repo's top-level contract directories
(`app/` per `docs/STRUCTURE.md` R3/R4).

```
app/
├── server/            zero-dependency Node bridge
│   ├── server.js      /api/health + /api/chat (streams NIM SSE)
│   ├── package.json
│   └── .env.example   copy to .env, add NIM_API_KEY
└── ui/                Vite + React + Material UI chat
    ├── src/App.jsx    one chat screen
    └── vite.config.js proxies /api -> :3001
```

Rules: **no Python files** in `app/` (enforced). The Python side lives in
`src/`; the JS/Node side lives here. Everything under `app/` is application
code — operational scripts belong in `scripts/`.

See the repo [`README.md`](../README.md) for run instructions.