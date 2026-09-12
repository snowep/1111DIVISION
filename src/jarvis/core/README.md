# core/

Authoritative JARVIS identity and configuration.

- `identity.py` — `load_identity(core_dir)` reads identity **only** from
  `.jarvis/core` (`identity.json` or `identity.md`).

Hard rule: Open WebUI configuration, environment variables, or any other
host-layer config are **never** treated as the identity source. Identity
comes exclusively from the canonical `.jarvis/core` directory.