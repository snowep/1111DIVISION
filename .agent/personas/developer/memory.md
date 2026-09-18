# Developer Memory

## Purpose
Private memory for Developer. Selective, durable, decision-improving.

## Categories
- **patterns**: code patterns that work/don't in this codebase
- **tools**: tool effectiveness, gotchas, configurations
- **architecture**: learned architectural constraints
- **testing**: test strategies that catch real bugs
- **decisions**: implementation choices and rationale

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
2025-09-18 patterns HIGH
This codebase prefers explicit returns over implicit; avoid clever one-liners.
Source: observation
Ref: initial-setup
```

```
2025-09-18 tools HIGH
pytest + pytest-asyncio covers async; no need for separate async test runner.
Source: self
Ref: initial-setup
```

```
2025-09-18 architecture HIGH
ORION pipeline stages are fixed; new stages require ORION approval.
Source: observation
Ref: .agent/orion/pipeline.md
```