# File & Folder Restructuring Guide

> Applied to: [[council/README]] — Council extraction project (2026-09-10)

> How to audit, rename, and restructure any project folder from messy to clean.  
> Learn once, apply everywhere. Re-read before starting any restructuring task.

---

## The Problem

Every project accumulates chaos:

- Files with inconsistent naming (`CamelCase`, `kebab-case`, `snake_case`, `UPPERCASE`, random)
- Duplicate data scattered across multiple files
- Wrapper files that just repeat what individual files already say
- Temp files, debug scripts, scratch outputs left behind
- Folders that don't clearly separate concerns
- README files that dump everything instead of acting as an index
- No single source of truth — the same information exists in 3 places

If Tony starts a restructuring project and finds this mess, here's exactly how to fix it.

---

## Phase 1: Audit

Before touching anything, understand what exists.

### Step 1: Map Everything

```
List every file and folder.
Note: name, location, size, type.
```

### Step 2: Read Every File

```
Read the content of each file.
Ask: "What is this file's ACTUAL job?"
Write it down in one sentence per file.
```

### Step 3: Find Redundancy

```
For each piece of data (quotes, tables, facts, names),
ask: "Does this same information appear in another file?"

If YES → that's redundancy. Mark it.
If NO → it's unique to that file. Good.
```

### Step 4: Find Duplication Patterns

```
Common duplication patterns:
- Same quote in both a group file and an individual file
- Same election/vote table in a log AND in individual member files
- Same "Source:" citation repeated across every file
- Same rules/regulations in multiple documents
- Same data in a summary file AND in the files it summarizes
```

### Step 5: Identify Temp/Scratch Files

```
Files that should not exist in a clean project:
- debug scripts (_debug.py, _check.py, _verify.py)
- output files (_output.txt, _baseline_tests.txt)
- temporary files (temp.md, scratch.md)
- migration scripts (after migration is complete)
```

---

## Phase 2: Plan

Before renaming or moving anything, decide the target structure.

### Step 1: Define the Target Structure

```
Write out the IDEAL folder structure.
Every file gets ONE clear purpose.
No file should exist without a reason.
```

### Step 2: Assign Each File a Job

```
For every existing file, decide:
→ KEEP AS-IS (if it already has a clear single job)
→ RENAME (if the name doesn't describe its job)
→ REWRITE (if it contains mixed/duplicate data)
→ DELETE (if its data is redundant or it's a temp file)
→ MERGE (if two files should be one)
→ SPLIT (if one file does too many jobs)
```

### Step 3: Define Naming Convention

Pick ONE convention and stick to it:

```
Recommended: kebab-case for files
  → seat-change-log.md (good)
  → seatChangeLog.md (bad)
  → SEAT_CHANGE_LOG.md (bad)
  → seat_change_log.md (acceptable but less readable)

Folders: lowercase, no spaces
  → council/ (good)
  → Council/ (bad)
  → my council/ (bad)

Profiles/people: first-last.md
  → steve-jobs.md (good)
  → Steve_Jobs.md (bad)
```

---

## Phase 3: Execute

Do the actual restructuring. One change at a time. Verify after each.

### Step 1: Create Clean Files (Don't Move Yet)

```
Write new, clean versions of files that need rewriting.
Do NOT delete the originals yet.
Keep originals as backup until new versions are verified.
```

### Step 2: Rename Files

```
Use consistent naming convention.
If a file has a typo → fix it.
If a file name doesn't describe its job → rename it.
```

### Step 3: Delete Redundant Files

```
After new versions are verified:
- Delete wrapper files that repeat individual data
- Delete group files whose data now lives in the log
- Delete temp/scratch files
```

### Step 4: Update Cross-References

```
If any file links to another file, update the path.
If README links to files, verify all links work.
If seat-change-log references member files, verify paths.
```

---

## Phase 4: Verify

### Step 1: Redundancy Check

```
Search for the same text appearing in 2+ files.
If found → one of them is wrong. Pick the canonical location.
```

### Step 2: Purpose Check

```
For each file, ask: "What is this file's ONE job?"
If you can't answer in one sentence → the file needs fixing.
```

### Step 3: Index Check (README)

```
README should be a pure index.
It should LINK to files, not contain their data.
```

### Step 4: Clean Up Temp Files

```
Delete all audit scripts, migration scripts, temp outputs.
The project folder should contain ONLY the final deliverables.
```

---

## Rules to Always Follow

### Rule 1: One File = One Job

```
BAD:  seat-change-log.md contains member profiles AND election results AND rules
GOOD: seat-change-log.md = only events/timeline
      steve-jobs.md = only Steve Jobs profile
      governance.md = only rules
```

### Rule 2: No Data in Two Places

```
If a quote appears in both:
  → individual-member.md AND group-file.md
  → DELETE it from the group file
  → Keep it in the individual file (canonical location)
```

### Rule 3: README = Index Only

```
README should contain:
  ✓ Links to all files
  ✓ Brief description of what each file contains
  ✓ Navigation structure

README should NOT contain:
  ✗ Actual data/content
  ✗ Duplicated information from other files
  ✗ Full paragraphs of information that belongs elsewhere
```

### Rule 4: Logs = Single Source of Truth

```
If there's a timeline of events:
  → ALL events go in the log
  → Individual files should NOT repeat events
  → Individual files should link to the log if needed
```

### Rule 5: No Wrapper Files

```
BAD:  temporary-seats.md lists who held temporary seats
      (this data already exists in seat-change-log.md)
GOOD: seat-change-log.md has the complete timeline
      temporary-seats.md is deleted
```

### Rule 6: Clean As You Go

```
After every restructuring:
  → Delete temp scripts
  → Delete debug files
  → Delete scratch outputs
  → Project folder should only contain final deliverables
```

---

## The Tony Test

Before considering any restructuring project complete, ask:

```
1. If Tony opens this folder, can he instantly understand what each file does?
2. Could he rename every file without losing any data?
3. Is there any data in 2+ files? (If yes → fix it)
4. Is the README a pure index? (If no → fix it)
5. Are there any temp/scratch files left? (If yes → delete them)
6. Does every file have a clear, single purpose? (If no → restructure it)
7. If you deleted one file, would you lose information that exists NOWHERE else? (If no → the file is redundant)
```

---

## Quick Reference: Naming Convention

```
Files:     kebab-case.md          → seat-change-log.md
Profiles:  first-last.md          → steve-jobs.md
Folders:   lowercase              → council/
Config:    lowercase              → config.yaml
Scripts:   lowercase, prefix _    → _audit.py (temp), deleted after use
```

---

## Quick Reference: File Roles

```
README.md         → Index. Links only. No data.
*-log.md          → Timeline of events. Single source of truth.
*-profile.md      → One entity's unique information.
governance.md     → Rules and procedures.
*.md (general)    → Whatever its filename says it is.
```

---

## Common Mistakes to Avoid

```
1. Creating a group file that just summarizes individual files
   → Individual files ARE the summary. Delete the group file.

2. Putting quotes in both the individual file and a collection file
   → Pick ONE location. Delete the other.

3. Writing election/vote results in every member's file
   → Put results in the log. Members file just says who they are.

4. Duplicating "Source:" citations across every file
   → Source info goes in ONE place (the log or README), not everywhere.

5. Leaving temp scripts in the project folder
   → Delete them immediately after use.

6. Making README a data dump
   → README is a map, not a book.
```

---

*Last updated: 2026-09-10*  
*Lesson learned from: Council extraction project (D:\Project\1111DIVISION\council)*
