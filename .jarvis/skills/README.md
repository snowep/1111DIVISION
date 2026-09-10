# Skills

> Active skills with explicit permissions. Not "can do anything."

## Skill Format

```yaml
id: skill-name
name: Human Readable Name
description: What this skill does
status: discovered | inspected | adapted | active | deprecated | rejected

# Permissions
permissions:
  filesystem:
    read: true | false
    write: true | false
  terminal:
    execute: true | false
  network:
    read: true | false
    write: true | false

# Metadata
source: github | local | user-created
adapted_from: null | original-repo
created: YYYY-MM-DD
updated: YYYY-MM-DD

# Capabilities
triggers:
  - keyword or pattern
required_tools:
  - tool-name
dependencies:
  - dependency-name
```

## Skill Lifecycle

```
discovered → inspected → adapted → active → deprecated
                  ↓                    ↓
               rejected             rejected
```

### States

| State | Meaning |
|-------|---------|
| `discovered` | Found but not yet examined |
| `inspected` | Analyzed, not yet adapted |
| `adapted` | Modified to fit JARVIS architecture |
| `active` | Ready for use (with permissions) |
| `deprecated` | No longer maintained |
| `rejected` | Not suitable for JARVIS |

## Permissions Model

**Critical:** Active skill ≠ can do anything.

Every skill must declare explicit permissions:

```yaml
permissions:
  filesystem:
    read: true      # Can read files
    write: false    # Cannot write files
  terminal:
    execute: false  # Cannot execute commands
  network:
    read: true      # Can read from network
    write: false    # Cannot write to network
```

### Permission Values

| Permission | Meaning | Risk |
|------------|---------|------|
| `filesystem.read` | Can read files | Low |
| `filesystem.write` | Can write/create/delete files | Medium |
| `terminal.execute` | Can execute shell commands | High |
| `network.read` | Can make HTTP requests | Low |
| `network.write` | Can send data to network | Medium |

### Safe Defaults

When adapting a skill, start with minimal permissions:

```yaml
permissions:
  filesystem:
    read: true
    write: false
  terminal:
    execute: false
  network:
    read: false
    write: false
```

Grant additional permissions only when:
1. The skill requires them
2. The user has approved
3. The risk is acceptable

## Example Skills

### GitHub Analysis

```yaml
id: github-analysis
name: GitHub Repository Analysis
description: Analyze GitHub repositories for architecture, security, and quality
status: active

permissions:
  filesystem:
    read: true
    write: false
  terminal:
    execute: false
  network:
    read: true
    write: false

source: github
adapted_from: snowep/skill-github-analysis
created: 2026-09-10
updated: 2026-09-10

triggers:
  - "analyze repo"
  - "scan repository"
  - "github analysis"

required_tools:
  - web_fetch
  - file_read

dependencies: []
```

### Code Review

```yaml
id: code-review
name: Code Review
description: Review code for quality, security, and architecture
status: active

permissions:
  filesystem:
    read: true
    write: false
  terminal:
    execute: false
  network:
    read: false
    write: false

source: local
created: 2026-09-10
updated: 2026-09-10

triggers:
  - "review code"
  - "code review"
  - "analyze code"

required_tools:
  - file_read

dependencies: []
```

## Skill Discovery

When scanning a skills directory:

1. Load skill definition (YAML frontmatter)
2. Validate permissions are declared
3. Check status (only active skills are candidates for use)
4. Match triggers against current task
5. Verify permissions are sufficient for task
6. Select safest, most relevant skill

## Permission Escalation

Skills cannot escalate their own permissions.

Permission changes require:
1. User explicit approval
2. Audit event recorded
3. Reason documented

```yaml
event_id: EVT-20260910-030
actor: user
action: permission.grant
target: SKILL-001
from_status: read-only
to_status: read-write
reason: user_authorized_write_access
```
