# tests/

Pytest suite. Tests mirror the packages under `src/` one level deep.
Run from the repository root:

```bash
python -m pytest -q
```

- `test_structure.py` — enforces sandbox structure (must always pass).
- `test_models.py`, `test_store.py`, `test_learn.py` — docstore + learn engine.