# Journal: State-Transitions

> Formal memory state changes with reasoning.

Each file: one state transition.

```yaml
transition_id: TRX-YYYYMMDD-NNN
date: timestamp
target: MEM-...
from_status: observed | interpreted | candidate | verified | active
to_status: verified | active | superseded | deprecated | rejected
trigger: what caused the transition
evidence:
  - evidence chain
```