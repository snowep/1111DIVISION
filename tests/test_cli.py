"""CLI integration tests: remember/status/forget/verify/skill wiring end-to-end."""
from jarvis.cli import main
from jarvis.docstore.store import DocumentStore
from jarvis.memory import list_active
from jarvis.skills import load_skills


def _root(tmp_path):
    return str(tmp_path / ".jarvis")


def test_cli_remember_status_roundtrip(tmp_path, capsys):
    root = _root(tmp_path)
    assert main(["--root", root, "remember",
                 "Project uses PostgreSQL for primary datastore",
                 "--kind", "semantic", "--tags", "project,database",
                 "--confidence", "0.9", "--actor", "user"]) == 0
    assert main(["--root", root, "remember",
                 "We decided to use SQLite for the workspace module",
                 "--kind", "decisions", "--actor", "user"]) == 0
    assert main(["--root", root, "remember",
                 "Yesterday we deployed the workspace sandbox",
                 "--kind", "episodic", "--actor", "user"]) == 0

    assert main(["--root", root, "status"]) == 0
    out = capsys.readouterr().out
    # status lists all notes (active + proposals) with their titles
    assert "PostgreSQL" in out
    assert "SQLite" in out
    assert "workspace sandbox" in out

    store = DocumentStore(root)
    semantic = store.list_documents("semantic")[0]
    assert main(["--root", root, "verify", semantic, "--reason", "confirmed"]) == 0
    active = list_active(store)
    assert any(n.kind == "semantic" and n.phase == "VERIFIED" for n in active)


def test_cli_status_json(tmp_path):
    root = _root(tmp_path)
    main(["--root", root, "remember", "json check", "--kind", "semantic"])
    assert main(["--root", root, "learn"]) == 0
    assert main(["--root", root, "status", "--json"]) == 0


def test_cli_forget_expired(tmp_path):
    root = _root(tmp_path)
    main(["--root", root, "remember", "old fact", "--kind", "semantic",
          "--valid-until", "2000-01-01T00:00:00+00:00"])
    assert main(["--root", root, "forget", "--dry-run"]) == 0
    assert main(["--root", root, "forget"]) == 0


def test_cli_skill_scan_list(tmp_path):
    root = _root(tmp_path)
    sk = tmp_path / ".jarvis" / "skills" / "echo"
    sk.mkdir(parents=True, exist_ok=True)
    (sk / "skill.md").write_text(
        "---\nname: echo\nversion: 0.1.0\ndescription: Echo input.\n"
        "permissions:\n  filesystem: read\nentry: impl.py\n---\n",
        encoding="utf-8",
    )
    (sk / "impl.py").write_text("# impl\n", encoding="utf-8")
    assert main(["--root", root, "skill", "scan"]) == 0
    assert main(["--root", root, "skill", "list"]) == 0
    skills = load_skills(tmp_path / ".jarvis")
    assert any(s.name == "echo" and s.permissions.get("filesystem") == "read" for s in skills)
    reg = (tmp_path / ".jarvis" / "skills" / "registry.md").read_text(encoding="utf-8")
    assert "echo" in reg