"""Tests for the P2 skill manager: manifests, permissions, derived registry."""
import pytest

from jarvis.docstore.models import DocError
from jarvis.skills import (
    PERMISSION_MEANING,
    SkillError,
    allowed_permissions,
    check_permission,
    load_skill,
    load_skills,
    parse_manifest,
    rebuild_registry,
)

VALID_MANIFEST = """---
name: echo
version: 0.1.0
description: Echo back the input text.
trigger: echo
params: [text]
permissions:
  filesystem: read
  network: no
entry: impl.py
source: local
status: active
---

Echo implementation.
"""


def test_parse_valid_manifest():
    m = parse_manifest(VALID_MANIFEST)
    assert m.name == "echo"
    assert m.version == "0.1.0"
    assert m.params == ["text"]
    assert m.permissions == {"filesystem": "read", "network": "no"}
    assert m.entry == "impl.py"
    assert m.status == "active"


def test_parse_missing_name_rejected():
    with pytest.raises(SkillError):
        parse_manifest("---\nversion: 0.1.0\n---\n")


def test_parse_invalid_permission_key_rejected():
    with pytest.raises(SkillError):
        parse_manifest(
            "---\nname: x\npermissions:\n  quantum: read\n---\n"
        )


def test_parse_invalid_permission_value_rejected():
    with pytest.raises(SkillError):
        parse_manifest(
            "---\nname: x\npermissions:\n  filesystem: yes_please\n---\n"
        )


def test_permission_shorthand_list():
    m = parse_manifest(
        "---\nname: x\npermissions: [filesystem.read, network.read]\n---\n"
    )
    assert m.permissions["filesystem"] == "read"
    assert m.permissions["network"] == "read"


def test_check_permission_grants_and_denies():
    m = parse_manifest(
        "---\nname: x\npermissions:\n  filesystem: read\n  network: no\n---\n"
    )
    check_permission(m, "filesystem.read")  # no raise
    with pytest.raises(SkillError):
        check_permission(m, "terminal.execute")
    with pytest.raises(SkillError):
        check_permission(m, "network.read")  # explicitly 'no'


def test_allowed_permissions_set():
    m = parse_manifest(
        "---\nname: x\npermissions:\n  filesystem: read\n  terminal: no\n---\n"
    )
    assert allowed_permissions(m) == {"filesystem.read"}


def _write_skill(root, name, manifest_text, impl_text="# impl\n") -> None:
    d = root / "skills" / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "skill.md").write_text(manifest_text, encoding="utf-8")
    (d / "impl.py").write_text(impl_text, encoding="utf-8")


def test_load_skills(tmp_path):
    _write_skill(tmp_path, "echo", VALID_MANIFEST)
    _write_skill(
        tmp_path,
        "stats",
        "---\nname: stats\nversion: 0.2.0\ndescription: Compute stats.\npermissions:\n  filesystem: read\nentry: impl.py\n---\n",
    )
    skills = load_skills(tmp_path)
    names = {s.name for s in skills}
    assert names == {"echo", "stats"}
    assert all(s.status == "active" for s in skills)


def test_load_skills_skips_invalid_manifest(tmp_path):
    _write_skill(tmp_path, "bad", "not frontmatter at all\n")
    skills = load_skills(tmp_path)
    assert len(skills) == 1
    assert skills[0].name == "bad"
    assert skills[0].status == "invalid"


def test_entry_missing_is_invalid(tmp_path):
    d = tmp_path / "skills" / "ghost"
    d.mkdir(parents=True, exist_ok=True)
    (d / "skill.md").write_text(
        "---\nname: ghost\nentry: missing.py\npermissions: {}\n---\n",
        encoding="utf-8",
    )
    skills = load_skills(tmp_path)
    assert skills[0].status == "invalid"


def test_registry_rebuild_is_deterministic(tmp_path):
    _write_skill(tmp_path, "echo", VALID_MANIFEST)
    _write_skill(
        tmp_path,
        "stats",
        "---\nname: stats\nversion: 0.1.0\ndescription: Stats.\npermissions:\n  filesystem: read\nentry: impl.py\n---\n",
    )
    first = rebuild_registry(tmp_path)
    second = rebuild_registry(tmp_path)
    assert first == second  # deterministic

    reg_md = (tmp_path / "skills" / "registry.md").read_text(encoding="utf-8")
    assert "DERIVED" in reg_md
    assert "| echo |" in reg_md
    assert "| stats |" in reg_md

    reg_json = (tmp_path / "skills" / "registry.json").read_text(encoding="utf-8")
    assert '"name": "echo"' in reg_json


def test_registry_reflects_new_skill(tmp_path):
    _write_skill(tmp_path, "echo", VALID_MANIFEST)
    first = rebuild_registry(tmp_path)
    assert len(first["skills"]) == 1
    _write_skill(
        tmp_path,
        "git-status",
        "---\nname: git-status\nversion: 0.1.0\ndescription: Show git status.\npermissions:\n  terminal: execute\nentry: impl.py\n---\n",
    )
    second = rebuild_registry(tmp_path)
    assert {s["name"] for s in second["skills"]} == {"echo", "git-status"}