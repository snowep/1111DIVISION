import os, subprocess

base = r"D:\Project\1111DIVISION"
os.chdir(base)

# Remove the cleanup script itself
for f in [".tmp_cleanup.py"]:
    p = os.path.join(base, f)
    if os.path.exists(p):
        os.remove(p)

# Check remaining tmp
import glob
left = glob.glob(os.path.join(base, ".tmp_*"))
print("REMAINING TMP:", left if left else "none")

r = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
print("\nSTATUS:\n", r.stdout)

# Add all
r = subprocess.run(["git", "add", "-A"], capture_output=True, text=True)
print("ADD:", r.returncode, r.stderr.strip())

r = subprocess.run(["git", "commit", "-m", "Rebuild vault from founding sources: extract chat-Council of Creators.txt + historical chat.json into brand bible, lore, design system, production, market, real decisions DEC-001..007, personas, milestones; remove invented placeholder decisions"], capture_output=True, text=True)
print("\nCOMMIT:", r.returncode)
print(r.stdout)
print(r.stderr)

r = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
print("PUSH:", r.returncode)
print((r.stdout or "")[-500:])
print((r.stderr or "")[-500:])

r = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
print("\nFINAL STATUS:", r.stdout or "(clean)")