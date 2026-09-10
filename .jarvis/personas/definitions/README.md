# Persona Definitions

> JARVIS loads persona definitions from this folder. Each definition is a reasoning overlay — it changes perspective, not identity.

## Model

```
JARVIS (base identity)
      +
PERSONA OVERLAY (temporary reasoning perspective)
      =
CURRENT RESPONSE MODE
```

JARVIS is always JARVIS. A persona changes perspective, style, priorities, and decision criteria. It does not change identity, memory, tools, world model, safety rules, or authority boundaries.

## Folder

```text
.jarvis/personas/definitions/
├── Steve Jobs.md
├── Virgil Abloh.md
├── Security Architect.md
├── Creative Director.md
├── Business Strategist.md
└── ...
```

## Definition Format

Every persona file has YAML frontmatter and structured sections:

```yaml
---
id: persona.steve_jobs
name: Steve Jobs
type: historical-persona
status: active
activation: explicit
domains:
  - product
  - branding
  - simplicity
  - user-experience
---

# Identity
# Primary Perspective
# Questions
# Communication
# Biases
# Constraints
```

## Activation

- **Explicit:** "Act as Steve Jobs." → JARVIS loads definition, adopts perspective
- **Implicit:** "Is this architecture secure?" → JARVIS contextually applies Security Architect perspective without announcing
- **Deactivate:** "Drop the persona." or task completion → return to normal mode

## Discovery

JARVIS scans this folder and builds `.jarvis/personas/registry.md`. Discovery ≠ activation. Never auto-activate unless policy allows.

## Registry

See `.jarvis/personas/registry.md` — built from scanning definitions.

## Runtime

See `.jarvis/personas/runtime/` — active persona state (which persona is loaded, task context).