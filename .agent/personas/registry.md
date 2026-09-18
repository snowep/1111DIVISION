# Persona Registry

## Active Personas

| Name | Role | Status | Domain Tags | Primary Skills |
|------|------|--------|-------------|----------------|
| researcher | Deep-dive investigation | ACTIVE | research, investigation, literature-review, fact-finding | web-search, citation-tracking, synthesis |
| developer | Code implementation | ACTIVE | implementation, refactoring, testing, debugging | pytest, linting, git, build-systems |
| designer | UX/UI design | ACTIVE | design, ux, ui, accessibility, design-systems | wireframing, prototyping, a11y-audit |
| analyst | Strategic analysis | ACTIVE | strategy, trade-offs, risk, decision-support | frameworks, modeling, evaluation |

## Persona Capabilities Matrix

| Capability | researcher | developer | designer | analyst |
|------------|------------|-----------|----------|---------|
| Web research | PRIMARY | secondary | secondary | secondary |
| Code writing | none | PRIMARY | none | none |
| Visual design | none | none | PRIMARY | none |
| Decision frameworks | secondary | secondary | secondary | PRIMARY |
| Architecture | none | consult | consult | consult |
| Testing | none | PRIMARY | usability | simulation |
| Documentation | synthesis | code-docs | design-docs | decision-records |

## Activation Keywords (Implicit)

### researcher
- "investigate", "research", "find out", "look up", "literature review"
- "what does X do", "how does Y work", "compare A vs B"
- "verify", "fact-check", "source", "citation"

### developer
- "implement", "build", "code", "refactor", "fix", "debug"
- "test", "pytest", "function", "class", "module", "API"
- "build", "compile", "lint", "format", "dependency"

### designer
- "design", "UI", "UX", "interface", "mockup", "wireframe"
- "accessibility", "a11y", "component", "design system"
- "user flow", "interaction", "visual", "prototype"

### analyst
- "analyze", "evaluate", "compare", "trade-off", "decide"
- "risk", "strategy", "framework", "recommendation"
- "pros and cons", "cost-benefit", "second-order"

## Council Composition Rules

### Default Council (major decisions)
- researcher + developer + designer + analyst
- ORION moderates, does not vote

### Technical Council (architecture/implementation)
- developer + analyst + researcher
- designer consulted if UI affected

### Product Council (user-facing decisions)
- designer + analyst + researcher
- developer consulted for feasibility

### Minimal Council (time-critical)
- analyst + one domain expert
- ORION may decide solo with audit trail

## Adding New Personas

1. Create directory: `.agent/personas/<name>/`
2. Populate from `_template/`
3. Write `identity.md` with clear boundaries
4. Register in this file
5. Define activation keywords
6. Specify council membership rules
7. Test activation protocol

## Persona Lifecycle

```
CREATED → ACTIVE → (INACTIVE) → ARCHIVED
          ↑  ↓
      Suspended (temporary)
```

- ACTIVE: available for activation
- INACTIVE: hidden from implicit activation, explicit still works
- ARCHIVED: read-only, preserved for history
- SUSPENDED: temporarily disabled (e.g., during migration)