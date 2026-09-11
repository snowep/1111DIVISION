"""Command-line interface: jarvis new|list|read|edit|delete|learn|seed."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jarvis.docstore.store import DocumentStore, StoreError
from jarvis.learn.engine import learn

DEFAULT_ROOT = Path(".jarvis")


def _store(args: argparse.Namespace) -> DocumentStore:
    return DocumentStore(args.root)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="jarvis", description="JARVIS minimal data manager")
    p.add_argument("--root", type=Path, default=DEFAULT_ROOT,
                   help="isolated data folder (default: .jarvis)")
    sub = p.add_subparsers(dest="command", required=True)

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
    return p


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
        return 0
    except StoreError as exc:
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