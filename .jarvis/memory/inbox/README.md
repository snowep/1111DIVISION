# Inbox

> Quarantine layer. Everything lands here first.

## Purpose

Prevent premature commitment. User statements, inferences, observations — all start as candidates. Only after validation and approval do they get promoted to persistent memory.

## Status

No items currently in inbox.

## Flow

```
INPUT → INBOX → CLASSIFY → VALIDATE → PROMOTE → MEMORY
```

### Classification

When an item enters the inbox, classify:

1. **Type:** What kind of memory is this? (project, knowledge, episodic, working)
2. **Authority:** Who can act on it? (user-explicit, external-information, inference, etc.)
3. **Approval:** Is this approved for action? (explicit, implicit, none)
4. **Scope:** What domain does it apply to?
5. **Confidence:** How reliable is this information?

### Validation

Before promotion, verify:

1. Is this confirmed by the user or by evidence?
2. Does this conflict with existing memory?
3. Is the authority sufficient for the intended action?
4. Is the scope correct?

### Promotion

After validation, promote to the appropriate memory class:

- **working/** — temporary, disposable
- **episodic/** — what happened (history, not truth)
- **project/** — validated project state (high confidence)
- **knowledge/** — general reusable knowledge

### Rejection

If validation fails:

- **Rejected:** Information is incorrect or unverifiable
- **Superseded:** Information is outdated by newer data
- **Deprecated:** Information is no longer relevant

## Example

User says: "I think we should abandon the current architecture."

This enters inbox as:

```yaml
---
id: INBOX-20260910-001
type: project-decision
status: candidate

source: user
confidence: 0.7  # user said "I think" — not committed

authority: user-explicit
approval: none   # not yet confirmed
scope: 11:11 Division

created: 2026-09-10
---
```

Only when the user commits does it become:

```yaml
status: active
approval: explicit
```
