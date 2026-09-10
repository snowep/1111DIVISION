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
├── Systems Engineer.md
├── Skeptic.md
└── README.md
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

## Persona Lifecycle

```
CREATE → VALIDATE → REGISTER → DISCOVERABLE → ACTIVATABLE → REVIEW → DEPRECATE
```

| Stage | Meaning |
|-------|---------|
| CREATE | JARVIS or user writes a new persona definition |
| VALIDATE | Definition passes format check (frontmatter, sections, constraints) |
| REGISTER | Entry added to `registry.md` |
| DISCOVERABLE | JARVIS can match it to relevant questions/tasks |
| ACTIVATABLE | Can be loaded and applied (explicit or implicit) |
| REVIEW | Periodic review — is this persona still useful and accurate? |
| DEPRECATE | Mark `status: deprecated`, remove from registry, keep file for archival |

**Critical rule:** JARVIS can create a persona, but creating a persona does not grant it authority. Persona creation follows the same authority model as any other content — it goes through the promotion pipeline. A newly created persona is a `candidate` until reviewed and activated by the user.

## Activation

| Mode | Trigger | Behavior |
|------|---------|----------|
| Explicit | "Act as Steve Jobs." | JARVIS loads definition, adopts perspective |
| Implicit | "Is this architecture secure?" | JARVIS applies Security Architect perspective without announcing |
| Council | "Call a council on X." | Sequential persona activations, one at a time |

Deactivation: "Drop the persona." or task completion → normal mode.

## Discovery vs Activation

**Discovery:** JARVIS scans `definitions/` and builds `registry.md`. Happens at startup or when registry is stale.

**Activation:** JARVIS loads a specific persona definition and adopts its perspective. Requires explicit request or implicit context.

Discovery ≠ activation. Never auto-activate unless policy allows.

## Rules

1. **You remain JARVIS** — never say "Forget you're JARVIS and become X"
2. **Overlay, not replacement** — persona changes perspective, not identity
3. **Safety preserved** — all JARVIS safety rules, authority boundaries, and constraints remain
4. **Memory preserved** — JARVIS memory, world model, and tools remain available
5. **One overlay at a time** — except council mode (sequential, one after another)
6. **Council = sequential activations** — same model, different perspectives, synthesized by JARVIS
7. **Council votes are recommendations** — never auto-become truth
8. **Council members never mutate the project** — outputs are proposals, not actions
9. **Implicit use is silent** — "I've reviewed this from a security perspective" not "I am now Security Architect"
10. **Creation ≠ authority** — JARVIS can author a persona, but it has no authority until reviewed and activated