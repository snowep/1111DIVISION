# Sandbox Structure — D:/Project/1111DIVISION

This repository **is** the sandbox. Everything lives in a prescribed location.
Structure is enforced by `scripts/check_structure.py` (must exit 0 before any
commit) and guarded by `tests/test_structure.py`.

## Layout

```
D:/Project/1111DIVISION/
├── README.md             front door — product summary
├── pyproject.toml        package metadata + pytest config
├── .gitignore            ignore rules
├── docs/                 documentation — Markdown only
│   ├── README.md
│   ├── STRUCTURE.md      (this file — canonical structure statement)
│   └── ROADMAP.md        (development roadmap + decisions of record)
├── scripts/              operational scripts — no application code
│   ├── README.md
│   └── check_structure.py
├── app/                  the JS/Node application (NIM bridge + React/MUI UI)
│   ├── README.md
│   ├── server/           zero-dependency Node bridge (keeps NIM key server-side)
│   └── ui/               Vite + React + Material UI chat
├── src/                  implementation — the `jarvis` Python package
│   └── jarvis/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── docstore/     canonical document store (frontmatter Markdown CRUD)
│       ├── learn/        derived knowledge — always rebuildable from docstore
│       ├── memory/       P1: vault memory (routing, provenance, phases, observe)
│       └── skills/       P2: skill manager (manifest, permissions, registry)
├── tests/                pytest suite — mirrors src/ one level deep
│   ├── conftest.py
│   ├── test_*.py
│   └── ...
└── .jarvis/              RUNTIME STATE — gitignored, never committed
    ├── vault/            canonical documents (the source of truth)
    │   ├── episodic/
    │   ├── semantic/
    │   ├── procedural/
    │   ├── decisions/
    │   └── learned/
    ├── skills/           skill definitions (skill.md manifests + impl)
    │   └── registry.md   DERIVED — rebuilt on scan, never hand-edited
    └── learn/            derived artifacts (always rebuilt from vault/)
```

## Rules

| # | Rule |
|---|------|
| R1 | **Canonical vs derived.** `.jarvis/vault/` is canonical. `.jarvis/learn/` and `.jarvis/skills/registry.*` are derived — always rebuilt from canonical sources, never edited by hand, never treated as authoritative. |
| R2 | **Isolation.** All runtime data lives under `.jarvis/`. It is gitignored and never becomes repo truth. |
| R3 | **One purpose per directory.** `src/jarvis` = Python application code; `app/` = JS/Node application code; `tests/` = tests only; `docs/` = Markdown only; `scripts/` = operational scripts only. |
| R4 | **No stray files.** Repo root allows exactly `README.md`, `pyproject.toml`, `.gitignore`, and the directories `docs/ scripts/ src/ tests/ app/`. No probe files, no scratch `.py`/`.js` files, no one-off scripts at the root. |
| R5 | **Every directory has a README.md** stating its purpose. |
| R6 | **Everything important is a document.** Decisions are written down before they are acted on. (`docs/ROADMAP.md` is the decision record.) |
| R7 | **Verification before commit.** `python scripts/check_structure.py` exits 0 **and** `python -m pytest -q` passes, or nothing is committed. |

## Enforcement

```bash
python scripts/check_structure.py   # exit 0 = conforms, non-zero = violates
python -m pytest -q                 # includes tests/test_structure.py
```