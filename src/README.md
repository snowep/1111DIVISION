# src/

Implementation — the `jarvis` Python package. No runtime data lives here;
all data belongs under `.jarvis/` at the repo root.

```
src/jarvis/
├── __init__.py
├── __main__.py      python -m jarvis entry point
├── cli.py           new | list | read | edit | delete | learn | seed
├── docstore/        canonical document store (frontmatter Markdown CRUD)
└── learn/           derived knowledge — always rebuildable from docstore
```

Rules: no stray files at `src/` root; modules import only within the
package; tests live in `tests/`, never here.