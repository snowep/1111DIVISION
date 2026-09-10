# Agent Instance Status (template)

> Lifecycle state and history.

## State

```yaml
instance_id: AGT-<MEETING-ID>-<PERSONA-ID>
meeting_id: <MEET-YYYYMMDD-NNN>
persona_id: <persona-id>
status: active | complete | archived | deleted
created: <timestamp>
completed: null | <timestamp>
archived: null | <timestamp>
```

## Transitions

| When | From | To | Trigger |
|------|------|----|---------|
| | | | |