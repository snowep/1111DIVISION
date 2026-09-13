"""Command-line interface: jarvis new|list|read|edit|delete|learn|seed|remember|status|forget|verify|supersede|skill."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jarvis.docstore.store import DocumentStore, StoreError
from jarvis.learn.engine import learn
from jarvis.memory import (
    MemoryError,
    ROUTING,
    ROUTING_DESCRIPTIONS,
    forget_expired,
    list_active,
    remember,
    route,
    supersede,
    verify,
)
from jarvis.skills import SkillError, load_skills, rebuild_registry

DEFAULT_ROOT = Path(".jarvis")


def _store(args: argparse.Namespace) -> DocumentStore:
    return DocumentStore(args.root)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="jarvis", description="JARVIS memory + skill manager")
    p.add_argument("--root", type=Path, default=DEFAULT_ROOT,
                   help="isolated data folder (default: .jarvis)")
    sub = p.add_subparsers(dest="command", required=True)

    # ---- documents (base docstore) ----
    sp = sub.add_parser("new", help="create a document")
    sp.add_argument("kind", help="document kind, e.g. note|proj|person")
    sp.add_argument("title", help="document title")
    sp.add_argument("--body", default="", help="markdown body")
    sp.add_argument("--tag", action="append", default=[], help="tag (repeatable)")
    sp.add_argument("--id", default=None, help="explicit document id")

    sp = sub.add_parser("list", help="list documents")
    sp.add_argument("--kind", default=None, help="filter by kind")
    sp.add_argument("--json", action="store_true", help="output JSON")

    sp = sub.add_parser("read", help="read a document")
    sp.add_argument("path", help="relative path, e.g. note/abc.md")

    sp = sub.add_parser("edit", help="update body/metadata/title")
    sp.add_argument("path", help="relative path")
    sp.add_argument("--title", default=None, help="new title")
    sp.add_argument("--body", default=None, help="new body (overwrites)")

    sp = sub.add_parser("delete", help="delete a document")
    sp.add_argument("path", help="relative path")
    sp.add_argument("--yes", action="store_true", help="skip confirmation")

    sub.add_parser("learn", help="rebuild derived knowledge from documents")

    sp = sub.add_parser("seed", help="create placeholder example documents")
    sp.add_argument("--reset", action="store_true", help="replace all notes with placeholders")

    # ---- memory (P1) ----
    sp = sub.add_parser("remember", help="store a memory note in the vault")
    sp.add_argument("text", help="memory text")
    sp.add_argument("--kind", default="episodic", choices=sorted(ROUTING),
                    help="memory type (routing)")
    sp.add_argument("--tags", default="", help="comma-separated tags")
    sp.add_argument("--confidence", type=float, default=None, help="0..1 epistemic confidence")
    sp.add_argument("--importance", type=float, default=None, help="0..1 importance weight (auto-assessed if omitted)")
    sp.add_argument("--valid-until", default=None, help="ISO datetime; auto-archived after (auto-calculated if omitted)")
    sp.add_argument("--phase", default="OBSERVED", help="lifecycle phase")
    sp.add_argument("--actor", default="user", help="who/what originated this")

    sp = sub.add_parser("status", help="show live memory + skill state")
    sp.add_argument("--json", action="store_true", help="output JSON")

    sp = sub.add_parser("forget", help="archive expired memory (SUPERSEDED, not deleted)")
    sp.add_argument("--dry-run", action="store_true", help="list without touching")

    sp = sub.add_parser("verify", help="promote an OBSERVED/CANDIDATE note to VERIFIED")
    sp.add_argument("path", help="note relative path")
    sp.add_argument("--reason", default="verified", help="reason recorded in provenance")

    sp = sub.add_parser("supersede", help="mark a note SUPERSEDED")
    sp.add_argument("path", help="note relative path")
    sp.add_argument("--reason", default="superseded", help="reason recorded in provenance")

    # ---- skills (P2) ----
    sp = sub.add_parser("skill", help="skill manager: registry, list, scan, run")
    skill_subsub = sp.add_subparsers(dest="skill_command", help="skill sub-command")
    skill_subsub.add_parser("scan", help="rebuild the skills registry from disk")
    skill_subsub.add_parser("list", help="list known skills with status and permissions")
    skill_run = skill_subsub.add_parser("run", help="run a skill by name")
    skill_run.add_argument("name", help="name of the skill to run")
    skill_run.add_argument(
        "param",
        nargs="*",
        help="parameters in the form key=value",
    )

    # ---- execution (P3b) ----
    exec_sub = sub.add_parser("exec", help="safe shell execution (blocklist-first, workspace-pinned)")
    exec_sub.add_argument("command", nargs="+", help="shell command to run (tokens joined with spaces)")
    exec_sub.add_argument("--timeout", type=int, default=30, help="timeout in seconds")
    exec_sub.add_argument("--cwd", default=None, help="working directory (must be inside the workspace)")

    # ---- web reader (P4) ----
    web_sub = sub.add_parser("web", help="bounded web reader (http/https only, SSRF + size guards)")
    web_sub.add_argument("url", help="absolute http(s) URL to fetch")
    web_sub.add_argument("--max-bytes", type=int, default=512 * 1024, help="response size cap")

    return p


def _cmd_remember(args) -> int:
    store = _store(args)
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    # Apply assess/decay if not explicitly provided
    importance = args.importance
    valid_until = args.valid_until
    if importance is None:
        from jarvis.memory.assess import assess_importance
        importance = assess_importance(args.text, args.kind)
    if valid_until is None:
        from jarvis.memory.assess import calculate_decay
        valid_until = calculate_decay(importance)

    note = remember(
        store,
        args.text,
        kind=args.kind,
        confidence=args.confidence,
        importance=importance,
        valid_until=valid_until,
        phase=args.phase,
        actor=args.actor,
        provenance={"type": "user", "source": "cli"},
        tags=tags or None,
    )
    print(note.document.path)
    return 0


def _cmd_status(args) -> int:
    store = _store(args)
    if args.json:
        from jarvis.memory.engine import parse_memory_note
        notes = []
        for rel in store.list_documents():
            try:
                n = parse_memory_note(store.read(rel))
            except (StoreError, MemoryError):
                continue
            notes.append({
                "path": rel,
                "kind": n.kind,
                "phase": n.phase,
                "confidence": n.confidence,
                "title": n.document.metadata.get("title", ""),
            })
        try:
            skills = [s.name for s in load_skills(store.root) if s.status == "active"]
        except SkillError:
            skills = []
        print(json.dumps({"vault_notes": notes, "skills": skills}, indent=2))
        return 0
    from jarvis.memory.engine import parse_memory_note
    notes = []
    for rel in store.list_documents():
        try:
            notes.append(parse_memory_note(store.read(rel)))
        except (StoreError, MemoryError):
            continue
    notes.sort(key=lambda n: (n.phase, n.document.path))
    active = [n for n in notes if n.phase in ("ACTIVE", "VERIFIED")]
    proposals = [n for n in notes if n.phase not in ("ACTIVE", "VERIFIED")]
    print("# JARVIS status")
    print(f"root: {store.root}")
    print(f"vault notes: {len(notes)} ({len(active)} active, {len(proposals)} proposals)")
    print("\n## Active\n")
    if active:
        for n in active:
            print(f"  - [{n.kind}/{n.phase}] {n.document.metadata.get('title', n.document.path)}")
    else:
        print("  (none)")
    print("\n## Proposals (OBSERVED/CANDIDATE)\n")
    if proposals:
        for n in proposals:
            print(f"  - [{n.kind}/{n.phase}] {n.document.metadata.get('title', n.document.path)}")
    else:
        print("  (none)")
    skills = [s for s in load_skills(store.root) if s.status == "active"]
    print(f"\nactive skills: {len(skills)}")
    for s in skills:
        print(f"  - {s.name} v{s.version}")
    print("\n## Routing")
    for kind, subdir in sorted(ROUTING.items()):
        print(f"  {kind} -> vault/{subdir}  ({ROUTING_DESCRIPTIONS.get(kind, '')})")
    return 0


def _cmd_exec(args) -> int:
    from jarvis.exec import safe_exec
    from jarvis.io.workspace import Authority

    root = Path(args.root) if args.root else DEFAULT_ROOT
    ws = root.parent.resolve() if str(root).startswith(".jarvis") else root.resolve()
    auth = Authority(
        kind="identity", name="JARVIS", scope=str(ws),
        permissions={"terminal": "execute"},
    )
    cwd = Path(args.cwd) if args.cwd else None
    command = " ".join(args.command)
    result = safe_exec(
        command,
        cwd=cwd,
        timeout=args.timeout,
        workspace_root=ws,
        authority=auth,
    )
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.success else 1


def _cmd_web(args) -> int:
    from jarvis.io.http_client import FetchError, HttpClient
    from jarvis.io.workspace import Authority

    root = Path(args.root) if args.root else DEFAULT_ROOT
    ws = root.parent.resolve() if str(root).startswith(".jarvis") else root.resolve()
    auth = Authority(
        kind="identity", name="JARVIS", scope=str(ws),
        permissions={"network": "read"},
    )
    client = HttpClient(max_bytes=args.max_bytes)
    try:
        result = client.fetch(args.url, authority=auth)
    except (FetchError, PermissionError) as exc:
        print(json.dumps({"success": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(result.to_dict(), indent=2))
    return 0


def _cmd_skill(args) -> int:
    root = Path(args.root) if args.root else DEFAULT_ROOT
    if args.skill_command == "scan":
        from jarvis.skills import rebuild_registry
        rebuild_registry(root)
        print("Registry rebuilt")
        return 0
    if args.skill_command == "list":
        from jarvis.skills import load_skills
        for skill in load_skills(root):
            print(f"{skill.name}: {skill.status} | {skill.permissions}")
        return 0
    if args.skill_command == "run":
        # Build parameters dict from key=value strings
        params = {}
        for p in args.param:
            if '=' not in p:
                print(f"error: parameter '{p}' must be in the form key=value")
                return 1
            k, v = p.split('=', 1)
            params[k] = v

        # Load the skill module
        skill_path = root / "skills" / args.name / "impl.py"
        if not skill_path.exists():
            print(f"error: skill '{args.name}' not found at {skill_path}")
            return 1

        import importlib.util
        import sys
        spec = importlib.util.spec_from_file_location(f"skill_{args.name}", skill_path)
        if spec is None:
            print(f"error: could not load skill '{args.name}'")
            return 1
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"error: failed to execute skill module: {e}")
            return 1

        if not hasattr(module, 'run'):
            print(f"error: skill '{args.name}' missing run function")
            return 1

        # Run the skill
        try:
            result = module.run(params, session_id=None)
            # Print result as JSON for clarity
            import json
            print(json.dumps(result, indent=2))
            return 0 if result.get("success", False) else 1
        except Exception as e:
            print(f"error: skill execution failed: {e}")
            return 1

    print("error: missing skill sub-command")
    return 1


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    store = _store(args)
    try:
        if args.command == "new":
            doc = store.create(args.kind, args.title, body=args.body,
                               metadata={"tags": args.tag} if args.tag else None,
                               doc_id=args.id)
            print(doc.path)
        elif args.command == "list":
            paths = store.list_documents(args.kind)
            if args.json:
                print(json.dumps({"documents": paths}, indent=2))
            else:
                for p in paths:
                    print(p)
        elif args.command == "read":
            doc = store.read(args.path)
            print(f"# {doc.metadata.get('title', args.path)}")
            print(f"path: {doc.path}")
            for key, value in doc.metadata.items():
                if key == "title":
                    continue
                print(f"{key}: {value}")
            print("---")
            print(doc.body)
        elif args.command == "edit":
            doc = store.update(args.path, body=args.body, title=args.title)
            print(f"updated {doc.path}")
        elif args.command == "delete":
            if not args.yes and not input(f"delete {args.path}? [y/N] ").strip().lower() == "y":
                print("aborted")
                return 1
            store.delete(args.path)
            print(f"deleted {args.path}")
        elif args.command == "learn":
            index = learn(store)
            print(f"learned from {index['document_count']} documents -> "
                  f"{store.learn_dir}")
        elif args.command == "seed":
            count = seed(store, reset=args.reset)
            print(f"seeded {count} placeholder documents")
        elif args.command == "remember":
            return _cmd_remember(args)
        elif args.command == "status":
            return _cmd_status(args)
        elif args.command == "forget":
            archived = forget_expired(store, dry_run=args.dry_run)
            if args.dry_run:
                print(f"{len(archived)} would be archived (dry-run)")
            else:
                print(f"archived {len(archived)} expired memory note(s)")
            for rel in archived:
                print(f"  - {rel}")
        elif args.command == "verify":
            note = verify(store, args.path, reason=args.reason)
            print(f"{args.path}: {note.phase}")
        elif args.command == "supersede":
            note = supersede(store, args.path, reason=args.reason)
            print(f"{args.path}: {note.phase}")
        elif args.command == "skill":
            return _cmd_skill(args)
        elif args.command == "exec":
            return _cmd_exec(args)
        elif args.command == "web":
            return _cmd_web(args)
        return 0
    except (StoreError, MemoryError, SkillError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def seed(store: DocumentStore, reset: bool = False) -> int:
    """Create placeholder documents. With reset=True, clear existing notes first."""
    if reset:
        for rel in store.list_documents():
            store.delete(rel)
    samples = [
        ("proj", "Sample Project", "## Lessons\n- Scaffold first, polish later.\n- Keep derived data rebuildable from source.",
         ["project", "placeholder"]),
        ("note", "Meeting Notes", "## Lessons\n- Decisions should be written down.\n- Absence of disagreement is not agreement.",
         ["meeting", "placeholder"]),
        ("note", "Research Idea", "Who watches the watchmen? Investigate provenance.",
         ["research", "placeholder"]),
    ]
    added = 0
    for kind, title, body, tags in samples:
        existing = [r for r in store.list_documents(kind) if title in r]
        if existing:
            continue
        store.create(kind, title, body, metadata={"tags": tags})
        added += 1
    return added


if __name__ == "__main__":
    raise SystemExit(main())