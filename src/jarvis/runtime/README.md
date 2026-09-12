# runtime/

Deterministic kernel bootstrap.

- `roots.py` — `resolve_root()` finds the canonical workspace root
  (explicit arg → `JARVIS_ROOT` env → walk up from cwd to the first dir
  containing `.jarvis/` → cwd fallback) and bundles sub-roots
  (`jarvis`, `vault`, `council`, `src`, `tests`, `docs`).
- `kernel.py` — `build_runtime()` constructs the full `Runtime` eagerly:
  roots + resolver + SafeIO + identity. Any failure raises a typed error;
  the runtime is never half-initialized.

Semantic alias resolution (`vault/ council/ skills/ core/ learn/`) lives in
`io/workspace.py`; identity loading lives in `core/identity.py`.