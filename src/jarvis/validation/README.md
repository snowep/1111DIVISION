# validation/

Frontmatter-typed loading + integrity checks.

- `loader.py` — `load_document()` / `load_all()` parse Markdown-with-YAML
  into typed `LoadedDocument`s and enforce:
  - required fields (`MissingFieldError`)
  - duplicate IDs across the vault (`DuplicateIdError`)
  - allowed status values (`InvalidStatusError`)
  - broken references (`BrokenRefError`, via `validate_refs()` against a
    known-path set)

Malformed frontmatter raises `ParseError`; a docstore failure is classified
to the precise kernel error (`NOT_FOUND`, `PATH_ESCAPE`, `PARSE_ERROR`,
`CORRUPT_STATE`). Corrupted state is **never silently repaired**.