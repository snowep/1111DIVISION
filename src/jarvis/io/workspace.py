"""Workspace resolver — canonical repository root + path confinement.

Every canonical location lives under one root.  The resolver:

1. Detects the repository root (the directory containing ``.git`` — the
   project anchor)
2. Registers named anchors (``.jarvis/``, ``vault/``, ``council/``,
   ``src/``, ``tests/``, ``docs/``) so callers address files by anchor,
   never by free-form relative path that could escape.
3. Confines every resolved path inside the root.  ``..`` segments that
   escape, absolute paths outside the root, symlinks that leave the root,
   and drive violations on Windows are all rejected.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from jarvis.errors import (
    PathEscapeError,
    PathNotFoundError,
    UnknownAnchorError,
)

# Default workspace anchors (relative to the repository root).
# Each anchor is the first component of any valid relative path.
_DEFAULT_ANCHORS: tuple[str, ...] = (
    ".git",
    ".jarvis",
    "vault",
    "council",
    "src",
    "tests",
    "docs",
)

# Anchors that are always read-only from the kernel's perspective (never
# written to, even by WriteBoundary, unless the caller explicitly unlocks
# them with an explicit override flag).
_PROTECTED_ANCHORS = frozenset({".jarvis"})

_UNSAFE_COMPONENTS = frozenset({"..", "~"})


def detect_repository_root(start: Path | None = None) -> Path:
    """Walk up from *start* until a directory containing ``.git`` is found.

    The repository root is the workspace root.  Raises
    :class:`PathNotFoundError` if no ``.git`` directory is found before
    the filesystem root.
    """
    current = (start or Path.cwd()).resolve()
    while True:
        if (current / ".git").is_dir():
            return current
        parent = current.parent
        if parent == current:
            raise PathNotFoundError(
                f"No .git directory found walking up from {current!r}.",
                path=str(current),
                code="no_git_root",
            )
        current = parent


def _is_within(child: Path, ancestor: Path) -> bool:
    """Return True if *child* is inside *ancestor* (or equal)."""
    try:
        child.relative_to(ancestor)
        return True
    except ValueError:
        return False


@dataclass(frozen=True)
class MatchedAnchor:
    """A resolved path snapped to its registered anchor."""

    anchor: str          # e.g. ".jarvis", "vault"
    anchor_path: Path     # absolute path of the anchor directory
    relative_inside: str  # path inside the anchor (may be "" when path == anchor)
    absolute_path: Path   # fully resolved, guaranteed inside root

    def to_dict(self) -> dict:
        return {
            "anchor": self.anchor,
            "anchor_path": str(self.anchor_path),
            "relative_inside": self.relative_inside,
            "absolute_path": str(self.absolute_path),
        }


class Workspace:
    """A confined view of the repository rooted at *root*.

    All paths are normalized to absolute and guaranteed inside the root.
    Resolvers return :class:`MatchedAnchor` tuples ready for I/O.
    """

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        if not self._root.exists():
            raise PathNotFoundError(
                f"Workspace root does not exist: {self._root!r}",
                path=str(self._root),
                code="workspace_root_missing",
            )
        self._anchors: dict[str, Path] = {}
        for name in _DEFAULT_ANCHORS:
            path = self._root / name
            self._anchors[name] = path

    # -- path confinement --------------------------------------------------

    @property
    def root(self) -> Path:
        return self._root

    def anchor(self, name: str) -> Path:
        """Return the absolute path of a registered anchor, or raise."""
        if name not in self._anchors:
            raise UnknownAnchorError(
                f"Unknown anchor {name!r}; known anchors: {sorted(self._anchors)}.",
                path=name,
                code="unknown_anchor",
            )
        return self._anchors[name]

    def anchors(self) -> dict[str, Path]:
        """Return a copy of all registered anchors."""
        return dict(self._anchors)

    def resolve(self, candidate: str | Path) -> Path:
        """Resolve *candidate* to an absolute path confined inside the root.

        The candidate can be:
        - a relative path (from the workspace root)
        - an absolute path already inside the root
        - a ``~``-prefixed path (home-relative; refused)

        Raises
        ------
        PathEscapeError
            If the resolved path is outside the root, uses ``..`` to
            escape, or uses an absolute path outside the workspace.
        """
        raw = str(candidate).strip()
        if not raw:
            raise PathEscapeError(
                "Empty path candidate.",
                path=raw,
                code="empty_path",
            )

        raw = raw.replace("\\", "/")

        # Internal escape detection: any '..' segment is an escape attempt.
        if _UNSAFE_COMPONENTS & set(raw.split("/")):
            # Check whether .. is conceptual or literal: ".." segments in
            # a path that would resolve inside root are still refused
            # because the architecture treats them as suspicious.
            raise PathEscapeError(
                f"Path contains an escape component ('..' or '~'): {raw!r}.",
                path=raw,
                code="escape_component",
            )

        # Resolve — os.path.normpath + realpath handles junctions/symlinks
        try:
            resolved = Path(raw)
            if not resolved.is_absolute():
                resolved = (Path(self._root) / resolved).resolve()
            else:
                resolved = resolved.resolve()
        except (OSError, RuntimeError, TypeError) as exc:
            raise PathEscapeError(
                f"Could not resolve path {raw!r}: {exc}",
                path=raw,
                code="resolve_failed",
            ) from exc

        if not _is_within(resolved, self._root):
            raise PathEscapeError(
                f"Path {raw!r} resolves outside the workspace root "
                f"{str(self._root)!r}: {str(resolved)!r}",
                path=raw,
                code="outside_root",
            )

        return resolved

    def resolve_inside(self, candidate: str | Path) -> MatchedAnchor:
        """Resolve *candidate* and snap it to its registered anchor.

        Raises UnknownAnchorError if the resolved path is inside the root
        but not under any registered anchor.
        """
        absolute = self.resolve(candidate)
        return self._snap_to_anchor(absolute)

    def _snap_to_anchor(self, absolute: Path) -> MatchedAnchor:
        """Match an absolute path to its registered anchor."""
        for name, anchor_path in self._anchors.items():
            if _is_within(absolute, anchor_path):
                rel = absolute.relative_to(anchor_path)
                return MatchedAnchor(
                    anchor=name,
                    anchor_path=anchor_path,
                    relative_inside=str(rel).replace("\\", "/"),
                    absolute_path=absolute,
                )
        raise UnknownAnchorError(
            f"Path {str(absolute)!r} is inside the workspace root but does not "
            f"match any registered anchor.",
            path=str(absolute),
            code="no_matching_anchor",
        )

    # -- read -------------------------------------------------------------

    def resolve_read(self, candidate: str | Path, must_exist: bool = True) -> Path:
        """Confined read resolution.  Raises if the path escapes the root."""
        path = self.resolve(candidate)
        if must_exist and not path.exists():
            raise PathNotFoundError(
                f"Path not found: {path!r}",
                path=str(candidate),
                code="path_not_found",
            )
        return path

    # -- anchor-relative convenience ---------------------------------------

    def jarvis(self) -> Path:
        return self.anchor(".jarvis")

    def vault(self) -> Path:
        return self.anchor("vault")

    def council(self) -> Path:
        return self.anchor("council")

    def src(self) -> Path:
        return self.anchor("src")

    def tests(self) -> Path:
        return self.anchor("tests")

    def docs(self) -> Path:
        return self.anchor("docs")

    def core(self) -> Path:
        return self.anchor(".jarvis") / "core"

    def personas(self) -> Path:
        return self.anchor(".jarvis") / "personas"

    def persona_definitions(self) -> Path:
        return self.personas() / "definitions"

    def memory(self, category: str) -> Path:
        """Return the path to a canonical memory category directory."""
        return self.anchor(".jarvis") / "memory" / category

    def skills(self, category: str | None = None) -> Path:
        base = self.anchor(".jarvis") / "skills"
        if category:
            return base / category
        return base

    def state(self, filename: str) -> Path:
        return self.anchor(".jarvis") / "state" / filename

    def __repr__(self) -> str:
        return f"Workspace(root={self._root!r})"