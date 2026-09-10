# How JARVIS Works

## Architecture
- `.jarvis/` — system brain (identity, memory, capabilities, state)
- `vault/` — shared knowledge surface (Obsidian)
- `src/`, `tests/`, `scripts/` — code

## Two Surfaces
- **vault/** — Obsidian shared knowledge surface. Human and JARVIS both read/write. This is the shared long-term memory.
- **.jarvis/** — JARVIS's private system brain. Identity, memory, capabilities, state.

## File System
- Wikilinks for dynamic cross-references
- One file = one job
- No data in two places

## Memory
- .jarvis/memory/ — persistent lessons, decisions, user preferences (JARVIS internal)
- vault/ — structured knowledge, projects, research (shared, human-editable)
