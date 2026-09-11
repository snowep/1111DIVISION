# scripts/

Operational scripts only — no application code. Every script must be
idempotent and safe to re-run.

- `check_structure.py` — validates repo structure against
  `docs/STRUCTURE.md` (R1–R7). Exit 0 = conforms.

Run the check before committing:

```bash
python scripts/check_structure.py
```