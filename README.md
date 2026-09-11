# JARVIS — minimal Markdown data manager

A deliberately small starting point. JARVIS manages your data in an **isolated
folder** (`.jarvis/` by default) as plain Markdown files with frontmatter.
It can perform CRUD, and it *learns* by deterministically rebuilding derived
knowledge from the canonical documents.

## Layout

```
.jarvis/                <- isolated data folder (gitignored)
  notes/                <- canonical documents (the source of truth)
    <kind>/<id>.md      <- one document per file, with frontmatter
  learn/                <- DERIVED, always rebuildable from notes/
    index.json          <- machine-readable inventory
    lessons.md          <- human-readable summary + extracted lessons
src/jarvis/             <- minimal implementation (no external deps)
tests/                  <- pytest suite
```

A document is a Markdown file with `---` frontmatter and a body:

```markdown
---
id: 20260912-123000-ab12cd
kind: note
title: Meeting Notes
tags: [meeting, decision]
created: 2026-09-12T12:30:00+00:00
updated: 2026-09-12T12:30:00+00:00
---

Decisions written down. Absence of disagreement is not agreement.

## Lessons
- Write decisions down.
```

## Commands

```bash
python -m jarvis seed                 # create placeholder example documents
python -m jarvis new note "Title"     # create (add --tag x --body "...")
python -m jarvis list                 # list all documents
python -m jarvis list --kind note     # filter by kind
python -m jarvis read note/<id>.md    # show one document
python -m jarvis edit note/<id>.md --title "New" --body "..."
python -m jarvis delete note/<id>.md --yes
python -m jarvis learn                # rebuild learn/index.json + lessons.md
```

Pass `--root <dir>` to use a different isolated folder than `.jarvis`.

## Design rules

1. **Isolation** — data lives only under the store root; path traversal is
   rejected.
2. **CRUD only** — create, read, update, delete. Nothing fancier yet.
3. **Derived state is rebuildable** — `learn/` is recomputed from `notes/`;
   it is never the source of truth.
4. **No magic** — the "learning" pass is deterministic: tag frequencies, counts,
   and lesson bullets extracted from `## Lessons` headings.
5. **Placeholder only** — no historical data is imported until explicitly
   authorized.

## Tests

```bash
python -m pytest -q
```