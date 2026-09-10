# Expert Personas

> Reasoning perspectives JARVIS can activate. Each has activation conditions.

## Canonical Location

The **authoritative persona library** is now:

```text
.jarvis/personas/definitions/
```

JARVIS scans this folder at startup (or when the registry is stale) and builds `.jarvis/personas/registry.md`.

This vault folder is the **human-readable curated layer** — it holds the same personas for human review in Obsidian. JARVIS loads definitions from `.jarvis/personas/definitions/`, not from vault.

## Current Library (canonical)

| Persona | File | Domains |
|---------|------|---------|
| Steve Jobs | `.jarvis/personas/definitions/Steve Jobs.md` | product, branding, simplicity |
| Virgil Abloh | `.jarvis/personas/definitions/Virgil Abloh.md` | design, branding, cultural-strategy |
| Security Architect | `.jarvis/personas/definitions/Security Architect.md` | security, architecture, risk |
| Creative Director | `.jarvis/personas/definitions/Creative Director.md` | design, branding, visual-identity |
| Business Strategist | `.jarvis/personas/definitions/Business Strategist.md` | business, strategy, market |
| Systems Engineer | `.jarvis/personas/definitions/Systems Engineer.md` | architecture, infrastructure, scalability |
| Skeptic | `.jarvis/personas/definitions/Skeptic.md` | critical-thinking, evidence |

## Older Vault Personas

These exist in vault and are kept as curated knowledge. They will be migrated into `.jarvis/personas/definitions/` (structured format with YAML frontmatter) when JARVIS next rebuilds the registry.

## Model

One model. One identity. Temporary reasoning overlays.

```
JARVIS (base) + PERSONA OVERLAY = CURRENT RESPONSE MODE
```

## See Also

- `.jarvis/personas/definitions/README.md` (definition format)
- `.jarvis/personas/registry.md` (auto-built index)
- `.jarvis/personas/runtime.md` (active persona state)