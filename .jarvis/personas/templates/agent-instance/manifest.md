---
# Agent Instance — Manifest (template)
# Copy the whole template folder per instance:
#   .jarvis/personas/instances/<MEET-YYYYMMDD-NNN>/
# Fill these fields, keep the rest as scaffolding.

instance_id: AGT-<MEETING-ID>-<PERSONA-ID>
meeting_id: <MEET-YYYYMMDD-NNN>
persona_id: <persona-id>
persona_name: <Display Name>
parent: jarvis

task: >
  <One sentence: what this instance must do.>
scope: <architecture | security | design | business | strategy | research>

independent_context: true

# Boundaries — defaults are read-only, non-mutating.
can_write_project: false
can_modify_memory: false
can_modify_constitution: false
can_execute_terminal: false

created: <timestamp>
status: active
---