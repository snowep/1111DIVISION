# errors/

Typed, inspectable error hierarchy for the runtime kernel.

Every failure mode has a stable machine-readable `code`. The kernel never
silently repairs corrupted state — it raises a typed error carrying a full
diagnostic (`path`, `detail`, `message`).

| Class | Code | Meaning |
|---|---|---|
| `EscapeError` | `PATH_ESCAPE` | path traversal / symlink / UNC escape |
| `NotFoundError` | `NOT_FOUND` | target does not exist |
| `ParseError` | `PARSE_ERROR` | frontmatter / YAML-subset malformed |
| `MissingFieldError` | `MISSING_FIELD` | required metadata field absent |
| `DuplicateIdError` | `DUPLICATE_ID` | same id in two documents |
| `InvalidStatusError` | `INVALID_STATUS` | status not in allowed set |
| `BrokenRefError` | `BROKEN_REF` | reference to unknown relpath |
| `MutationDeniedError` | `MUTATION_DENIED` | write without in-scope authority |
| `CorruptStateError` | `CORRUPT_STATE` | source of truth corrupt; not auto-repaired |
| `IdentityError` | `IDENTITY_ERROR` | identity missing / corrupt / partial |
| `ContextError` | `CONTEXT_ERROR` | context priority violation |

All inherit from `JarvisError`. Use `err.to_dict()` for structured reporting
into `OperationResult.errors`.