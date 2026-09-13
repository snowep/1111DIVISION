"""P6 — GitHub skill importer tests (hermetic, no network).

Covers the pipeline: DISCOVER → INSPECT → VALIDATE → ISOLATE → ADAPT →
TEST → INTEGRATE, with the human approval gate. All network calls are
monkeypatched so the tests are deterministic; the security posture
(never execute remote code, never auto-grant permissions, never
overwrite existing skills) is what's exercised.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from jarvis.skills.import_github import (
    ImportError_,
    ImportReport,
    _adapt_entry,
    _parse_manifest_text,
    _validate_manifest,
    discover_manifest,
    install_skill,
    inspect_and_validate,
)

GOOD_MANIFEST = """---
name: example_skill
version: 0.1.0
description: A test skill.
trigger: when asked to do the thing
params: "input (str): the thing"
permissions:
  filesystem: read
  network: no
entry: impl.py
source: github:example/example
status: active
---
body text
"""

BAD_MANIFEST = """---
name: bad
version: 0.1.0
entry: impl.py
permissions:
  filesystem: write
---
"""


def test_parse_manifest_frontmatter():
    meta = _parse_manifest_text(GOOD_MANIFEST)
    assert meta["name"] == "example_skill"
    assert meta["permissions"] == {"filesystem": "read", "network": "no"}


def test_validate_good_manifest():
    ok, warnings = _validate_manifest(_parse_manifest_text(GOOD_MANIFEST))
    assert ok is True
    assert warnings == []


def test_validate_bad_manifest_reports_missing():
    ok, warnings = _validate_manifest(_parse_manifest_text(BAD_MANIFEST))
    assert ok is False
    assert any("description" in w for w in warnings)


def test_discover_manifest_finds_skill_md(monkeypatch):
    def fake_api(path, token):
        if "git/trees" in path:
            return {
                "tree": [
                    {"type": "blob", "path": "skills/demo/skill.md"},
                    {"type": "blob", "path": "skills/demo/impl.py"},
                ]
            }
        raise AssertionError(f"unexpected api call {path}")
    monkeypatch.setattr("jarvis.skills.import_github._api", fake_api)
    path, item = discover_manifest("owner/repo")
    assert path == "skills/demo/skill.md"


def test_discover_no_manifest(monkeypatch):
    monkeypatch.setattr(
        "jarvis.skills.import_github._api",
        lambda path, token: {"tree": [{"type": "blob", "path": "README.md"}]},
    )
    path, _ = discover_manifest("owner/repo")
    assert path is None


def test_inspect_rejects_bad_manifest(monkeypatch):
    def fake_api(path, token):
        if "git/trees" in path:
            return {"tree": [{"type": "blob", "path": "skill.md"}]}
        if "contents" in path:
            import base64
            return {"content": base64.b64encode(BAD_MANIFEST.encode()).decode()}
        raise AssertionError(f"unexpected api call {path}")

    monkeypatch.setattr("jarvis.skills.import_github._api", fake_api)
    report, data = inspect_and_validate("owner/repo")
    assert report.status == "rejected"
    assert report.validated is False


def test_adapt_entry_rewrites_repo_token():
    adapted = _adapt_entry("BLAH $REPO", "owner/repo")
    assert adapted == "BLAH owner/repo"


def test_install_requires_approval(monkeypatch, tmp_path):
    def fake_api(path, token):
        if "git/trees" in path:
            return {"tree": [{"type": "blob", "path": "skill.md"}]}
        if "skill.md" in path and "contents" in path:
            import base64
            return {"content": base64.b64encode(GOOD_MANIFEST.encode()).decode()}
        raise AssertionError(f"unexpected api call {path}")

    monkeypatch.setattr("jarvis.skills.import_github._api", fake_api)
    monkeypatch.setenv("JARVIS_WORKSPACE", str(tmp_path))
    report = install_skill("owner/repo", approve=False)
    assert report.status == "needs-approval"
    assert (tmp_path / ".jarvis/skills").exists() is False  # nothing installed


def test_install_approved_isolates_skill(monkeypatch, tmp_path):
    def fake_api(path, token):
        if "git/trees" in path:
            return {"tree": [{"type": "blob", "path": "skill.md"}]}
        if "contents" in path:
            import base64
            local_text = GOOD_MANIFEST if "skill.md" in path else "print('x')"
            return {"content": base64.b64encode(local_text.encode()).decode()}
        raise AssertionError(f"unexpected api call {path}")

    monkeypatch.setattr("jarvis.skills.import_github._api", fake_api)
    monkeypatch.setenv("JARVIS_WORKSPACE", str(tmp_path))
    report = install_skill("owner/repo", approve=True)
    assert report.status == "approved"
    assert (tmp_path / ".jarvis/skills/example_skill/skill.md").is_file()
    assert (tmp_path / ".jarvis/skills/example_skill/impl.py").is_file()
    assert report.installed_to.replace("\\", "/") == ".jarvis/skills/example_skill"


def test_install_refuses_overwrite(monkeypatch, tmp_path):
    def fake_api(path, token):
        if "git/trees" in path:
            return {"tree": [{"type": "blob", "path": "skill.md"}]}
        if "contents" in path:
            import base64
            local_text = GOOD_MANIFEST if "skill.md" in path else "print('x')"
            return {"content": base64.b64encode(local_text.encode()).decode()}
        raise AssertionError(f"unexpected api call {path}")

    monkeypatch.setattr("jarvis.skills.import_github._api", fake_api)
    monkeypatch.setenv("JARVIS_WORKSPACE", str(tmp_path))
    (tmp_path / ".jarvis/skills/example_skill").mkdir(parents=True)
    (tmp_path / ".jarvis/skills/example_skill/skill.md").write_text("existing")
    report = install_skill("owner/repo", approve=True)
    assert report.status == "rejected"
    assert "refusing to overwrite" in report.warnings[0]