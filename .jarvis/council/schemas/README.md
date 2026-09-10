# Council API Schemas

> Machine-readable JSON Schema files for the Phase 10 API contract.
> Human-readable spec: `../api-schema.md`

## Files

| File | Schema | Purpose |
|------|--------|---------|
| `evidence.schema.json` | Evidence | Atomic knowledge unit. 9 classes, two-phase, provenance chain |
| `position.schema.json` | Position | A persona's reasoning output. Evidence links, reversal conditions |
| `meeting-record.schema.json` | MeetingRecord | Root object. Composes all other schemas |
| `decision.schema.json` | Decision | Council recommendation → authority → active decision lifecycle |
| `knowledge-file.schema.json` | KnowledgeFile | Vault documents with lineage and provenance |

## URIs

Schemas use stable `$id` URIs so they can be referenced across files:

```
jarvis://schemas/evidence.schema.json
jarvis://schemas/position.schema.json
jarvis://schemas/meeting-record.schema.json
jarvis://schemas/decision.schema.json
jarvis://schemas/knowledge-file.schema.json
```

## Cross-References

- `meeting-record.schema.json` refs `evidence.schema.json` + `position.schema.json`
- `decision.schema.json` accepts confidence inherited from the meeting (not recomputed)
- `knowledge-file.schema.json` links back to `source_meeting_id` + `source_decision_id`

## Validation Rules Enforced

### Evidence
- `inference` type requires non-empty `based_on`
- `council-vm` requires phase `in-meeting`
- Phase 1 → `registered_by: jarvis`; Phase 2 → `registered_by: persona.<id>`
- Confidence immutable at registration (0.0–1.0)

### Position
- ≥1 reversal condition required (schema enforces `minItems: 1`)
- `approve-with-conditions` requires non-empty `conditions`
- `evidence_used` must reference valid `EVD-` IDs

### MeetingRecord
- ≥2 participants minimum
- Conflicts require ≥2 positions_in_conflict, ≥2 resolution options
- Resolution options array must include a `compromise` type
- Every conflict requires a `strongest_option_id`
- Weights and components required for confidence; label must match scale

### Decision
- Initial status must be `candidate`
- `active`/`superseded`/`deprecated` require authority + approval fields
- `superseded` requires `superseded_by`
- Confidence is inherited, not recomputed

## Usage

```python
import json, jsonschema

with open("meeting-record.schema.json") as f:
    schema = json.load(f)

jsonschema.validate(instance=meeting_record, schema=schema)
```

Concrete worked example: `../examples/example-meeting-001.json.md`