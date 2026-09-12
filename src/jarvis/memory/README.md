# memory/

Obsidian-compatible long-term memory built on the docstore.

- `constants.py` — phases, routing matrix, transitions (no circular imports).
- `engine.py` — routing, `remember()`, phase transitions, `list_active()`,
  `forget_expired()`, provenance chains.
- `observe.py` — heuristic transcript → vault routing pass (proposal stage).

See `docs/ROADMAP.md` (P1) for design decisions.