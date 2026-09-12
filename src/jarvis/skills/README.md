# skills/

Capability manager: manifest + permission model + derived registry.

- `skill.py` — `SkillManifest`, `parse_manifest()`, `load_skill(s)`,
  `check_permission()`, `allowed_permissions()`, `rebuild_registry()`.

A skill is a directory under `.jarvis/skills/<name>/` containing `skill.md`
(manifest) and an implementation file. The registry is derived and rebuilt on
scan; it is never hand-edited.

See `docs/ROADMAP.md` (P2) for design decisions.