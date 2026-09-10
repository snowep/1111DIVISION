# Personas

<!-- JARVIS internal: pointer to canonical persona system -->

## Canonical Location

The persona library is now managed in one place:

```text
.jarvis/personas/definitions/   # Structured persona definitions (YAML frontmatter)
.jarvis/personas/registry.md    # Auto-built index (scan of definitions/)
.jarvis/personas/runtime.md     # Active overlay state
```

This file is kept for capability compatibility — it no longer holds persona state. See `.jarvis/personas/README.md`.

## Model

One model. One identity. Temporary reasoning overlays.

- A persona changes: perspective, style, priorities, decision criteria
- A persona never changes: identity, memory, tools, world model, safety, authority
- Council = sequential persona activations on the same model
- Discovery ≠ activation