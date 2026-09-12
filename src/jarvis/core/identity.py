"""Identity loader: reads JARVIS identity ONLY from .jarvis/core.

Hard architectural rule (Phase 10 constraint): identity comes exclusively
from the canonical `.jarvis/core` directory. Open WebUI configuration,
environment variables, or any other host-layer config is NEVER treated as
the identity source.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from jarvis.errors import IdentityError


@dataclass
class Identity:
    name: str
    role: str
    version: str
    core_dir: Path
    capabilities: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def id_string(self) -> str:
        return f"{self.name}@{self.role}"


def load_identity(core_dir: str | Path) -> Identity:
    """Load canonical identity from .jarvis/core.

    Preferred file: core/identity.json. Falls back to core/identity.md
    (YAML-subset frontmatter) for Obsidian-native identity documents.
    Raises IdentityError on any absence/corruption — never approximates.
    """
    core = Path(core_dir)
    if not core.is_dir():
        raise IdentityError(f"core directory missing: {core}", path=str(core))

    json_file = core / "identity.json"
    md_file = core / "identity.md"

    if json_file.is_file():
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise IdentityError(f"corrupt identity.json: {exc}", path=str(json_file))
        return _identity_from_dict(data, core)

    if md_file.is_file():
        try:
            from jarvis.docstore.models import parse_document
            doc = parse_document(md_file.name, md_file.read_text(encoding="utf-8"))
        except Exception as exc:
            raise IdentityError(f"corrupt identity.md: {exc}", path=str(md_file))
        return _identity_from_dict(doc.metadata, core)

    raise IdentityError(
        f"no identity found in core dir {core} "
        "(expected core/identity.json or core/identity.md)",
        path=str(core),
    )


def _identity_from_dict(data: dict[str, Any], core: Path) -> Identity:
    for required in ("name", "role", "version"):
        if required not in data:
            raise IdentityError(f"identity missing required field '{required}'")
    caps = data.get("capabilities") or []
    if not isinstance(caps, list):
        caps = [caps]
    return Identity(
        name=str(data["name"]),
        role=str(data["role"]),
        version=str(data["version"]),
        core_dir=core,
        capabilities=[str(c) for c in caps],
        extra={k: v for k, v in data.items()
               if k not in ("name", "role", "version", "capabilities")},
    )