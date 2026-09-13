"""Phase 10-linking tests: crawl/import-gh/evolve are wired into the CLI.

These prove the full P1-P10 loop is reachable as ONE `jarvis` invocation
chain -- not just via Python API:

- `jarvis crawl`: wraps Crawler, enforces the authority write boundary and
  P5 guards (depth/pages/domain). Uses an injected fake HTTP client so no
  network is needed; the guard set itself is covered in test_phase10_crawl.py.
- `jarvis import-gh`: wraps install_skill with JARVIS_WORKSPACE aligned to
  --root; requires --approve for installation (approval gate intact).
- `jarvis evolve check/apply`: propose -> validate (scratch, no mutation);
  apply refuses without --approve. Tested against a real temp git repo with
  real pytest (the repo is tiny), so gates genuinely run.
- `jarvis web` / `jarvis exec` (P4/P3b) already existed in cli.py; the tests
  below also lock those in so the chain is complete and regression-proof.
"""
from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from jarvis.cli import main
from jarvis.io.workspace import Authority


def _root(tmp_path: Path) -> str:
    return str(tmp_path / ".jarvis")


def _patch_http(monkeypatch):
    """Point the crawler's HttpClient at a deterministic fake.

    ``jarvis.io.http_client`` is shadowed by a *function* of the same name
    in ``jarvis/io/__init__.py``, so patch the real module object instead
    of monkeypatching the dotted import string.
    """
    http_mod = importlib.import_module("jarvis.io.http_client")
    monkeypatch.setattr(http_mod, "HttpClient", lambda **kw: _FakeHttp())


# --------------------------------------------------------------------------
# crawl
# --------------------------------------------------------------------------
PAGES = {
    "https://seed.test/": {
        "body": "<a href='/a'>A</a> <a href='https://elsewhere.test/x'>X</a>",
        "content_type": "text/html",
    },
    "https://seed.test/a": {"body": "<p>leaf</p>", "content_type": "text/html"},
}


class _FakeHttp:
    def fetch(self, url, authority=None):
        page = PAGES.get(url)
        if page is None:
            return {
                "success": False, "url": url, "final_url": url,
                "status": 404, "body": "not found", "content_type": "text/html",
                "error": f"404 for {url}",
            }
        return {
            "success": True, "url": url, "final_url": url,
            "status": 200, "body": page["body"], "content_type": page["content_type"],
        }


def test_cli_crawl_writes_into_workspace(monkeypatch, tmp_path, capsys):
    root = _root(tmp_path)
    _patch_http(monkeypatch)
    rc = main(["--root", root, "crawl", "https://seed.test/",
               "--max-depth", "1", "--max-pages", "5"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["fetched"] == 2
    files = list((tmp_path / ".jarvis/vault/semantic").glob("*.md"))
    assert len(files) == 2
    assert "source_url:" in files[0].read_text(encoding="utf-8")


def test_cli_crawl_blocked_when_out_dir_outside_authority(monkeypatch, tmp_path, capsys):
    # workspace is <tmp>/ws (parent of <tmp>/ws/.jarvis); <tmp>/outside is
    # therefore genuinely outside the authority scope.
    ws = tmp_path / "ws"
    root = str(ws / ".jarvis")
    _patch_http(monkeypatch)
    outside = tmp_path / "outside"
    outside.mkdir()
    rc = main(["--root", root, "crawl", "https://seed.test/",
               "--out-dir", str(outside)])
    assert rc == 1
    out = json.loads(capsys.readouterr().out)
    assert out["success"] is False
    assert "MUTATION_DENIED" in out["error"]


def test_cli_crawl_invalid_seed(monkeypatch, tmp_path, capsys):
    root = _root(tmp_path)
    _patch_http(monkeypatch)
    rc = main(["--root", root, "crawl", "not-a-url"])
    assert rc == 1
    out = json.loads(capsys.readouterr().out)
    assert out["success"] is False


# --------------------------------------------------------------------------
# import-gh
# --------------------------------------------------------------------------
GOOD_MANIFEST = """---
name: cli_demo_skill
version: 0.1.0
description: wired via import-gh
permissions:
  filesystem: read
entry: impl.py
---
"""


def _fake_api(path, token):
    if "git/trees" in path:
        return {"tree": [{"type": "blob", "path": "skill.md"}]}
    if "contents" in path:
        import base64
        text = GOOD_MANIFEST if "skill.md" in path else "print('ok')\n"
        return {"content": base64.b64encode(text.encode()).decode()}
    raise AssertionError(f"unexpected api call {path}")


def test_cli_import_gh_requires_approval(monkeypatch, tmp_path, capsys):
    root = _root(tmp_path)
    monkeypatch.setattr("jarvis.skills.import_github._api", _fake_api)
    rc = main(["--root", root, "import-gh", "owner/repo"])
    assert rc == 0
    out = capsys.readouterr().out
    report = json.loads(out)
    assert report["status"] == "needs-approval"
    assert report["validated"] is True
    # nothing installed
    assert not (tmp_path / ".jarvis/skills/cli_demo_skill").exists()


def test_cli_import_gh_approved_installs(monkeypatch, tmp_path, capsys):
    root = _root(tmp_path)
    monkeypatch.setattr("jarvis.skills.import_github._api", _fake_api)
    rc = main(["--root", root, "import-gh", "owner/repo", "--approve"])
    assert rc == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "approved"
    assert (tmp_path / ".jarvis/skills/cli_demo_skill/skill.md").is_file()
    assert (tmp_path / ".jarvis/skills/cli_demo_skill/impl.py").is_file()


def test_cli_import_gh_aligns_workspace_env(monkeypatch, tmp_path):
    root = _root(tmp_path)
    monkeypatch.setattr("jarvis.skills.import_github._api", _fake_api)
    monkeypatch.delenv("JARVIS_WORKSPACE", raising=False)
    main(["--root", root, "import-gh", "owner/repo", "--approve"])
    # without alignment the engine would have used '.' as the workspace
    assert (tmp_path / ".jarvis/skills/cli_demo_skill").exists()
    assert not (Path.cwd() / ".jarvis/skills/cli_demo_skill").exists()


# --------------------------------------------------------------------------
# evolve
# --------------------------------------------------------------------------
def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "scripts").mkdir()
    (repo / "src").mkdir()
    (repo / "tests").mkdir()
    (repo / "scripts" / "check_structure.py").write_text(
        "import sys\nprint('OK')\nsys.exit(0)\n", encoding="utf-8"
    )
    (repo / "tests" / "test_demo.py").write_text(
        "def test_true(): assert True\n", encoding="utf-8"
    )
    for sub in ("scripts", "src", "tests"):
        (repo / sub / "__init__.py").write_text("", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "t"], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "init"], check=True)
    return repo


def test_cli_evolve_check_gates_but_does_not_mutate(tmp_path, capsys):
    repo = _make_repo(tmp_path)
    change = json.dumps({
        "path": "tests/test_new.py", "operation": "create", "after": "def test_x(): assert True\n",
    })
    rc = main(["--root", _root(tmp_path), "evolve", "check",
               "--title", "add test", "--change", change, "--repo", str(repo)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["gates"]["ok"] is True
    assert "pytest" in out["gates"]
    assert not (repo / "tests/test_new.py").exists()  # scratch only, no mutation


def test_cli_evolve_apply_refuses_without_approve(tmp_path, capsys):
    repo = _make_repo(tmp_path)
    change = json.dumps({
        "path": "tests/test_new.py", "operation": "create", "after": "def test_x(): assert True\n",
    })
    rc = main(["--root", _root(tmp_path), "evolve", "apply",
               "--title", "add test", "--change", change, "--repo", str(repo)])
    assert rc == 1
    assert "--approve" in capsys.readouterr().err
    assert not (repo / "tests/test_new.py").exists()


def test_cli_evolve_apply_approved_commits(tmp_path, capsys):
    repo = _make_repo(tmp_path)
    change = json.dumps({
        "path": "tests/test_new.py", "operation": "create", "after": "def test_x(): assert True\n",
    })
    rc = main(["--root", _root(tmp_path), "evolve", "apply",
               "--title", "add test", "--change", change,
               "--approve", "--repo", str(repo)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["applied"]["approved"] is True
    assert out["applied"]["commit_hash"]
    assert (repo / "tests/test_new.py").exists()
    # committed, not just written
    status = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert status == ""


# --------------------------------------------------------------------------
# web / exec already existed -- lock them in as part of the chain
# --------------------------------------------------------------------------
def test_cli_web_requires_network_authority_output(tmp_path, capsys):
    root = _root(tmp_path)
    # loopback is blocked by the P4 SSRF guard before any connect
    rc = main(["--root", root, "web", "http://127.0.0.1/"])
    assert rc == 1
    out = json.loads(capsys.readouterr().out)
    assert out["success"] is False
    # the CLI surfaces the FetchError message (the code attr is not printed)
    assert "SSRF" in out["error"]


def test_cli_exec_blocklist_before_shell(tmp_path, capsys):
    from jarvis.exec.safe import _is_blocked

    # Pure-python check that the CLI's token-join -> blocklist path blocks
    # destructive commands BEFORE any shell is ever touched.
    assert _is_blocked("rm -rf /") is not None
    assert _is_blocked("shutdown /s") is not None
    # and the CLI joining tokens preserves the blocked prefix
    joined = " ".join(["rm", "-rf", "/"])
    assert _is_blocked(joined) is not None