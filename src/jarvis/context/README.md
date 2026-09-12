# context/

Deterministic prompt/context assembly with priority ordering.

- `builder.py` — `ContextBuilder` stacks named layers and `build()`s an
  `AssembledContext`. Canonical priority (index 0 = highest):

```
platform → constitution → system → world_model → memory → skills → task → persona → user
```

Lower layers never override higher ones. `apply_override(caller=...)`
enforces this: a lower layer (e.g. `user`) attempting to write into a
higher layer (e.g. `memory`) raises `CONTEXT_ERROR`.

The assembled context is deterministic: identical inputs → identical output.