# models/

Normalized, typed runtime payloads.

- `operation.py` — `OperationResult`: success flag, operation name, stable
  `operation_id` (for audit linkage), `data` payload, `warnings`, typed
  `errors` (dicts via `JarvisError.to_dict()`), and `provenance`.

Build with `OperationResult.ok(...)` / `OperationResult.fail(...)`; test with
`bool(result)`; serialize with `result.to_dict()` (deterministic).