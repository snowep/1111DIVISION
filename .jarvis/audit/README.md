# Audit

> Event-sourced mutation history. Append-only.

## Purpose

Every meaningful mutation produces an event. Audit is not text logs — it's an event history.

## Event Format

```yaml
event_id: EVT-YYYYMMDD-NNN
timestamp: YYYY-MM-DDTHH:MM:SSZ
actor: user | jarvis | tool | system | council | external | automation
action: memory.create | memory.promote | memory.supersede | decision.make | skill.activate | ...
target: MEM-XXX | DEC-XXX | SKILL-XXX
from_status: previous state
to_status: new state
reason: explanation
provenance:
  type: github | conversation | inference | observation | council | tool | automation
  # ... (full provenance chain)
```

## Event Types

### Memory Events

```yaml
# Memory created (enters inbox)
event_id: EVT-20260910-001
timestamp: 2026-09-10T14:30:00Z
actor: jarvis
action: memory.create
target: MEM-20260910-001
from_status: null
to_status: observed
reason: user_input_received
provenance:
  type: conversation
  session_id: ...
  message_id: ...
```

```yaml
# Memory promoted (inbox → project)
event_id: EVT-20260910-002
timestamp: 2026-09-10T14:35:00Z
actor: jarvis
action: memory.promote
target: MEM-20260910-001
from_status: candidate
to_status: active
reason: explicit_user_confirmation
provenance:
  type: conversation
  session_id: ...
  message_id: ...
```

```yaml
# Memory superseded
event_id: EVT-20260910-003
timestamp: 2026-09-10T15:00:00Z
actor: user
action: memory.supersede
target: MEM-20260910-001
from_status: active
to_status: superseded
reason: user_provided_updated_information
provenance:
  type: conversation
  session_id: ...
  message_id: ...
```

### Decision Events

```yaml
# Decision made
event_id: EVT-20260910-010
timestamp: 2026-09-10T14:40:00Z
actor: user
action: decision.make
target: DEC-001
from_status: null
to_status: active
reason: explicit_user_decision
provenance:
  type: conversation
  session_id: ...
  message_id: ...
```

### Skill Events

```yaml
# Skill activated
event_id: EVT-20260910-020
timestamp: 2026-09-10T14:45:00Z
actor: jarvis
action: skill.activate
target: SKILL-001
from_status: discovered
to_status: active
reason: skill_validated_and_adapted
provenance:
  type: tool
  inspected: skill-definition
```

### Permission Events

```yaml
# Permission changed
event_id: EVT-20260910-030
timestamp: 2026-09-10T14:50:00Z
actor: user
action: permission.grant
target: SKILL-001
from_status: read-only
to_status: read-write
reason: user_authorized_write_access
provenance:
  type: conversation
  session_id: ...
  message_id: ...
```

## Storage

Events are stored in:

```text
.audit/
├── actions/           # Action events
├── memory/            # Memory mutation events
├── skills/            # Skill lifecycle events
├── permissions/       # Permission change events
└── errors/            # Error events
```

## Rules

1. **Append-only** — events are never modified or deleted
2. **Immutable** — once written, an event is permanent
3. **Complete** — every meaningful mutation produces an event
4. **Traceable** — every event has actor, timestamp, and provenance
5. **Queryable** — events can be searched by actor, action, target, time

## Querying

Find all memory mutations:

```bash
grep -r "action: memory" .audit/memory/
```

Find all user actions:

```bash
grep -r "actor: user" .audit/
```

Find all events for a specific memory:

```bash
grep -r "target: MEM-20260910-001" .audit/
```
