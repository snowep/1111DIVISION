"""Command-line interface: jarvis new|list|read|edit|delete|learn|seed|remember|status|forget|skill."""
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
    sp = sub.add_parser("skill", help="skill manager: registry, list, scan")
    sp.add_argument("action", choices=["list", "scan", "rebuild"], default="list", nargs="?",
                    help="list = show registry (or rebuild if missing)")

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
    print(f"\n## Active\n")
    if active:
        for n in active:
            print(f"  - [{n.kind}/{n.phase}] {n.document.metadata.get('title', n.document.path)}")
    else:
        print("  (none)")
    print(f"\n## Proposals (OBSERVED/CANDIDATE)\n")
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


def _cmd_skill(args) -> int:
    store = _store(args)
    if args.action == "scan" or args.action == "rebuild":
        # Rebuild derived registry from skills/ (deterministic).
        data = rebuild_registry(store.root)
        print(f"registry rebuilt: {len(data['skills'])} skill(s) "
              f"({data['scanned_at']}) -> {store.root / 'skills' / 'registry.md'}")
        return 0
    # list: rebuild if missing, then show
    reg_md = store.root / "skills" / "registry.md"
    if not reg_md.is_file():
        rebuild_registry(store.root)
    skills = load_skills(store.root)
    if not skills:
        print("(no skills registered — create skills/<name>/skill.md then run 'jarvis skill scan')")
        return 0
    for s in skills:
        perms = ",".join(f"{k}={v}" for k, v in sorted(s.permissions.items())) or "none"
        print(f"  {s.name} v{s.version} [{s.status}] perms={{{perms}}} — {s.description}")
    return 0


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