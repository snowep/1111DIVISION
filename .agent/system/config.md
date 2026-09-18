# System Configuration

## ORION Configuration

```yaml
orion:
  version: "0.1.0"
  branch: "improve/persona-architecture"
  identity_file: ".agent/orion/identity.md"
  memory_file: ".agent/orion/memory.md"
  experience_file: ".agent/orion/experience.md"
  knowledge_dir: ".agent/orion/knowledge"
  skills_dir: ".agent/orion/skills"
  evolution_dir: ".agent/orion/evolution"
```

## Persona System Configuration

```yaml
personas:
  registry: ".agent/personas/"
  template: ".agent/personas/_template/"
  isolation: true
  auto_promote: false
  promotion_review_required: true
```

## Memory Configuration

```yaml
memory:
  private_dirs:
    - ".agent/orion/"
    - ".agent/personas/*/"
  shared_dir: ".agent/shared/memory/"
  promotion_log: ".agent/shared/memory/index.md"
  compression_threshold_kb: 100
  max_entries_per_category: 1000
```

## Knowledge Configuration

```yaml
knowledge:
  layers:
    - persona: ".agent/personas/*/knowledge/"
    - shared: ".agent/shared/knowledge/"
    - orion: ".agent/orion/knowledge/"
    - project: "projects/*/knowledge/"
  retrieval:
    max_results: 10
    relevance_threshold: 0.7
```

## EXP System Configuration

```yaml
exp:
  awards:
    simple_verified: 10
    normal_verified: 25
    complex_verified: 50
    major_contribution: 100
    recovery: 10
    reusable_improvement: 10
    important_discovery: 10
    exceptional_verification: 10
  levels:
    - name: "Novice"
      min_exp: 0
    - name: "Experienced"
      min_exp: 100
    - name: "Reliable"
      min_exp: 500
    - name: "Specialized"
      min_exp: 1500
    - name: "Advanced"
      min_exp: 5000
```

## Task Configuration

```yaml
tasks:
  dir: ".agent/tasks/"
  templates_dir: ".agent/tasks/templates/"
  require_verification: true
  require_critique: true
  orion_review_threshold: "complex"
```

## Session Configuration

```yaml
sessions:
  dir: ".agent/sessions/"
  auto_log: true
  max_sessions_kept: 50
```

## Evolution Configuration

```yaml
evolution:
  orion_dir: ".agent/orion/evolution/"
  persona_dirs: ".agent/personas/*/evolution/"
  require_test: true
  require_evidence: true
  auto_apply: false
```