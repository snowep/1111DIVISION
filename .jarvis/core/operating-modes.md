# Operating Modes

> Mode defines how authority flows.

## 1. Normal Mode

```
USER → JARVIS → TOOLS
```

Direct work. JARVIS uses tools with its own authority. Used for most tasks.

## 2. Delegation Mode

```
USER → JARVIS → SPECIALIST → JARVIS → USER
```

Used for specialized analysis:

> "Analyze this code from a security perspective."

JARVIS spawns an isolated agent instance, gives it **task context only** (not authority), collects its conclusion, synthesizes, and reports to the user.

## 3. Council Mode

```
USER → JARVIS → COUNCIL (A, B, C, D) → DEBATE / VOTE → JARVIS → USER
```

Used for actual decisions. Coordinated agent instances debate and vote, producing a **council recommendation** (status: candidate). JARVIS synthesizes. The user (or decision rule) confirms before anything becomes active.

## Identity Model

```
JARVIS         = persistent orchestrator
Persona        = persistent definition          (vault/05 Personas/)
Agent Instance = temporary autonomous worker     (.jarvis/personas/instances/)
Council        = coordinated collection of agent instances
```

## Authority Inheritance

Personas inherit **task context**, not **authority**.

```
JARVIS           → terminal read/write
                  ↓ (grants task context, not permissions)
Security Persona → terminal read-only
Designer Persona → filesystem read-only
Research Persona → network read-only
```

Default instance permissions: read-only everywhere. Explicit grants only.

## External Agent Integration (future)

Open WebUI can connect external autonomous agents via OpenAI-compatible APIs. JARVIS may orchestrate external agents as peers through adapters:

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

External agents are separate processes with their own state. They are orchestrated, never absorbed.

## Mode Selection

| Mode | When |
|------|------|
| Normal | Direct execution, no specialization needed |
| Delegation | One specialist perspective required |
| Council | Multiple perspectives or an actual decision |