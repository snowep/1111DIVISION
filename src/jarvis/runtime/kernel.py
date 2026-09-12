"""Deterministic runtime kernel: resolve roots, build IO, load identity.

This is the instantiation point for the whole Phase 10 kernel. It produces
a single ``Runtime`` object with:

- roots:        canonical root bundle
- resolver:     WorkspaceResolver (path confinement)
- io:           SafeIO bound to the resolver
- identity:     Identity loaded from .jarvis/core ONLY
- context:      ContextBuilder (assembles the ordered prompt context)

Everything is eager and validated at startup; any failure raises a typed
error rather than leaving the runtime half-initialized.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from jarvis.core.identity import Identity, load_identity
from jarvis.errors import JarvisError
from jarvis.io.workspace import SafeIO, WorkspaceResolver
from jarvis.runtime.roots import Roots, resolve_root


@dataclass
class Runtime:
    roots: Roots
    resolver: WorkspaceResolver
    io: SafeIO
    identity: Identity
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    @property
    def root(self) -> Path:
        return self.roots.root

    def new_operation_id(self) -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        return f"{stamp}-{uuid.uuid4().hex[:8]}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "root": str(self.root),
            "identity": {
                "name": self.identity.name,
                "role": self.identity.role,
                "version": self.identity.version,
            },
        }


def build_runtime(root: str | Path | None = None) -> Runtime:
    """Build the full runtime kernel from a workspace root."""
    roots = resolve_root(root)
    resolver = WorkspaceResolver(
        roots.root,
        [str(roots.jarvis), str(roots.vault), str(roots.council)],
        aliases={
            "vault": roots.vault,
            "council": roots.council,
            "skills": roots.jarvis / "skills",
            "core": roots.jarvis / "core",
            "learn": roots.jarvis / "learn",
        },
    )
    io = SafeIO(resolver)
    identity = load_identity(roots.jarvis / "core")
    return Runtime(
        roots=roots,
        resolver=resolver,
        io=io,
        identity=identity,
    )