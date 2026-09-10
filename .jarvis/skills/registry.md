# Skill Registry

> Derived state. Rebuilt by scanning skill directories per `.jarvis/skills/discovery-protocol.md`.
> Never hand-edit as truth — regenerate from the scan.

## Registry Status

```yaml
updated: 2026-09-11
scan_source: .jarvis/skills/(discovered|inspected|adapted|installed)/
status: current
protocol: .jarvis/skills/discovery-protocol.md
```

## Skills

### Active

| ID | Name | Status | Source | Permissions | Triggers |
|----|------|--------|--------|-------------|----------|
| `github-analysis` | GitHub Repository Analysis | active | adapted | fs.read, net.read | analyze repo, scan repository, github analysis |

### Discovered / Inspected / Adapted (pending activation)

_None currently._

### Rejected

| ID | Reason |
|----|--------|
| _None currently._ |

---

## Notes

1. Only `status: active` skills are candidates for automatic use.
2. New skills land in `discovered/` — never straight to active.
3. Permission escalation requires user approval + audit event.
4. This file is derived from the skill directories. Regenerate on scan; do not treat as authoritative.