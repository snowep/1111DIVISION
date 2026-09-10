# Persona Library

> The human-readable persona knowledge layer. Canonical machine-loadable definitions live in `.jarvis/personas/definitions/`.

## Structure

```text
vault/05 Personas/
├── Council/          # Council knowledge layer
├── Expert Personas/  # Curated persona definitions (human view)
└── User/             # User profile
```

## Canonical Source

The **one canonical persona folder** JARVIS scans is:

```text
.jarvis/personas/definitions/
```

This vault folder is the Obsidian-facing view. Both surfaces describe the same persona library. The `.jarvis` copy is what JARVIS actually loads at runtime; vault is what the human reads and edits. JARVIS distills vault edits back into `.jarvis/personas/definitions/`.

## Model

One model. One identity. Temporary reasoning overlays.

```
JARVIS (base) + PERSONA OVERLAY = CURRENT RESPONSE MODE
```

Activation:
- Explicit ("Act as Steve Jobs") → load definition
- Implicit ("Is this secure?") → apply perspective silently
- Council → sequential activations on same model
- Deactivate ("Drop the persona") → normal mode