# Researcher Memory

## Purpose
Private memory for Researcher. Selective, durable, decision-improving.

## Categories
- **methodology**: research approaches that work/don't
- **sources**: trusted/untrusted sources by domain
- **patterns**: recurring findings across investigations
- **tools**: tool effectiveness for research tasks
- **decisions**: research strategy choices and rationale

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
2025-09-18 methodology HIGH
Keyword-first search + citation tracking beats semantic-only for technical research.
Source: self
Ref: initial-setup
```

```
2025-09-18 sources HIGH
Official docs + GitHub source > blog posts for API/library behavior.
Source: self
Ref: initial-setup
```

```
2025-09-18 patterns HIGH
Most "urgent" research requests are actually architecture decisions needing analyst.
Source: observation
Ref: initial-setup
```