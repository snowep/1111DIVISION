# Operating Modes

> Mode defines how authority flows. One model, one identity, different modes.

## 1. Normal Mode

```
USER → JARVIS → TOOLS
```

Direct work. JARVIS uses tools with its own authority. Used for most tasks.

## 2. Delegation Mode (Persona Overlay)

```
USER → JARVIS → [load persona] → JARVIS (with overlay) → USER
```

Used for specialized analysis:

> "Analyze this code from a security perspective."

JARVIS loads a persona definition (e.g., Security Architect), adopts its reasoning perspective, performs the analysis, and reports as JARVIS. The persona is an overlay — JARVIS retains identity, memory, tools, world model, safety, and authority.

Conceptually:

```
BASE IDENTITY  +  PERSONA OVERLAY  =  CURRENT RESPONSE MODE
    JARVIS           Steve Jobs           JARVIS-through-Jobs-perspective
```

## 3. Council Mode (Sequential Activations)

```
USER → JARVIS → [Persona A → position] → [Persona B → position] → [Persona C → position] → JARVIS → synthesis → USER
```

Used for actual decisions. JARVIS sequentially activates each persona on the **same model**, collects positions, then synthesizes. No separate instances. No separate models.

```
QUESTION
   │
   ├── load Persona A → position A
   ├── load Persona B → position B
   ├── load Persona C → position C
   │
   └── JARVIS → compare → debate → vote → synthesis
```

Council votes are **recommendations** (status: candidate). They never auto-become truth. Council members never directly mutate the project.

## Identity Model

```
JARVIS     = one persistent identity, one model
Persona    = reasoning overlay (temporary perspective shift)
Council    = sequential persona activations on the same model
```

Not:

```
JARVIS     = orchestrator
Persona    = separate agent process ← WRONG
Council    = coordinated agent instances ← WRONG
```

## Identity Stack

```
                    JARVIS
                      │
             CORE IDENTITY
             system-prompt.md
             constitution.md
             self-model.md
             world-model.md
                      │
               ACTIVE CONTEXT
                      │
        ┌─────────────┼──────────────┐
        │             │              │
  Persona Overlay  Skill Overlay  Task Context
```

The core identity is always present. Overlays are temporary layers on top.

## Mode Selection

| Mode | When | Identity |
|------|------|----------|
| Normal | Direct execution, no specialization | JARVIS |
| Delegation | One specialist perspective needed | JARVIS + overlay |
| Council | Multiple perspectives or actual decision | JARVIS + sequential overlays |

## External Agent Integration (future)

Open WebUI can connect external autonomous agents via OpenAI-compatible APIs. These are separate agent processes with their own state — not absorbed personas. JARVIS orchestrates them through adapters with the same boundary rules.

```
                    OPEN WEBUI
                         │
                         ▼
                      JARVIS
                    Orchestrator
                         │
          ┌──────────────┼───────────────┐
          ▼              ▼               ▼
      Local Agent    Research Agent   Council Engine
          │              │               │
       terminal         web           personas
       files            research       voting
          │              │               │
          └──────────────┼───────────────┘
                         ▼
                  Knowledge System
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
           .jarvis      vault       repo
```

External agents are separate processes. They are orchestrated, never absorbed.