"""Enforce the strict sandbox structure defined in docs/STRUCTURE.md.

Usage:
    python scripts/check_structure.py [root]

Exit 0 if the structure conforms, 1 if any rule is violated. Every
violation is printed as ``RULE Rn: detail``. Deterministic, no dependencies.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT_ALLOWED_FILES = {"README.md", "pyproject.toml", ".gitignore"}
ROOT_ALLOWED_DIRS = {"docs", "scripts", "src", "tests"}
TOP_LEVEL_DIRS = ("docs", "scripts", "src", "tests")


def _walk(root: Path):
    """Yield files under root, skipping ignored tooling dirs."""
    for p in sorted(root.rglob("*")):
        if any(part in {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"} for part in p.parts):
            continue
        yield p


def check(root: Path) -> list[str]:
    """Return a list of rule violations. Empty list = conforms."""
    violations: list[str] = []
    if not root.is_dir():
        return [f"RULE R0: root is not a directory: {root}"]

    # R4: repo root allows exactly README.md, pyproject.toml, .gitignore + dirs.
    for entry in sorted(root.iterdir()):
        name = entry.name
        if entry.is_dir():
            if name in (".git", ".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache"):
                continue  # tooling/version-control internals
            if name in ROOT_ALLOWED_DIRS:
                continue
            violations.append(f"RULE R4: unexpected directory at root: {name}")
        else:
            if name in ROOT_ALLOWED_FILES:
                continue
            violations.append(f"RULE R4: stray file at root: {name}")

    # R5: every top-level directory contains a README.md.
    for d in TOP_LEVEL_DIRS:
        dir_path = root / d
        if not dir_path.is_dir():
            violations.append(f"RULE R5: required directory missing: {d}/")
            continue
        if not (dir_path / "README.md").is_file():
            violations.append(f"RULE R5: {d}/ has no README.md")

    # R3/R7: docs/ contains Markdown only.
    docs = root / "docs"
    if docs.is_dir():
        for p in _walk(docs):
            if p.is_file() and p.suffix.lower() != ".md":
                violations.append(f"RULE R3: docs/ contains non-Markdown file: {p.relative_to(root)}")

    # R3: scripts/ contains only .py and .md files.
    scripts = root / "scripts"
    if scripts.is_dir():
        for p in _walk(scripts):
            if p.is_file() and p.suffix.lower() not in (".py", ".md"):
                violations.append(f"RULE R3: scripts/ contains unexpected file: {p.relative_to(root)}")

    # R3: tests/ contains no non-python, non-md, non-.ini files.
    tests = root / "tests"
    if tests.is_dir():
        for p in _walk(tests):
            if p.is_file() and p.suffix.lower() not in (".py", ".md", ".ini", ".cfg", ".txt"):
                violations.append(f"RULE R3: tests/ contains unexpected file: {p.relative_to(root)}")

    # R4: no Python files anywhere at the repo root.
    for p in sorted(root.glob("*.py")):
        violations.append(f"RULE R4: python file at repo root: {p.name}")

    # R6: implementation package exists and is importable-shaped.
    pkg_init = root / "src" / "jarvis" / "__init__.py"
    if not pkg_init.is_file():
        violations.append("RULE R6: src/jarvis/__init__.py missing")

    return sorted(violations)


def main(argv: list[str] | None = None) -> int:
    root = Path(argv[0]) if argv and argv[0] else Path(__file__).resolve().parent.parent
    violations = check(root)
    if violations:
        for v in violations:
            print(v)
        print(f"FAILED: {len(violations)} structure violation(s)")
        return 1
    print("OK: sandbox structure conforms to docs/STRUCTURE.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))