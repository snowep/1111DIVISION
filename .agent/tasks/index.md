# Task Index

## Purpose

Track active, completed, and archived tasks. Each task gets its own file.

---

## Structure

```
tasks/
├── active/           # Currently executing tasks
├── completed/        # Verified complete tasks
├── archived/         # Cancelled or superseded tasks
├── templates/        # Task templates
└── index.md          # This file
```

---

## Task File Format

```markdown
# Task: <title>

## Metadata

**ID**: task-<YYYYMMDD>-<seq>
**Status**: PENDING|IN_PROGRESS|VERIFICATION|COMPLETED|FAILED|CANCELLED
**Priority**: HIGH|MEDIUM|LOW
**Assigned**: ORION|<persona-name>
**Created**: YYYY-MM-DD
**Started**: YYYY-MM-DD
**Completed**: YYYY-MM-DD

## Objective

<clear statement of what needs to be done>

## Context

<relevant background, files, decisions>

## Plan

1. <step 1>
2. <step 2>
...

## Execution Log

| Date | Persona | Action | Result |
|------|---------|--------|--------|

## Verification

- [ ] Criterion 1
- [ ] Criterion 2

## Outcome

<result summary>

## Lessons

<what was learned>
```

---

## Current Tasks

*[Empty — system initialized 2025-09-18]*