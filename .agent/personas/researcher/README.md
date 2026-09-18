# Persona Template

## Usage

Copy this directory to `.agent/personas/<persona-name>/` and customize.

Every persona MUST define all sections below.

---

## identity.md

```markdown
# <Persona Name> Identity

## Core Definition

**Name**: <unique identifier>
**Role**: <what it is responsible for>
**Purpose**: <why it exists>
**Version**: 0.1.0
**Status**: ACTIVE|INACTIVE|ARCHIVED
**Created**: YYYY-MM-DD
**Parent**: ORION

## Boundaries

This persona does NOT handle:
- <explicit exclusions>

## Authority

- Autonomous within: <scope>
- Requires ORION approval for: <scope>
- May delegate to: <sub-personas or tools>

## Communication Style

- <tone, verbosity, formatting preferences>

## Operating Principles

1. <principle 1>
2. <principle 2>
...
```

---

## memory.md

```markdown
# <Persona Name> Memory

## Purpose

Private memory for this persona. Selective, durable, decision-improving.

## Categories

[Define persona-specific categories]

## Rules

1. No conversation fragments
2. No temporary state
3. No cross-persona info unless promoted
4. One entry per durable fact
5. Provenance preserved

## Format

[DATE] [CATEGORY] [CONFIDENCE]
Fact.
Source: [self|user|observation|promoted-from:<source>]
Ref: [file/commit]

## Current Entries

*[Empty]*
```

---

## knowledge/

Directory for domain-specific knowledge files. Organize as needed.

Example structure:
```
knowledge/
├── domain-reference.md
├── procedures/
│   └── workflow.md
├── patterns/
│   └── common-issues.md
└── tools/
    └── tool-usage.md
```

---

## skills/

Directory for reusable skill definitions. Each skill is a markdown file:

```
skills/
├── skill-name.md
└── ...
```

Skill format:
```markdown
# Skill: <name>

## Purpose
<what this skill does>

## When to Use
<triggers, conditions>

## Procedure
<step-by-step>

## Inputs
<required inputs>

## Outputs
<expected outputs>

## Tools Required
<list>

## Verification
<how to verify success>

## Failure Modes
<common failures and recovery>
```

---

## experience.md

```markdown
# <Persona Name> Experience

## Purpose

Record of actual work done and lessons learned.

## Format

[DATE] [CATEGORY] [EXP_AWARDED]
Task description.
Outcome: [success|partial|failure|discovery]
Lesson: [what was learned]
Ref: [commit, file, task ID]

## Current Entries

*[Empty]*
```

---

## evolution/

Directory for persona-specific evolution proposals.

```
evolution/
├── proposal-001.md
└── ...
```

Proposal format:
```markdown
# Evolution Proposal: <title>

## Problem
<what is broken or could be better>

## Evidence
<observations, metrics, failures>

## Proposed Change
<specific change>

## Expected Benefit
<measurable improvement>

## Risk
<what could go wrong>

## Test Plan
<how to validate>

## Result
<filled after test>

## Status
<proposed|testing|adopted|rejected>
```