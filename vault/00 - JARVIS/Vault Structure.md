# Vault Structure

> The knowledge architecture of 11:11 DIVISION.

```
vault/
├── 00 - JARVIS/
│   ├── Current State.md          ← active project state
│   ├── Architectural Rules.md    ← anti-hallucination rules
│   ├── Epistemic Memory.md       ← memory metadata system
│   ├── File Restructuring Guide.md
│   └── Folder Structure.md
│
├── 01 - Brand/
│   ├── Assets/
│   ├── Moodboard/
│   ├── References/
│   ├── Rituals/
│   └── Strategy/
│
├── 02 - Lore/
│   ├── Canon/
│   ├── Characters/
│   ├── Drops/
│   ├── Faction/
│   ├── Relics/
│   ├── Runtime/
│   ├── Timeline/
│   └── World/
│
├── 03 - Products/
│   ├── Archive/
│   ├── Catalog/
│   ├── Pricing/
│   ├── PO System/
│   └── Production/
│
├── 04 - Decisions/
│   ├── Active Decisions/
│   ├── Decision Records/
│   └── Superseded/
│
├── 05 - People & Personas/
│   ├── User/
│   ├── Personas/
│   └── Council/
│
├── 06 - Skills/
│   ├── Available Skills/
│   ├── Learned Skills/
│   ├── Adapted Skills/
│   └── Skill Reviews/
│
├── 07 - Projects/
│   ├── 11-11 Division/
│   └── Archive/
│
├── 08 - Logs/
│   └── Council Meetings/
│
└── 09 - Archive/
    └── (deprecated knowledge)
```

## Layers

| Layer | Purpose | Who Writes |
|-------|---------|-----------|
| `vault/` | Curated knowledge | JARVIS + Human |
| `.jarvis/` | Machine state | JARVIS only |
| `sessions/` | Raw history | System |
| `audit/` | Execution trail | JARVIS only |

## Rules

1. `vault/` is curated, not a landfill
2. JARVIS must distill before persisting to vault
3. Raw transcripts stay in `sessions/`
4. Every memory has source, timestamp, confidence, status
5. Evidence before knowledge
