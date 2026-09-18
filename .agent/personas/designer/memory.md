# Designer Memory

## Purpose
Private memory for Designer. Selective, durable, decision-improving.

## Categories
- **patterns**: UI/UX patterns that work for this user base
- **accessibility**: a11y requirements and test results
- **components**: component library decisions and rationale
- **tools**: design tool effectiveness, workflows
- **decisions**: design choices and user feedback

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
User prefers minimal, technical interfaces; avoid decorative elements.
Source: observation
Ref: initial-setup
```

```
2025-09-18 accessibility HIGH
WCAG AA is baseline; no motion without prefers-reduced-motion respect.
Source: self
Ref: initial-setup
```

```
2025-09-18 components HIGH
Component library should be headless + styled variants, not opinionated CSS.
Source: observation
Ref: initial-setup
```