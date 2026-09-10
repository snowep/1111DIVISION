# Architecture Statement — 11:11 DIVISION Knowledge System

**Date:** 2026-09-10
**Author:** JARVIS
**Status:** Active

---

## Why This Structure

The repository uses a **two-surface architecture**: one for human-readable knowledge, one for machine-operational state. This is not arbitrary. It solves a specific set of problems that simpler structures cannot.

---

## The Problem With Flat Structures

A flat structure like this:

```
project/
├── notes/
├── memory/
├── decisions/
├── skills/
└── council/
```

works until it doesn't. The failure mode is **entanglement**. When everything lives in one surface, JARVIS cannot distinguish between:

- What the human curated intentionally
- What JARVIS generated automatically
- What was raw conversation output
- What was validated knowledge

The result is a landfill. Obsidian becomes a dump of chat transcripts, terminal logs, half-formed thoughts, and JARVIS hallucinations — all equally weighted, all equally untrustworthy.

---

## Why Two Surfaces

### `vault/` — Curated Knowledge

This is Obsidian. The human opens it, reads it, edits it, restructures it. JARVIS maintains it as part of a shared contract. Everything here is **intentional** — curated, organized, linked.

**Rule:** JARVIS must distill conversations before persisting to vault. Raw transcripts stay in `sessions/`.

### `.jarvis/` — Machine State

This is JARVIS's private brain. Identity, memory, capabilities, skills, sessions, audit trail, cache. The human never edits this directly. It is **operational**, not editorial.

**Rule:** `.jarvis/` is append-only for audit. Memory is corrected, not deleted.

### `sessions/` — Raw History

Every conversation, every terminal output, every tool call. This is the landfill — but a controlled one. JARVIS references sessions when distilling, but sessions are never treated as knowledge.

**Rule:** Sessions are evidence, not authority.

### `audit/` — Execution Trail

Every action JARVIS takes. Commands run, files modified, memory changed, skills adapted. Append-only. For forensic analysis, not daily reference.

**Rule:** Audit is immutable. Never delete.

---

## Why This Over Alternatives

### Alternative: Single `memory/` folder

**Problem:** Conflates user preferences, project decisions, technical lessons, and research notes. No distinction between what the human decided and what JARVIS inferred. No metadata. No confidence levels. A hallucination stored here looks identical to an explicit user instruction.

**Solution:** `.jarvis/memory/` separates into `user/`, `projects/`, `decisions/`, `lessons/`, `research/` — each with metadata (source, timestamp, confidence, status).

### Alternative: Everything in Obsidian

**Problem:** JARVIS's operational state (current session, active tasks, cache) pollutes the human's knowledge base. Terminal logs, session dumps, and JARVIS internal reasoning appear alongside curated decisions and brand strategy.

**Solution:** `.jarvis/` holds operational state. `vault/` holds curated knowledge. Clean separation.

### Alternative: No audit trail

**Problem:** When something goes wrong — a bad file delete, an incorrect memory, a hallucination that became "fact" — there's no way to trace what happened.

**Solution:** `.jarvis/audit/` records every action. Immutable. Forensic analysis possible.

### Alternative: No session history

**Problem:** JARVIS cannot revisit context from previous conversations. Decisions made in chat are lost when the session ends.

**Solution:** `sessions/` preserves raw history. JARVIS distills important content into vault before it becomes knowledge.

---

## Why The Numbered Vault Structure

```
vault/
├── 00 - JARVIS/          (meta: how JARVIS works)
├── 01 - Projects/        (active project knowledge)
├── 02 - Knowledge/       (reference material by domain)
├── 03 - Research/        (external research)
├── 04 - Decisions/       (institutional memory)
├── 05 - People & Personas/ (council, personas, user)
├── 06 - Skills/          (skill lifecycle)
├── 07 - Ideas/           (inbox → developing → archive)
├── 08 - Logs/            (council meetings, experiments, milestones)
└── 99 - Archive/         (deprecated knowledge)
```

**Why numbered:** Consistent ordering. No alphabetical drift. JARVIS and Obsidian both benefit from predictable sort order.

**Why 00 first:** JARVIS meta-knowledge (current state, architectural rules) must be the first thing JARVIS reads. It is the operating context.

**Why 99 last:** Archive is explicitly separated. Deprecated knowledge doesn't mix with active knowledge.

**Why separated by domain:** Each number represents a distinct knowledge domain. Cross-references use Obsidian `[[links]]`. No file belongs to two domains.

---

## Why Council and Docs Stay at Root

```
council/     ← canonical council configuration (source of truth)
docs/        ← technical documentation
src/         ← application code
tests/       ← test suite
scripts/     ← utilities
```

**`council/`** is not knowledge — it is configuration. The canonical seat definitions, member profiles, and seat-change log are the **source of truth** for council structure. `vault/05 - People & Personas/Council/` holds derived knowledge (meeting records, analysis). Configuration lives at root. Knowledge lives in vault.

**`docs/`**, **`src/`**, **`tests/`**, **`scripts/`** are standard project directories. They belong at root because they are project infrastructure, not knowledge.

---

## Why Epistemic Memory Matters

The most dangerous failure mode for an AI operating system is the **hallucination amplification loop**:

```
JARVIS thinks something
↓
JARVIS writes it to memory
↓
JARVIS reads it later
↓
JARVIS assumes it is true
↓
JARVIS acts on it
↓
JARVIS writes the result back
```

A hallucination becomes "fact" simply because it was persisted. The memory looks authoritative. JARVIS treats it as authoritative. The error compounds.

**Solution:** Every memory carries metadata:

```yaml
source: user | observation | inference | research
confidence: high | medium | low | unknown
status: active | superseded | deprecated
```

JARVIS can now distinguish:
- "The user explicitly said this" (high confidence, source: user)
- "JARVIS inferred this from context" (medium confidence, source: inference)
- "JARVIS assumed this" (low confidence, source: inference)
- "JARVIS hallucinated this" (unknown confidence, source: unknown)

This is **epistemic memory** — memory that knows what it knows, how it knows it, and how confident it is.

---

## Why Skills Have a Lifecycle

Skills are not static. They are discovered, inspected, validated, adapted, tested, and activated. Or rejected.

```
DISCOVERED → INSPECTED → VALIDATED → ADAPTED → TESTED → ACTIVE → IMPROVED
     ↓
  REJECTED
```

Two surfaces:
- `vault/06 - Skills/` — human-readable skill knowledge
- `.jarvis/skills/` — machine state (installed, adapted, discovered, rejected)

JARVIS can receive a GitHub skill, understand it, adapt it, and use it automatically. Each skill gets a review before activation. Rejected skills are recorded with rejection reason.

---

## Why Personas Have Activation Conditions

Personas are not just names. They are reasoning perspectives with **activation conditions**:

```yaml
auto-activate:
  - credentials
  - external-execution
  - permissions-change
```

JARVIS reads the task context, checks activation conditions, and applies the right persona without the user asking. Security-sensitive code triggers Security Architect. Design decisions trigger Brutal Creative Director. Major decisions trigger Devil's Advocate.

This is not magic. It is structured matching. The persona files define the conditions. JARVIS checks them.

---

## Why Decisions Link to Council Meetings

Council meetings are not just conversations. They are institutional memory. Each meeting records:
- The question
- Each seat's position
- The conflicts
- The vote
- JARVIS's synthesis
- The final decision
- The linked DEC-XXX record

This creates a traceable chain: **question → debate → decision → consequence**. Six months later, JARVIS can answer "why did we decide X?" by tracing back through the council meeting that produced the decision.

---

## Summary

This structure exists because:

1. **Separation of concerns** — human knowledge vs. machine state vs. raw history
2. **Anti-hallucination** — epistemic memory with metadata prevents confidence inflation
3. **Institutional memory** — decisions and council meetings are permanent, traceable, linked
4. **Skill lifecycle** — external capabilities are discovered, validated, adapted, not blindly copied
5. **Persona activation** — reasoning perspectives engage automatically based on context
6. **Clean Obsidian** — vault is curated knowledge, not a landfill of chat transcripts
7. **Forensic capability** — audit trail and session history enable analysis when things go wrong

The alternative — everything in one folder, no metadata, no separation, no lifecycle — produces a system that looks organized but fails silently. Hallucinations persist. Decisions are forgotten. Skills are copied without understanding. Personas are never activated.

This structure makes the invisible visible. It forces JARVIS to know what it knows, how it knows it, and how confident it is.

That is the difference between a chatbot with file access and an operating intelligence.
