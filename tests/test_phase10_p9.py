"""P9 — Self-evolution tests (hermetic, no real git/pytest needed).

Exercises the propose → validate → apply → revert pipeline:
- propose() builds a pure Proposal with FileChanges.
- validate() runs gates against a SCRATCH mirror with the proposal applied
  (never the real tree); pytest/structure results are captured.
- apply() refuses without approval; applies on approval, commits, records
  hash.
- A proposal cannot be applied twice.
- FileChange create refuses-overwrite / modify-missing checks.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from jarvis.evolution.engine import (
    EvolutionError,
    FileChange,
    Proposal,
    apply,
    propose,
    validate,
)


def _make_repo(tmp_path: Path, files: dict[str, str]) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "scripts").mkdir()
    for rel, content in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return repo


def test_propose_builds_pure_data():
    p = propose(
        "Add feature",
        "A tiny feature.",
        [FileChange(path="src/x.py", before="", after="x = 1", operation="create")],
    )
    assert p.title == "Add feature"
    assert p.changes[0].path == "src/x.py"
    assert p.approved is False
    assert p.commit_hash is None


def test_validate_runs_gates_on_scratch(monkeypatch, tmp_path):
    repo = _make_repo(tmp_path, {
        "scripts/check_structure.py": "import sys\nsys.exit(0)\n",
        "tests/test_demo.py": "def test_x(): assert True\n",
    })
    proposal = propose(
        "change", "d",
        [FileChange(path="scripts/check_structure.py", before="sys.exit(0)\n",
                    after="import sys\nsys.exit(1)\n", operation="modify")],
    )

    real_subprocess = subprocess.run
    calls = []

    def fake_run(cmd, **kw):
        calls.append((cmd, kw.get("cwd")))
        # Gate scripts: structure exits 1 (proposal makes it fail), pytest OK.
        args = list(cmd)
        if any("check_structure" in a for a in args):
            return subprocess.CompletedProcess(args, 1, stdout="VIOLATION", stderr="")
        if "-m" in args and "pytest" in args:
            return subprocess.CompletedProcess(args, 0, stdout="8 passed", stderr="")
        return real_subprocess(cmd, **kw)

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = validate(proposal, repo=repo)
    assert result["ok"] is False  # structure gate failed
    assert "VIOLATION" in result["structure"]
    # The scratch mirror got the change; the real tree was untouched.
    assert (repo / "scripts/check_structure.py").read_text().endswith("sys.exit(0)\n")


def test_apply_refuses_without_approval(tmp_path):
    repo = _make_repo(tmp_path, {"app.py": "print(1)"})
    proposal = propose("b", "c", [FileChange(path="app.py", before="print(1)", after="print(2)")])
    with pytest.raises(EvolutionError):
        apply(proposal, approved=False, repo=repo)
    assert (repo / "app.py").read_text() == "print(1)"  # untouched


def test_apply_commits_and_records_hash(monkeypatch, tmp_path):
    repo = _make_repo(tmp_path, {"app.py": "print(1)"})
    proposal = propose("b", "c", [FileChange(path="app.py", before="print(1)", after="print(2)")])

    real_run = subprocess.run

    def fake_run(cmd, **kw):
        args = list(cmd)
        # Simulate ALL git calls against the temp repo (not a real git repo).
        if args[0] == "git" and args[1] == "-C" and str(args[2]) == str(repo):
            if "add" in args:
                return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            if "commit" in args:
                return subprocess.CompletedProcess(args, 0, stdout="[main abc1234] b", stderr="")
            if "rev-parse" in args:
                return subprocess.CompletedProcess(args, 0, stdout="abc1234deadbeef", stderr="")
        return real_run(cmd, **kw)

    monkeypatch.setattr(subprocess, "run", fake_run)
    out = apply(proposal, approved=True, repo=repo)
    assert out.approved is True
    assert out.commit_hash == "abc1234deadb"
    assert (repo / "app.py").read_text() == "print(2)"  # applied


def test_apply_twice_refused(monkeypatch, tmp_path):
    repo = _make_repo(tmp_path, {"app.py": "a"})
    proposal = propose("b", "c", [FileChange(path="app.py", before="a", after="b")])

    real_run = subprocess.run

    def fake_run(cmd, **kw):
        args = list(cmd)
        # Simulate ALL git calls against the temp repo (not a real git repo).
        if args[0] == "git" and args[1] == "-C" and str(args[2]) == str(repo):
            if "add" in args:
                return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            if "commit" in args:
                return subprocess.CompletedProcess(args, 0, stdout="[main deadbeef] b", stderr="")
            if "rev-parse" in args:
                return subprocess.CompletedProcess(args, 0, stdout="deadbeef1234", stderr="")
        return real_run(cmd, **kw)

    monkeypatch.setattr(subprocess, "run", fake_run)
    apply(proposal, approved=True, repo=repo)
    with pytest.raises(EvolutionError):
        apply(proposal, approved=True, repo=repo)  # already applied


def test_create_refuses_overwrite(tmp_path):
    repo = _make_repo(tmp_path, {"app.py": "a"})
    proposal = propose("b", "c", [FileChange(path="app.py", before="", after="new", operation="create")])
    with pytest.raises(EvolutionError):
        apply(proposal, approved=True, repo=repo)