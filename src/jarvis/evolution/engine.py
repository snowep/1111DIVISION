"""P9 — Self-evolution: propose → validate → apply → revert (git-driven).

No silent edits. The pipeline is:

1. `propose(title, description, changes)` — build a `Proposal` describing
   file changes (create/modify/delete) with the full before/after content.
2. `validate(proposal)` — run the repo gates WITHOUT touching the working
   tree: `python -m pytest` and the structure check, using a scratch copy
   of the affected files (the proposal is applied to a temp mirror).
   NEVER validates against the live tree (that would be a silent edit).
3. `apply(proposal, approved=True)` — apply the diff to the real tree,
   stage, commit, push. Refuses to run without `approved=True`.
4. `revert(commit_hash)` — `git revert` (rollback is reversible history).

A proposal is a pure data object; applying it is the only mutation.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


class EvolutionError(Exception):
    """Raised when an evolution step violates the rules."""


@dataclass
class FileChange:
    """One file edit in a proposal."""

    path: str          # repo-relative path
    before: str = ""   # previous content ("" = new file)
    after: str = ""    # new content ("" = delete file)
    operation: str = "modify"  # create | modify | delete


@dataclass
class Proposal:
    """A proposal to change the repository (pure data)."""

    title: str
    description: str = ""
    changes: list[FileChange] = field(default_factory=list)
    commit_hash: Optional[str] = None
    approved: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "changes": [c.__dict__ for c in self.changes],
            "commit_hash": self.commit_hash,
            "approved": self.approved,
        }


def _git(repo: Path, *args: str) -> str:
    """Run a git command against the repo; returns stdout (stderr included)."""
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, timeout=60,
    )
    if proc.returncode != 0:
        raise EvolutionError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return (proc.stdout or "").strip()


def _repo_root() -> Path:
    """Locate the repo root from the current working directory (git-aware)."""
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, timeout=30,
    )
    if proc.returncode != 0:
        raise EvolutionError("not inside a git repository")
    return Path(proc.stdout.strip())


def propose(title: str, description: str, changes: list[FileChange]) -> Proposal:
    return Proposal(title=title, description=description, changes=changes)


def _apply_to_tree(repo: Path, proposal: Proposal) -> None:
    """Apply the proposal's changes to the working tree (mutation!)."""
    for change in proposal.changes:
        target = repo / change.path
        if change.operation == "delete":
            if target.exists():
                target.unlink()
            continue
        if change.operation == "create":
            if target.exists():
                raise EvolutionError(f"refusing to overwrite existing file: {change.path}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(change.after, encoding="utf-8")
        else:  # modify
            if not target.exists():
                raise EvolutionError(f"cannot modify missing file: {change.path}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(change.after, encoding="utf-8")


def validate(proposal: Proposal, repo: Optional[Path] = None) -> dict[str, Any]:
    """Run pytest + structure gate against a SCRATCH copy of the repo with the
    proposal applied. Returns {'ok': bool, 'pytest': ..., 'structure': ...}.
    Never mutates the real working tree.
    """
    repo = repo or _repo_root()
    if not proposal.changes:
        raise EvolutionError("empty proposal (no changes)")
    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp) / "repo"
        # Copy tracked repo into scratch (skip .git heavy copy: copy .git too
        # so git commands work in the mirror).
        shutil.copytree(repo, scratch, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
        # Re-create a minimal .git (for git status in validation), or simply
        # run pytest + structure (no git needed for those gates).
        for change in proposal.changes:
            target = scratch / change.path
            if change.operation == "delete":
                if target.exists():
                    target.unlink()
                continue
            if change.operation == "create" and target.exists():
                return {"ok": False, "pytest": "", "structure": f"would overwrite {change.path}"}
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(change.after, encoding="utf-8")

        # Run structure check first (cheap), then pytest.
        structure_out = ""
        try:
            proc = subprocess.run(
                ["python", "scripts/check_structure.py"],
                cwd=scratch, capture_output=True, text=True, timeout=120,
            )
            structure_out = (proc.stdout or "") + (proc.stderr or "")
            structure_ok = proc.returncode == 0
        except Exception as exc:
            structure_ok, structure_out = False, str(exc)

        pytest_out = ""
        pytest_ok = False
        try:
            proc = subprocess.run(
                ["python", "-m", "pytest", "-q"],
                cwd=scratch, capture_output=True, text=True, timeout=600,
            )
            stdout = (proc.stdout or "").strip()
            pytest_out = stdout.splitlines()[-1] if stdout else ""
            stderr = (proc.stderr or "").strip()
            if stderr:
                pytest_out = f"{pytest_out}\n{stderr}"
            pytest_ok = proc.returncode == 0
        except Exception as exc:
            pytest_out = str(exc)

        ok = structure_ok and pytest_ok
        return {
            "ok": ok,
            "pytest": pytest_out,
            "structure": structure_out.splitlines()[-1] if structure_out.strip() else "",
        }


def apply(proposal: Proposal, *, approved: bool, repo: Optional[Path] = None) -> Proposal:
    """Apply a proposal to the real tree, commit, push. Requires approval."""
    repo = repo or _repo_root()
    if not approved:
        raise EvolutionError("proposal not approved; refusing to change the tree")
    if proposal.approved:
        raise EvolutionError("proposal already applied")
    _apply_to_tree(repo, proposal)
    # Stage + commit.
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", proposal.title, "-m", proposal.description)
    head = _git(repo, "rev-parse", "HEAD")
    proposal.commit_hash = head[:12]
    proposal.approved = True
    return proposal


def revert(commit_hash: str, repo: Optional[Path] = None) -> str:
    """Rollback by `git revert` (reversible history, never a force-push)."""
    repo = repo or _repo_root()
    _git(repo, "revert", "--no-edit", commit_hash)
    return _git(repo, "rev-parse", "HEAD")[:12]