# Epistemic Memory

> Memory that knows what it knows, how it knows it, and how confident it is.

## Structure

```yaml
---
type: memory
category: project-decision | user-preference | technical | lesson | research
status: active | superseded | deprecated
confidence: high | medium | low | unknown
source: user | observation | inference | research
created: 2026-09-10
updated: 2026-09-10
---
```

## Why This Matters

Without metadata, JARVIS cannot distinguish:
- Something the user explicitly said (high confidence)
- Something JARVIS inferred (medium confidence)
- Something JARVIS assumed (low confidence)
- Something JARVIS hallucinated (unknown confidence)

With metadata, JARVIS can:
- Prioritize high-confidence memories
- Flag low-confidence memories for verification
- Detect when inference has been treated as fact
- Correct itself when new evidence arrives

## Anti-Hallucination Loop

The danger loop:

```
JARVIS thinks → writes to memory → reads later → assumes true → acts → writes back
```

The safe loop:

```
OBSERVATION → EVIDENCE → ASSESSMENT → VALIDATION → KNOWLEDGE → MEMORY
```

Every memory should be traceable to its source. If the source is "JARVIS thought about it" — that's inference, not knowledge.
