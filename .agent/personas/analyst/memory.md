# Analyst Memory

## Purpose
Private memory for Analyst. Selective, durable, decision-improving.

## Categories
- **frameworks**: decision frameworks that work/don't
- **biases**: known cognitive biases in this context
- **trade-offs**: recurring trade-off patterns
- **data**: reliable data sources and their limits
- **decisions**: past recommendations and outcomes

## Rules
1. No conversation fragments
2. No temporary state
3. No cross-persona info unless promoted
4. One entry per durable fact
5. Provenance preserved

## Format
```
[DATE] [CATEGORY] [CONFIDENCE]
Fact.
Source: [self|user|observation|promoted-from:<source>]
Ref: [file/commit]
```

## Current Entries
```
2025-09-18 frameworks HIGH
User prefers reversible decisions over optimal ones; frame accordingly.
Source: observation
Ref: initial-setup
```

```
2025-09-18 biases HIGH
Sunk cost appears in architecture discussions; explicitly surface it.
Source: self
Ref: initial-setup
```

```
2025-09-18 trade-offs HIGH
Speed vs. correctness: user chooses correctness for core, speed for experiments.
Source: observation
Ref: initial-setup
```