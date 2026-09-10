# Architectural Rules

> The rules that prevent JARVIS from becoming dangerous.

## Rule 1: JARVIS Memory Is Not Infallible Authority

JARVIS may maintain its own memory and capabilities, but it must never treat its own memory as infallible authority.

**Why:** A hallucination becomes "fact" simply because it was persisted. The feedback loop is:

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

This is a hallucination amplifier. Memory persistence ≠ truth.

## Rule 2: Obsidian Is the Long-Term Knowledge Layer, Not Execution Authority

`vault/` is curated knowledge. `sessions/` is raw history. `.jarvis/` is machine state.

The AI should **distill** conversations rather than permanently dumping them into the vault.

```
vault/        → curated knowledge
.jarvis/      → machine state + operational memory
sessions/     → raw history
audit/        → execution history
```

## Rule 3: Evidence Before Knowledge

The correct flow:

```
OBSERVATION → EVIDENCE → ASSESSMENT → VALIDATION → KNOWLEDGE → MEMORY
```

Not:

```
THOUGHT → MEMORY → ASSUMPTION → ACTION → MEMORY
```

## Rule 4: Memory Requires Metadata

Every important memory should have:

```yaml
source: user | observation | inference | research
timestamp: 2026-09-10
confidence: high | medium | low | unknown
status: active | superseded | deprecated
```

This gives JARVIS **epistemic memory** — memory that knows what it knows, how it knows it, and how confident it is.

## Rule 5: Vault Is Curated, Not a Landfill

Do not put into vault/:
- Raw chat transcripts
- Terminal logs
- Every observation
- Every thought
- Every memory

Put into vault/:
- Curated knowledge
- Decision records
- Council meeting summaries
- Personas
- Skills
- Architecture
- Procedures

## Rule 6: Two Surfaces, Clean Separation

- `vault/` — human-readable, Obsidian-native, both human and JARVIS read/write
- `.jarvis/` — machine-readable, JARVIS-internal, not for direct human editing

## Rule 7: Memory Correction Is Mandatory

If new evidence contradicts old memory:
1. Detect the conflict
2. Compare evidence
3. Update the memory
4. Preserve reasoning when useful
5. Remove obsolete information

Never allow old memories to silently override newer explicit user instructions.
