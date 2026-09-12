"""Tests enforcing the strict sandbox structure (docs/STRUCTURE.md)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from check_structure import check  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent


def _make_tree(base: Path, files: dict[str, str]) -> None:
    """Create a directory tree from {relative_path: content}."""
    for rel, content in files.items():
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


CONFORMING = {
    "README.md": "# x",
    "pyproject.toml": "[project]",
    ".gitignore": "",
    "docs/README.md": "# docs",
    "docs/STRUCTURE.md": "# s",
    "scripts/README.md": "# scripts",
    "scripts/check_structure.py": "",
    "src/jarvis/__init__.py": "",
    "src/jarvis/cli.py": "",
    "tests/README.md": "# tests",
    "tests/test_models.py": "",
    "app/README.md": "# app",
}


def test_repo_root_conforms():
    """The repository itself must currently conform — no violations allowed."""
    assert check(REPO_ROOT) == []


def test_stray_file_at_root_is_violation(tmp_path):
    _make_tree(tmp_path, CONFORMING)
    (tmp_path / "_probe.py").write_text("x = 1", encoding="utf-8")
    assert any(v.startswith("RULE R4") and "_probe.py" in v for v in check(tmp_path))


def test_missing_readme_is_violation(tmp_path):
    _make_tree(tmp_path, CONFORMING)
    (tmp_path / "scripts" / "README.md").unlink()
    assert any("scripts/ has no README.md" in v for v in check(tmp_path))


def test_non_markdown_in_docs_is_violation(tmp_path):
    _make_tree(tmp_path, CONFORMING)
    (tmp_path / "docs" / "notes.txt").write_text("x", encoding="utf-8")
    assert any("docs/ contains non-Markdown" in v for v in check(tmp_path))


def test_unexpected_root_dir_is_violation(tmp_path):
    _make_tree(tmp_path, CONFORMING)
    (tmp_path / "cache").mkdir()
    assert any("unexpected directory at root: cache" in v for v in check(tmp_path))


def test_python_in_app_is_violation(tmp_path):
    _make_tree(tmp_path, CONFORMING)
    (tmp_path / "app" / "x.py").write_text("x = 1", encoding="utf-8")
    assert any("app/ contains Python file" in v for v in check(tmp_path))


def test_missing_package_init_is_violation(tmp_path):
    _make_tree(tmp_path, CONFORMING)
    (tmp_path / "src" / "jarvis" / "__init__.py").unlink()
    assert any("src/jarvis/__init__.py missing" in v for v in check(tmp_path))