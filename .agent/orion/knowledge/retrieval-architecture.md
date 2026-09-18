# ORION Knowledge — Retrieval Architecture

## Core Principle
**Never dump the entire vault into context.** Task → Determine relevance → Search → Retrieve small sections → Reason → Act

---

## Retrieval Flow

```
TASK INPUT
    ↓
EXTRACT QUERY TERMS (objective, entities, constraints)
    ↓
ROUTE TO STORES
    ├── memory/     → preferences, decisions, long-term context
    ├── knowledge/  → reference docs, specs, architectures
    └── experience/ → past tasks, patterns, failures
    ↓
SEARCH EACH STORE (parallel)
    ├── Keyword match (filename, headings, frontmatter)
    ├── Semantic similarity (future: embeddings)
    └── Recency + relevance scoring
    ↓
RANK & FILTER
    ├── Top-K per store (default K=3)
    ├── Deduplicate overlapping content
    └── Relevance threshold (configurable)
    ↓
RETRIEVE SECTIONS
    ├── Extract relevant headings + N lines context
    ├── Preserve provenance (file, line range, store)
    └── Total context budget: ~2000 tokens
    ↓
REASON WITH RETRIEVED CONTEXT
    ├── Synthesize answer/plan
    ├── Cite sources inline
    └── Note gaps (what wasn't found)
    ↓
ACT / RESPOND
```

---

## Store Characteristics

| Store | Purpose | Update Frequency | Query Pattern |
|-------|---------|------------------|---------------|
| memory/ | Decision-critical facts | Low (explicit) | "What did we decide about X?" |
| knowledge/ | Reference truth | Medium (curated) | "How does X work?" |
| experience/ | Audit trail, patterns | High (auto) | "Have we done X before?" |

---

## Search Strategies

### Memory Store
- **Index:** Decision records, preference keys, context sections
- **Match:** Exact term in headings/frontmatter > body text
- **Boost:** Recent decisions, high-confidence entries
- **Filter:** By category (decisions, preferences, context)

### Knowledge Store
- **Index:** Topic files, architecture docs, specs
- **Match:** Topic keywords, section headings
- **Boost:** Authoritative sources, cross-references
- **Filter:** By domain (pipeline, retrieval, personas, skills)

### Experience Store
- **Index:** Task IDs, types, outcomes, lessons
- **Match:** Task type, keywords in lesson/outcome
- **Boost:** Recent, successful, similar task type
- **Filter:** By outcome (success/failure), date range

---

## Context Budget Management

| Budget Tier | Token Limit | Use Case |
|-------------|-------------|----------|
| Micro | ~500 | Quick fact lookup |
| Standard | ~2000 | Typical task execution |
| Deep | ~4000 | Complex analysis/debugging |
| Full | ~8000 | Architecture review (rare) |

**Enforcement:** Hard stop at budget. Truncate lowest-relevance sections first.

---

## Retrieval API (Internal)

```python
def retrieve(task: Task, budget: str = "standard") -> RetrievedContext:
    """
    Main retrieval entry point.
    
    Args:
        task: Structured task from UNDERSTAND stage
        budget: micro | standard | deep | full
    
    Returns:
        RetrievedContext with:
        - memory_sections: List[Section]
        - knowledge_sections: List[Section]
        - experience_sections: List[Section]
        - total_tokens: int
        - gaps: List[str]  # what wasn't found
    """
```

### Section Structure
```python
@dataclass
class Section:
    store: Literal["memory", "knowledge", "experience"]
    file: str              # relative path
    heading: str           # nearest heading
    content: str           # extracted lines
    line_range: Tuple[int, int]
    relevance_score: float
    provenance: str        # why this was retrieved
```

---

## Query Term Extraction

From task objective, extract:
1. **Entities** — proper nouns, component names, file paths
2. **Actions** — verbs indicating intent (analyze, fix, create, etc.)
3. **Constraints** — limits, requirements, negative constraints
4. **Types** — task classification (analysis/creation/fix/research)

Example:
> "Fix the verification logic in ORION core that incorrectly matches substrings"

Extracted:
- Entities: `verification logic`, `ORION core`, `core.py`
- Actions: `fix`, `incorrectly matches`
- Constraints: `substring matching`
- Type: `fix`

---

## Ranking Algorithm (v1)

```
score = 
  0.4 * keyword_overlap(query_terms, section_terms) +
  0.3 * heading_match(query_terms, section_heading) +
  0.2 * recency_boost(section_date) +
  0.1 * authority_boost(section_source)
```

- `keyword_overlap`: Jaccard similarity of term sets
- `heading_match`: 1.0 if query term in heading, 0.5 if in parent heading, 0 otherwise
- `recency_boost`: exponential decay, half-life 30 days
- `authority_boost`: decisions > preferences > context; specs > general docs

---

## Integration with Pipeline

### UNDERSTAND Stage
- Retrieve relevant preferences & decisions for task framing
- Budget: micro

### INSPECT Stage
- Primary retrieval: knowledge + experience for evidence gathering
- Budget: standard

### PLAN Stage
- Retrieve similar past tasks (experience) for pattern reuse
- Budget: micro

### CRITIQUE Stage
- Retrieve relevant decisions & failure patterns
- Budget: micro

---

## Future Enhancements (v2+)

1. **Embedding-based semantic search** — For concept-level matching
2. **Cross-store linking** — Explicit references between stores
3. **Query expansion** — Synonyms, related terms from knowledge graph
4. **Learning to rank** — Feedback from verification outcomes
5. **Incremental indexing** — Watch filesystem for changes
6. **Cache layer** — Hot queries served from memory