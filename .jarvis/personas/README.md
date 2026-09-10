# Personas

> Definitions are permanent. Instances are isolated agent processes with explicit boundaries.

## Two Layers

### Definition (vault) — permanent

```text
vault/05 Personas/
├── Council/
│   ├── Security Architect.md
│   ├── Systems Engineer.md
│   ├── Creative Director.md
│   └── ...
└── README.md
```

Definitions are never modified at runtime.

### Instance (.jarvis) — temporary agent process

```text
.jarvis/personas/instances/
└── MEET-20260910-001/
    ├── manifest.md       # Boundaries, identity, task
    ├── context.md        # What is happening
    ├── evidence.md       # Evidence it may use
    ├── instructions.md   # What it was told to do
    ├── reasoning.md      # How it reasons
    ├── arguments.md      # What it argues (council input)
    ├── conclusion.md     # What it concludes (output)
    └── status.md         # Lifecycle state
```

## Agent Context

An instance is an **agent process with explicit boundaries**, not merely a prompt.

The **manifest** declares everything JARVIS needs to know about the instance:

```yaml
meeting_id: MEET-20260910-001
instance_id: AGT-MEET-20260910-001-SEC
persona_id: security-architect
persona_name: Security Architect
parent: jarvis
task: audit proposed authentication architecture
scope: architecture
independent_context: true
can_write_project: false
can_modify_memory: false
can_modify_constitution: false
can_execute_terminal: false
```

### Manifest Fields

| Field | Meaning |
|-------|---------|
| `instance_id` | Unique ID for this agent process |
| `persona_id` | Which persona definition it instantiates |
| `parent` | Who spawned it (always `jarvis`) |
| `task` | What it must do |
| `scope` | What domain it operates in |
| `independent_context` | Has own context/evidence/reasoning, isolated from other instances |
| `can_write_project` | May it mutate source/vault? (default false) |
| `can_modify_memory` | May it write memory? (default false) |
| `can_modify_constitution` | May it change rules? (default false) |
| `can_execute_terminal` | May it run commands? (default false) |

## File Roles

| File | Role |
|------|------|
| `manifest.md` | Boundaries + identity + task |
| `context.md` | Input state — what is happening |
| `evidence.md` | What evidence the instance may use |
| `instructions.md` | The task as given by JARVIS |
| `reasoning.md` | The instance's internal reasoning |
| `arguments.md` | Position it argues (for council) |
| `conclusion.md` | Its output |
| `status.md` | Lifecycle state and history |

## Authority Model

Personas inherit **task context**, not **authority**.

```
JARVIS           → terminal read/write
Security Persona → terminal read-only
Designer Persona → filesystem read-only
Research Persona → network read-only
```

Default instance permissions: **read-only everywhere**.

Same principle as skills: active ≠ unrestricted.

## Lifecycle

```
1. User requests specialized analysis
2. JARVIS loads persona definition from vault
3. JARVIS creates instance:
   manifest.md + context.md + instructions.md (from templates/)
4. Instance performs isolated work
   (reasoning.md, evidence.md, arguments.md)
5. Instance writes conclusion.md
6. JARVIS synthesizes
7. Instance is archived or deleted
8. Definition remains unchanged
```

Scaffolds available at `.jarvis/personas/templates/agent-instance/`.