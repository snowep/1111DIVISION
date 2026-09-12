"""Canonical root resolution for the JARVIS runtime.

The kernel works against ONE resolved workspace root (the repo root that
contains `.jarvis/`, `vault/`, `council/`, `src/`, `tests/`, `docs/`).
Resolution order (deterministic, never guesses):

1. explicit ``root`` argument
2. ``JARVIS_ROOT`` environment variable (if set and absolute)
3. walk up from cwd to find the first directory containing ``.jarvis/``
4. fall back to cwd

The resolver also exposes the standard sub-roots used by the architecture:
``.jarvis`` (runtime state), ``vault`` (canonical notes), ``council``
(seat configs), ``src``, ``tests``, ``docs``.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from jarvis.errors import EscapeError, NotFoundError


@dataclass(frozen=True)
class Roots:
    """Canonical root plus named sub-roots."""

    root: Path
    jarvis: Path
    vault: Path
    council: Path
    src: Path
    tests: Path
    docs: Path

    def sub(self, name: str) -> Path:
        return self.root / name


def _find_root_from_cwd(cwd: Path) -> Path | None:
    """Walk up from cwd to find the first dir that has .jarvis/."""
    cur = cwd.resolve()
    while True:
        if (cur / ".jarvis").is_dir():
            return cur
        if cur.parent == cur:
            return None
        cur = cur.parent


def resolve_root(root: str | Path | None = None) -> Roots:
    """Resolve the canonical workspace root and build the Roots bundle."""
    if root is not None:
        candidate = Path(root).expanduser().resolve()
    else:
        env = os.environ.get("JARVIS_ROOT")
        if env:
            candidate = Path(env).expanduser().resolve()
        else:
            found = _find_root_from_cwd(Path.cwd())
            if found is None:
                candidate = Path.cwd().resolve()
            else:
                candidate = found

    if not candidate.is_dir():
        raise NotFoundError(f"workspace root not a directory: {candidate}", path=str(candidate))

    jarvis = candidate / ".jarvis"
    return Roots(
        root=candidate,
        jarvis=jarvis,
        vault=jarvis / "vault",
        council=jarvis / "council",
        src=candidate / "src",
        tests=candidate / "tests",
        docs=candidate / "docs",
    )


def assert_no_escape(target: Path, roots: Roots) -> None:
    """Guard: a resolved path must live under one of the allowed roots."""
    allowed = [roots.root, roots.jarvis, roots.vault, roots.council]
    for base in allowed:
        try:
            target.resolve().relative_to(base.resolve())
            return
        except ValueError:
            continue
    raise EscapeError(f"path escapes allowed roots: {target}")