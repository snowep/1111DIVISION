"""Workspace-aware filesystem IO with read/write authority boundary.

Semantics (see docs/ARCHITECTURE.md):
- ``resolve()`` returns a canonical absolute path inside one of the allowed
  roots. Any traversal (``..``, absolute jump, symlink escape, UNC drive
  change) raises EscapeError.
- Reads are always allowed (with the root check).
- Writes require passing an ``authority`` context (e.g. an Identity or a
  validated mutation permit). Without authority, mutation raises
  MutationDeniedError. This makes the boundary explicit and inspectable:
  the kernel never writes outside an authorized scope.
- Everything is deterministic: no silent symlink-following, no magic cwd.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Optional

from jarvis.errors import EscapeError, MutationDeniedError, NotFoundError, PathError


@dataclass(frozen=True)
class Authority:
    """The acting authority for a mutation (or None for read-only ops)."""

    kind: str  # e.g. "identity", "system", "tool"
    name: str
    scope: str  # path the authority is permitted to mutate

    def __str__(self) -> str:
        return f"{self.kind}:{self.name}"

    def permits(self, target: Path) -> bool:
        try:
            target.resolve().relative_to(Path(self.scope).resolve())
            return True
        except ValueError:
            return False


class WorkspaceResolver:
    """Canonical root + safe path resolution for the sandbox.

    ``aliases`` maps semantic top-level names (e.g. ``vault``, ``council``,
    ``skills``, ``core``) to their canonical locations under ``.jarvis/``.
    Resolving ``vault/episodic/a.md`` therefore hits
    ``<root>/.jarvis/vault/episodic/a.md`` — the real canonical vault.
    """

    def __init__(self, root: str | Path, allowed: Iterable[str] = (), aliases: Optional[dict[str, str | Path]] = None) -> None:
        self.root = Path(root).resolve()
        self._allowed: list[Path] = [self.root]
        for extra in allowed:
            p = Path(extra).resolve()
            try:
                p.relative_to(self.root)
            except ValueError:
                raise EscapeError(f"allowed path outside root: {p}")
            self._allowed.append(p)
        self._allowed = sorted(set(self._allowed))
        self.aliases: dict[str, Path] = {}
        for name, target in (aliases or {}).items():
            t = Path(target).resolve()
            if not self._within(t):
                raise EscapeError(f"alias '{name}' target outside allowed roots: {t}")
            self.aliases[name] = t

    # ----------------------------------------------------------------- res
    def resolve(self, rel: str | Path) -> Path:
        """Resolve a relative path against the canonical root (read-only).

        A leading alias segment (``vault/...``) is redirected to its
        canonical directory; everything else is relative to ``self.root``.
        """
        p = Path(rel)
        if p.is_absolute():
            raise EscapeError(f"absolute paths are not allowed: {rel!r}")
        parts = PurePosixPath(rel).as_posix().split("/")
        if ".." in parts:
            raise EscapeError(f"traversal attempt blocked: {rel!r}")
        base: Path = self.root
        if parts and parts[0] in self.aliases:
            base = self.aliases[parts[0]]
            rest = "/".join(parts[1:])
            candidate = (base / rest).resolve(strict=False)
        else:
            candidate = (self.root / PurePosixPath(rel)).resolve(strict=False)
        if not self._within(candidate):
            raise EscapeError(f"path escapes workspace root: {rel!r}")
        return candidate

    def resolve_read(self, rel: str | Path) -> Path:
        target = self.resolve(rel)
        if not target.exists():
            raise NotFoundError(f"not found: {rel}", path=rel)
        return target

    def resolve_write(self, rel: str | Path, authority: Optional[Authority]) -> Path:
        target = self.resolve(rel)
        if authority is None:
            raise MutationDeniedError(
                "write requires authority (an explicit Identity/mutation permit)",
                path=rel,
            )
        if not authority.permits(target):
            raise MutationDeniedError(
                f"authority {authority} not permitted to mutate {target} "
                f"(scope: {authority.scope})",
                path=rel,
            )
        return target

    # -------------------------------------------------------------- helpers
    def _within(self, target: Path) -> bool:
        for allowed in self._allowed:
            try:
                target.relative_to(allowed)
                return True
            except ValueError:
                continue
        return False

    def list_relative(self, sub: str | Path = ".") -> list[str]:
        """Return posix relpaths of all files under a workspace subpath."""
        base = self.resolve(str(sub)) if str(sub) != "." else self.root
        if not base.is_dir():
            return []
        out: list[str] = []
        for p in sorted(base.rglob("*")):
            if p.is_file():
                # always report paths relative to the workspace ROOT
                try:
                    out.append(p.relative_to(self.root).as_posix())
                except ValueError:
                    continue
        return out


class SafeIO:
    """Read/write helpers bound to a resolver + authority model."""

    def __init__(self, resolver: WorkspaceResolver) -> None:
        self.resolver = resolver

    def read_text(self, rel: str | Path) -> str:
        target = self.resolver.resolve_read(rel)
        return target.read_text(encoding="utf-8")

    def write_text(
        self,
        rel: str | Path,
        text: str,
        authority: Optional[Authority] = None,
    ) -> Path:
        target = self.resolver.resolve_write(rel, authority)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, target)
        return target