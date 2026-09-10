import os, subprocess, glob

base = r"D:\Project\1111DIVISION"
os.chdir(base)

# Remove this script + any remaining tmp
for f in glob.glob(os.path.join(base, ".tmp_*")):
    if os.path.basename(f) != ".tmp_commit2.py":
        os.remove(f)
        print("REMOVED:", os.path.basename(f))

# Remove itself at end
import atexit
atexit.register(lambda: os.path.exists(os.path.join(base, ".tmp_commit2.py")) and os.remove(os.path.join(base, ".tmp_commit2.py")))

r = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
print("=" * 60)
print("STATUS BEFORE COMMIT:")
print(r.stdout)

r = subprocess.run(["git", "add", "-A"], capture_output=True, text=True)
print("\nADD:", "ok" if r.returncode == 0 else r.stderr)

r = subprocess.run(["git", "commit", "-m", "Rebuild vault & council from founding sources\n\nExtract chat-Council of Creators.txt (215 sessions) + historical chat.json (founding constitution) into:\n- vault/01 - Projects/11-11 Division: Brand Bible, Project Home, Product System, Drop System, Visual Identity, Content Strategy, Lore, Open Questions\n- vault/02 - Knowledge: brand lore & worldbuilding\n- vault/04 - Decisions: DEC-001..007 (real decisions from chats, removed invented placeholders)\n- vault/05 Personas/Council: Supreme Council structure (4 permanent + 7 temporary seats)\n- .jarvis/council/decisions.md: rebuilt to real decision list"], capture_output=True, text=True)
print("\nCOMMIT:", r.returncode)
print(r.stdout[:2000])
print(r.stderr[:1000])

if r.returncode == 0:
    r = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
    print("\nPUSH:", r.returncode)
    print((r.stdout or "")[-600:])
    print((r.stderr or "")[-600:])

r = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
print("\nFINAL STATUS:", r.stdout or "(clean)")