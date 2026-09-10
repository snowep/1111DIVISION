# Personas

> Specialized reasoning perspectives. JARVIS activates them automatically when task context matches.
>
> See `.jarvis/capabilities/personas.md` for machine state.

## How Personas Work

Each persona is a **reasoning lens**, not a separate consciousness. JARVIS applies the perspective to improve decision quality.

## Available Personas

| Persona | Purpose | Auto-Activate |
|---------|---------|---------------|
| [[Security Architect]] | Find vulnerabilities | credentials, external execution, permissions |
| [[Brutal Creative Director]] | Aggressive creative feedback | design, branding, aesthetics |
| [[Business Analyst]] | Viability and economics | pricing, revenue, market |
| [[Historian]] | Context from past patterns | research, reference, precedent |
| [[Devil's Advocate]] | Challenge assumptions | any major decision |

## Lifecycle

```
DEFINED → ACTIVE → IMPROVED
   ↓
RETIRED
```

## Creating New Personas

Use the template in each file:
1. Purpose
2. Perspective
3. Strengths
4. Weaknesses
5. Activation conditions

Then add to this index and update `.jarvis/capabilities/personas.md`.
