# System Permissions

## Permission Matrix

| Action | ORION | Persona | Shared | External |
|--------|-------|---------|--------|----------|
| Read own memory | ✅ | ✅ | ✅ | ❌ |
| Write own memory | ✅ | ✅ | ✅ | ❌ |
| Read shared memory | ✅ | ✅ | ✅ | ❌ |
| Write shared memory | ✅ | ⚠️ Review | ✅ | ❌ |
| Read other persona memory | ✅ | ❌ | ❌ | ❌ |
| Write other persona memory | ✅ | ❌ | ❌ | ❌ |
| Promote memory | ✅ | ⚠️ Request | ❌ | ❌ |
| Create persona | ✅ | ❌ | ❌ | ❌ |
| Delete persona | ✅ | ❌ | ❌ | ❌ |
| Modify system config | ✅ | ❌ | ❌ | ❌ |
| Propose evolution | ✅ | ✅ Self | ❌ | ❌ |
| Adopt evolution | ✅ | ❌ | ❌ | ❌ |
| Execute tasks | ✅ | ✅ Assigned | ❌ | ❌ |
| Verify tasks | ✅ | ✅ Own | ❌ | ❌ |
| ORION review | ✅ | ❌ | ❌ | ❌ |
| Access knowledge (own) | ✅ | ✅ | ✅ | ❌ |
| Access knowledge (shared) | ✅ | ✅ | ✅ | ❌ |
| Access knowledge (orion) | ✅ | ✅ | ❌ | ❌ |
| Access knowledge (project) | ✅ | ✅ Assigned | ❌ | ❌ |
| Use skills (own) | ✅ | ✅ | ✅ | ❌ |
| Register skills | ✅ | ⚠️ Review | ❌ | ❌ |
| Write experience | ✅ | ✅ | ✅ | ❌ |
| Read experience | ✅ | ✅ | ✅ | ❌ |

## Legend

- ✅ Allowed
- ⚠️ Conditional (requires review/approval)
- ❌ Forbidden

## Notes

- Personas may request memory promotion via ORION
- Personas may propose self-evolution via their `evolution/` directory
- All destructive operations require ORION approval
- External access (user, tools) mediated by ORION
- Knowledge access follows layer hierarchy: persona → shared → orion → project
- Skills registered in `.agent/orion/skills/` or `.agent/personas/*/skills/`

## Knowledge Layer Access Rules

```
ORION:        [persona] + [shared] + [orion] + [project]
Persona:      [own] + [shared] + [orion] + [assigned project]
Shared:       [shared] + [orion] (read-only)
External:     None (mediated by ORION)
```