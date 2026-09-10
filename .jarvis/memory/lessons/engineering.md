# Engineering Lessons

## file-organization
- one file = one job, no exceptions
- no data in two places — pick canonical location
- README = index only, links not data
- logs = single source of truth
- no wrapper files that summarize individual files
- clean as you go, delete temp scripts immediately

## naming
- files: kebab-case.md
- folders: lowercase
- profiles: first-last.md

## restructuring-process
1. audit → read all, find redundancy
2. plan → define target, assign jobs
3. execute → write clean, rename, delete
4. verify → check duplication, purpose, index

## surface-separation
- vault/ = human-readable, shared, Obsidian
- .jarvis/ = machine-readable, internal, operational
- never expose .jarvis/ state as prose in vault
