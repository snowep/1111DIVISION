# src/jarvis — implementation

Python package for JARVIS: a deterministic Markdown-based personal
intelligence operating system.

| Module | Purpose |
|---|---|
| `errors/` | typed, inspectable error hierarchy |
| `models/` | normalized runtime payloads (`OperationResult`) |
| `runtime/` | kernel bootstrap — roots, Runtime, build_runtime() |
| `core/` | identity loaded only from `.jarvis/core` |
| `io/` | safe path resolution + authority-bounded read/write |
| `validation/` | frontmatter-typed loading + integrity checks |
| `context/` | deterministic context assembly with priority ordering |
| `docstore/` | canonical Markdown CRUD (vault) |
| `memory/` | P1 vault memory (routing, provenance, phases, filter, critique) |
| `skills/` | P2 skill manager (manifest, permissions, registry) |
| `learn/` | derived knowledge, always rebuildable |

See `docs/ROADMAP.md` for the phase-by-phase record.