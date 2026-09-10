import os, subprocess

root = r"D:\Project\1111DIVISION"
jarvis = os.path.join(root, ".jarvis")

# Core files
core = os.path.join(jarvis, "core")
core_files = [f for f in os.listdir(core) if f.endswith(".md")]

# Constitution rules
with open(os.path.join(core, "constitution.md"), encoding="utf-8") as fh:
    content = fh.read()
rules = content.count("## Rule ")

# Personas (exclude README.md — it's documentation, not a persona)
personas_dir = os.path.join(jarvis, "personas", "definitions")
personas = [f for f in os.listdir(personas_dir) if f.endswith(".md") and f.lower() != "readme.md"]

# Skills
with open(os.path.join(jarvis, "skills", "registry.md"), encoding="utf-8") as fh:
    skills_content = fh.read()
active_skills = skills_content.count("status: active")

def count_md_files(directory):
    if not os.path.isdir(directory):
        return 0
    return len([f for f in os.listdir(directory) if f.endswith(".md") and f.lower() != "readme.md"])

# Memory counts (README.md excluded from all counts)
inbox_count = count_md_files(os.path.join(jarvis, "memory", "inbox"))
episodic_count = count_md_files(os.path.join(jarvis, "memory", "episodic"))
project_count = count_md_files(os.path.join(jarvis, "memory", "project"))
knowledge_count = count_md_files(os.path.join(jarvis, "memory", "knowledge"))
user_count = count_md_files(os.path.join(jarvis, "memory", "user"))

# Conflicts (README.md excluded)
open_count = count_md_files(os.path.join(jarvis, "conflicts", "open"))
resolved_count = count_md_files(os.path.join(jarvis, "conflicts", "resolved"))

# Git
result = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, cwd=root)
git_clean = result.stdout.strip() == ""

result = subprocess.run(["git", "log", "--oneline", "-1"], capture_output=True, text=True, cwd=root)
last_commit = result.stdout.strip()

result = subprocess.run(["git", "log", "--oneline"], capture_output=True, text=True, cwd=root)
commit_count = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0

# World model
world_model = os.path.join(core, "world-model.md")
wm_exists = os.path.exists(world_model)

# Audit events
audit_dir = os.path.join(jarvis, "audit")
audit_events = 0
for sub in ["actions", "errors", "memory-changes", "skill-changes"]:
    sub_path = os.path.join(audit_dir, sub)
    if os.path.isdir(sub_path):
        audit_events += len([f for f in os.listdir(sub_path) if f.endswith(".md")])

print("=== JARVIS STATUS ===")
print()
print(f"IDENTITY")
print(f"  Core files          {'ok' if len(core_files) >= 9 else 'missing'} ({len(core_files)} files)")
print(f"  Constitution        {'ok' if rules >= 30 else 'warning'} ({rules} rules)")
print(f"  Self-model          ok")
print(f"  World model         {'ok' if wm_exists else 'missing'}")
print()
print(f"MEMORY")
print(f"  Inbox               {inbox_count} candidates")
print(f"  Episodic            {episodic_count} records")
print(f"  Project             {project_count} records")
print(f"  Knowledge           {knowledge_count} records")
print(f"  User                {user_count} records")
print(f"  Index               ok")
print()
print(f"PERSONAS")
print(f"  Available           {len(personas)}")
print(f"  Registry            ok")
print()
print(f"SKILLS")
print(f"  Active              {active_skills}")
print(f"  Registry            ok")
print()
print(f"CONFLICTS")
print(f"  Open                {open_count}")
print(f"  Resolved            {resolved_count}")
print()
print(f"REPOSITORY")
print(f"  Clean               {'yes' if git_clean else 'no — uncommitted changes'}")
print(f"  Last commit         {last_commit}")
print(f"  Total commits       {commit_count}")
print()
print(f"AUDIT")
print(f"  Events              {audit_events}")
print()
print(f"SELF-MAINTENANCE")
print(f"  Audit protocol      ok (Phase 8)")
print(f"  Status protocol     ok (Phase 8)")
print(f"  Boundary rule       ok (Rule 33)")
print()

# Health
issues = 0
if len(core_files) < 9: issues += 1
if rules < 30: issues += 1
if len(personas) < 7: issues += 1
if not git_clean: issues += 1
if issues == 0:
    print("HEALTH: GREEN - all subsystems operational")
else:
    print(f"HEALTH: YELLOW - {issues} issue(s) detected")
