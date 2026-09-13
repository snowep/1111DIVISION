"""Skills: capability manifests + permission model + derived registry.

A skill is a directory under <root>/skills/<name>/ containing:
    skill.md       -- manifest (frontmatter: name, version, description,
                      trigger, params, permissions, entry)
    impl           -- implementation file (Python or JS)

skills/registry.md is DERIVED — rebuilt deterministically from the skills
directories on every scan. It is never hand-edited and never authoritative.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from jarvis.docstore.models import DocError, parse_document

_SHORT_PERMS = ("filesystem", "terminal", "network", "memory")
_ALLOWED_PERMS = {"read", "write", "execute", "no"}

# Long permission name (what check_permission() takes) -> short manifest key.
_LONG_TO_SHORT: dict[str, str] = {
    "filesystem.read": "filesystem",
    "filesystem.write": "filesystem",
    "terminal.execute": "terminal",
    "network.read": "network",
    "network.write": "network",
    "memory.read": "memory",
    "memory.write": "memory",
}

# Permission semantics:
#   filesystem.read  = may read files
#   filesystem.write = may write/modify files
#   terminal.execute = may run shell commands
#   network.read     = may fetch URLs (GET)
#   network.write    = may POST/PUT/DELETE to remote
#   memory.read      = may read vault/notes
#   memory.write     = may create/update/delete vault notes
PERMISSION_MEANING: dict[str, str] = {
    "filesystem.read": "read files on the local filesystem",
    "filesystem.write": "create/update/delete local files",
    "terminal.execute": "run shell commands (timed, sandboxed)",
    "network.read": "fetch URLs (GET)",
    "network.write": "send data to remote URLs (POST/PUT/DELETE)",
    "memory.read": "read vault notes",
    "memory.write": "create/update/delete vault notes",
}


class SkillError(Exception):
    """Raised when a skill manifest is invalid or a permission is denied."""


@dataclass
class SkillManifest:
    """Validated skill manifest."""

    name: str
    version: str
    description: str = ""
    trigger: str = ""
    params: list[str] = field(default_factory=list)
    permissions: dict[str, str] = field(default_factory=dict)
    entry: str = ""
    source: str = ""  # provenance, e.g. "local" or "github:owner/repo"
    status: str = "active"


def _validate_short_key(short: str) -> str:
    """Validate a short permission key from a manifest (e.g. 'filesystem')."""
    if short not in _SHORT_PERMS:
        raise SkillError(f"unknown permission key {short!r}; expected one of {_SHORT_PERMS}")
    return short


def _validate_perm_value(value: Any) -> str:
    """Coerce a raw permission value to a canonical level.

    Accepts the literal ``None`` (parser maps YAML ``none`` to Python
    ``None``) as the explicit "no permission" level.
    """
    if value is None or (isinstance(value, str) and value.strip().lower() in ("none", "no")):
        return "no"
    v = str(value).strip().lower()
    if v not in _ALLOWED_PERMS:
        raise SkillError(f"invalid permission value {value!r}; expected one of {sorted(_ALLOWED_PERMS)}")
    return v


def _coerce_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def parse_manifest(md_text: str) -> SkillManifest:
    """Parse + validate a skill.md manifest string (frontmatter)."""
    doc = parse_document("skill.md", md_text)
    m = doc.metadata
    name = str(m.get("name", "")).strip()
    if not name:
        raise SkillError("skill.md missing required frontmatter field 'name'")
    perms: dict[str, str] = {}
    raw_perms = m.get("permissions")
    if raw_perms is None:
        raw_perms = {}
    if isinstance(raw_perms, dict):
        for k, v in raw_perms.items():
            key = _validate_short_key(str(k))
            perms[key] = _validate_perm_value(str(v))
    elif isinstance(raw_perms, list):
        # Allow ["filesystem.read", "network.read"] shorthand -> grant those.
        for item in raw_perms:
            short = _LONG_TO_SHORT.get(str(item))
            if short is None:
                raise SkillError(f"unknown permission {item!r}; expected one of {sorted(_LONG_TO_SHORT)}")
            perms[short] = "read" if "read" in str(item) else "write"
    elif isinstance(raw_perms, str):
        for item in raw_perms.replace(",", " ").split():
            short = _LONG_TO_SHORT.get(item)
            if short is None:
                raise SkillError(f"unknown permission {item!r}; expected one of {sorted(_LONG_TO_SHORT)}")
            perms[short] = "read" if "read" in item else "write"
    else:
        raise SkillError(f"invalid permissions type: {type(raw_perms).__name__}")

    entry = str(m.get("entry", "")).strip()
    return SkillManifest(
        name=name,
        version=str(m.get("version", "0.1.0")),
        description=str(m.get("description", "")).strip(),
        trigger=str(m.get("trigger", "")).strip(),
        params=_coerce_str_list(m.get("params")),
        permissions=perms,
        entry=entry,
        source=str(m.get("source", "local")).strip(),
        status=str(m.get("status", "active")).strip().lower(),
    )


# ---------------------------------------------------------------------------
# Skill directory loading
# ---------------------------------------------------------------------------
def _read_manifest_file(skill_dir: Path) -> SkillManifest:
    md = skill_dir / "skill.md"
    if not md.is_file():
        raise SkillError(f"skill {skill_dir.name}: missing skill.md manifest")
    return parse_manifest(md.read_text(encoding="utf-8"))


def load_skill(skill_dir: Path) -> SkillManifest:
    """Load + validate a single skill directory."""
    manifest = _read_manifest_file(skill_dir)
    if manifest.name != skill_dir.name:
        # Allow name != dirname, but keep dirname as canonical path key
        pass
    if manifest.entry and not (skill_dir / manifest.entry).is_file():
        raise SkillError(f"skill {skill_dir.name}: entry file {manifest.entry!r} not found")
    return manifest


def load_skills(root: str | Path) -> list[SkillManifest]:
    """Scan <root>/skills/* and load every valid skill manifest.

    Invalid skills (missing/invalid skill.md) are skipped, and a warning is
    recorded in the derived registry so the scan stays deterministic.
    """
    root = Path(root)
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        return []
    skills: list[SkillManifest] = []
    for d in sorted(skills_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        try:
            skills.append(load_skill(d))
        except (SkillError, DocError) as exc:
            # Keep the scan deterministic: silently skip + note in registry.
            skills.append(
                SkillManifest(
                    name=d.name,
                    version="0.0.0",
                    description=f"(invalid) {exc}",
                    status="invalid",
                )
            )
    return skills


# ---------------------------------------------------------------------------
# Permission enforcement
# ---------------------------------------------------------------------------
def check_permission(manifest: SkillManifest, permission: str) -> None:
    """Raise SkillError if the skill does not have the given permission.

    `permission` is a long-form name like 'filesystem.read'. The manifest
    stores short keys ('filesystem') with a value of read|write|execute|no.
    Semantics:
      filesystem.read  granted by value in {read, write}
      filesystem.write granted by value == write
      network.read     granted by value in {read, write}
      network.write    granted by value == write
      memory.read      granted by value in {read, write}
      memory.write     granted by value == write
      terminal.execute granted by value == execute
    """
    if permission not in _LONG_TO_SHORT:
        raise SkillError(f"unknown permission {permission!r}; expected one of {sorted(_LONG_TO_SHORT)}")
    short = _LONG_TO_SHORT[permission]
    value = manifest.permissions.get(short)
    if value is None:
        raise SkillError(
            f"skill '{manifest.name}' lacks permission {permission} "
            f"(granted: {manifest.permissions or '(none)'})"
        )
    if value == "no":
        raise SkillError(f"skill '{manifest.name}' explicitly denies {permission}")
    granted = _is_granted(permission, value)
    if not granted:
        raise SkillError(
            f"skill '{manifest.name}' permission {permission} requires value "
            f"{_required_value(permission)}, got {value!r}"
        )


def _is_granted(long_name: str, value: str) -> bool:
    if value not in ("read", "write", "execute"):
        return False
    if long_name.endswith("write"):
        return value == "write"
    if long_name == "terminal.execute":
        return value == "execute"
    return value in ("read", "write")  # read grants


def _required_value(long_name: str) -> str:
    if long_name.endswith("write"):
        return "write"
    if long_name == "terminal.execute":
        return "execute"
    return "read or write"


def allowed_permissions(manifest: SkillManifest) -> set[str]:
    """Return the set of long-form permissions a skill can actually exercise."""
    out: set[str] = set()
    for long_name in _LONG_TO_SHORT:
        short = _LONG_TO_SHORT[long_name]
        value = manifest.permissions.get(short)
        if value is not None and _is_granted(long_name, value):
            out.add(long_name)
    return out


# ---------------------------------------------------------------------------
# Derived registry
# ---------------------------------------------------------------------------
def _registry_markdown(skills: list[SkillManifest], scanned_at: str) -> str:
    lines = [
        "# Skill Registry",
        "",
        "> **DERIVED** — rebuilt deterministically from `skills/*/skill.md`.",
        "> Do not hand-edit. To add a skill, create a skill directory.",
        "",
        f"Scanned at: {scanned_at}",
        f"Skills found: {len([s for s in skills if s.status == 'active'])} active, "
        f"{len([s for s in skills if s.status != 'active'])} inactive/invalid",
        "",
        "| Skill | Version | Status | Permissions | Description |",
        "|---|---|---|---|---|",
    ]
    for s in sorted(skills, key=lambda x: x.name):
        perms = ",".join(f"{k}={v}" for k, v in sorted(s.permissions.items())) or "—"
        desc = s.description.replace("|", "/").replace("\n", " ")
        lines.append(f"| {s.name} | {s.version} | {s.status} | {perms} | {desc} |")
    lines.append("")
    return "\n".join(lines)


def rebuild_registry(root: str | Path) -> dict[str, Any]:
    """Scan skills/ and rebuild the DERIVED registry (registry.md + registry.json).

    Returns a summary dict. Never treats the old registry as source.
    """
    root = Path(root)
    skills_dir = root / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    skills = load_skills(root)
    scanned_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    md = _registry_markdown(skills, scanned_at)
    (root / "skills" / "registry.md").write_text(md, encoding="utf-8")
    data = {
        "scanned_at": scanned_at,
        "skills": [
            {
                "name": s.name,
                "version": s.version,
                "status": s.status,
                "description": s.description,
                "permissions": s.permissions,
                "entry": s.entry,
                "source": s.source,
            }
            for s in skills
        ],
    }
    (root / "skills" / "registry.json").write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return data