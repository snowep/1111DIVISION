"""Quick integration test for the new memory filter (importance + auto-decay)."""
from jarvis.cli import main
from jarvis.docstore.store import DocumentStore
import json

def _run(*argv):
    return main(["--root", str(tmp_json["root"]), *argv])

# Use a temp isolated folder for this check
import tempfile
from pathlib import Path
tmp_dir = Path(tempfile.mkdtemp())
root = tmp_dir / ".jarvis"
root.mkdir(parents=True, exist_ok=True)

# --- Test 1: Low-importance statement should get low importance + 1-day decay ---
assert main(["--root", str(root), "remember",
             "I guess this might work",  # contains heuristic 'guess' -> low weight
             "--kind", "semantic",
             "--actor", "user"]) == 0

store = DocumentStore(root)
semantic_notes = store.list_documents("semantic")
assert len(semantic_notes) == 1
note = store.read(semantic_notes[0])
assert note.metadata["importance"] < 0.4  # heuristic low weight
assert note.metadata.get("valid_until") is not None  # should have decay
print("✓ Low-importance statement got low importance + decay:", note.metadata)

# --- Test 2: High-importance decision should get high importance + no decay ---
assert main(["--root", str(root), "remember",
             "We decided to use PostgreSQL for the primary datastore.",  # 'decided' -> high weight
             "--kind", "decisions",
             "--actor", "user"]) == 0

decisions = store.list_documents("decisions")
assert len(decisions) == 1
note = store.read(decisions[0])
assert note.metadata["importance"] > 0.7  # heuristic high weight
assert note.metadata.get("valid_until") is None  # no decay for high importance
print("✓ High-importance decision got high importance + no decay:", note.metadata)

# --- Test 3: Explicit importance/valid_until overrides heuristic ---
assert main(["--root", str(root), "remember",
             "This is a test override.",
             "--kind", "learned",
             "--importance", "0.95",
             "--valid-until", "2030-01-01T00:00:00+00:00",
             "--actor", "user"]) == 0

learned = store.list_documents("learned")
assert len(learned) == 1
note = store.read(learned[0])
assert note.metadata["importance"] == 0.95
assert note.metadata["valid_until"] == "2030-01-01T00:00:00+00:00"
print("✓ Explicit flags override heuristic:", note.metadata)

# Final status JSON to see ordering by importance
assert main(["--root", str(root), "status", "--json"]) == 0