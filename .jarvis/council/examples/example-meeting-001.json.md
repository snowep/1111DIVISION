# Example: Resolved Council Output (Schema Conformance)

> A worked, fully-resolved example of a council meeting serialized against the
> Phase 10 schemas. Proves the schema accepts real structured output.
> This is NOT a real meeting — it exists to validate the API contract.
>
> Reference: `.jarvis/council/api-schema.md`
> Schema files: `.jarvis/council/schemas/*.json`

---

## Meeting: MEETING-20260911-001

**Question:** "Should 11:11 Division adopt a limited-drop model for Drop 002?"

**Meeting Type:** `strategic-direction`
**Status:** `complete`
**Participants:** Security Architect, Systems Engineer, Business Strategist, Skeptic

---

## Evidence (Schema 1)

```json
[
  {
    "id": "EVD-001",
    "meeting_id": "MEETING-20260911-001",
    "description": "ComplexCon 2025 limited drops sold out in under 2 minutes",
    "type": "external-article",
    "source": "Hypebeast article: 'ComplexCon 2025 Recap'",
    "source_type": "web",
    "confidence": 0.75,
    "verified": false,
    "phase": "pre-meeting",
    "registered_by": "jarvis",
    "registered_at": "2026-09-11T09:00:00Z",
    "cited_by": ["POS-MEETING-20260911-001-persona.business-strategist"]
  },
  {
    "id": "EVD-002",
    "meeting_id": "MEETING-20260911-001",
    "description": "Drop 001 sold out via full inventory in 3 hours without artificial scarcity",
    "type": "historical",
    "source": "JARVIS memory: Drop 001 sales data",
    "source_type": "memory",
    "confidence": 0.85,
    "verified": true,
    "phase": "pre-meeting",
    "registered_by": "jarvis",
    "registered_at": "2026-09-11T09:01:00Z",
    "cited_by": ["POS-MEETING-20260911-001-persona.systems-engineer", "POS-MEETING-20260911-001-persona.business-strategist"]
  },
  {
    "id": "EVD-003",
    "meeting_id": "MEETING-20260911-001",
    "description": "Scalpers resold Drop 001 items at 2.5-4x retail within 48 hours",
    "type": "direct-observation",
    "source": "JARVIS filesystem scan of resale channel tracking doc",
    "source_type": "file",
    "confidence": 0.9,
    "verified": true,
    "phase": "pre-meeting",
    "registered_by": "jarvis",
    "registered_at": "2026-09-11T09:02:00Z",
    "cited_by": ["POS-MEETING-20260911-001-persona.security-architect"]
  }
]
```

---

## Positions (Schema 2)

```json
[
  {
    "id": "POS-MEETING-20260911-001-persona.security-architect",
    "meeting_id": "MEETING-20260911-001",
    "persona_id": "persona.security-architect",
    "persona_name": "Security Architect",
    "vote": "approve-with-conditions",
    "confidence": 0.85,
    "reasoning": "Scarcity increases both desirability and fraud vectors; must be paired with bot protection",
    "supporting_arguments": [
      { "id": "ARG-SEC-01", "text": "Limited drops create verification bottleneck opportunities", "evidence_ids": ["EVD-003"], "strength": "strong" }
    ],
    "counterarguments": [
      { "id": "ARG-SEC-02", "text": "Scarcity events attract malicious traffic", "evidence_ids": ["EVD-003"], "strength": "moderate" }
    ],
    "conditions": ["Bot detection must be live before drop", "Rate limiting on purchase endpoint"],
    "assumptions": ["Scalper behavior observed in Drop 001 will scale with scarcity"],
    "evidence_used": [
      { "evidence_id": "EVD-003", "interpretation": "Resale markup proves demand exceeds supply, but also proves verification is needed" }
    ],
    "reversal_conditions": [
      {
        "id": "REV-SEC-01",
        "condition": "Drop 002 scalper ratio exceeds 30%",
        "threshold": ">30% of purchases by suspected bot accounts",
        "currently_met": false,
        "evidence_required": "Post-drop transaction analysis"
      }
    ],
    "activated_at": "2026-09-11T09:30:00Z",
    "deactivated_at": "2026-09-11T09:45:00Z",
    "phase": "pre-meeting",
    "flags": []
  },
  {
    "id": "POS-MEETING-20260911-001-persona.systems-engineer",
    "meeting_id": "MEETING-20260911-001",
    "persona_id": "persona.systems-engineer",
    "persona_name": "Systems Engineer",
    "vote": "approve",
    "confidence": 0.8,
    "reasoning": "Infrastructure held under full-inventory load; scarcity reduces concurrent load",
    "supporting_arguments": [
      { "id": "ARG-SYS-01", "text": "Scarcity reduces concurrent connection load on purchase flow", "evidence_ids": ["EVD-002"], "strength": "strong" }
    ],
    "counterarguments": [],
    "conditions": [],
    "assumptions": ["Traffic pattern during Drop 002 is similar to Drop 001"],
    "evidence_used": [
      { "evidence_id": "EVD-002", "interpretation": "Drop 001 completed full load without system failure, so scarcity is not required for stability" }
    ],
    "reversal_conditions": [
      {
        "id": "REV-SYS-01",
        "condition": "Infrastructure cannot sustain 3 hours of full-inventory load",
        "threshold": "Error rate exceeds 5% during load test",
        "currently_met": false,
        "evidence_required": "Load test report"
      }
    ],
    "activated_at": "2026-09-11T09:45:00Z",
    "deactivated_at": "2026-09-11T10:00:00Z",
    "phase": "pre-meeting",
    "flags": []
  },
  {
    "id": "POS-MEETING-20260911-001-persona.business-strategist",
    "meeting_id": "MEETING-20260911-001",
    "persona_id": "persona.business-strategist",
    "persona_name": "Business Strategist",
    "vote": "approve",
    "confidence": 0.9,
    "reasoning": "Scarcity maximizes perceived value and controls resale narrative",
    "supporting_arguments": [
      { "id": "ARG-BIZ-01", "text": "Limited drops are the standard for streetwear brand positioning", "evidence_ids": ["EVD-001"], "strength": "strong" }
    ],
    "counterarguments": [
      { "id": "ARG-BIZ-02", "text": "Artificial scarcity can backfire if perceived as manipulation", "evidence_ids": [], "strength": "weak" }
    ],
    "conditions": [],
    "assumptions": ["Target demographic responds positively to limited drops"],
    "evidence_used": [
      { "evidence_id": "EVD-001", "interpretation": "Industry precedent (ComplexCon) supports scarcity model" },
      { "evidence_id": "EVD-002", "interpretation": "Full inventory also sold out, suggesting demand could sustain either model" }
    ],
    "reversal_conditions": [
      {
        "id": "REV-BIZ-01",
        "condition": "Customer surveys show negative sentiment toward artificial scarcity",
        "threshold": ">60% negative sentiment in post-drop survey",
        "currently_met": false,
        "evidence_required": "Post-drop customer survey data"
      }
    ],
    "activated_at": "2026-09-11T10:00:00Z",
    "deactivated_at": "2026-09-11T10:15:00Z",
    "phase": "pre-meeting",
    "flags": []
  },
  {
    "id": "POS-MEETING-20260911-001-persona.skeptic",
    "meeting_id": "MEETING-20260911-001",
    "persona_id": "persona.skeptic",
    "persona_name": "Skeptic",
    "vote": "reject",
    "confidence": 0.75,
    "reasoning": "We have zero evidence scarcity improves long-term brand equity; Drop 001 succeeded without it",
    "supporting_arguments": [
      { "id": "ARG-SKE-01", "text": "No causal link between scarcity and long-term loyalty", "evidence_ids": ["EVD-001", "EVD-002"], "strength": "moderate" }
    ],
    "counterarguments": [
      { "id": "ARG-SKE-02", "text": "Scarcity is industry standard but that is correlation, not causation", "evidence_ids": ["EVD-001"], "strength": "strong" }
    ],
    "conditions": [],
    "assumptions": ["Long-term brand equity is the primary success metric"],
    "evidence_used": [
      { "evidence_id": "EVD-001", "interpretation": "Industry precedent shows popularity, not necessarily equity" },
      { "evidence_id": "EVD-002", "interpretation": "Drop 001 proves full inventory works" }
    ],
    "reversal_conditions": [
      {
        "id": "REV-SKE-01",
        "condition": "Data shows limited-drop brands retain customers at higher rates",
        "threshold": "Longitudinal retention study across competing brands",
        "currently_met": false,
        "evidence_required": "Retention cohort data"
      }
    ],
    "activated_at": "2026-09-11T10:15:00Z",
    "deactivated_at": "2026-09-11T10:30:00Z",
    "phase": "pre-meeting",
    "flags": []
  }
]
```

---

## Cross-Examination (Schema 3)

```json
{
  "meeting_id": "MEETING-20260911-001",
  "skipped": false,
  "conflicts": [
    {
      "id": "CONFLICT-001",
      "disagreement": "Whether artificial scarcity is necessary or beneficial for Drop 002",
      "materiality": "high",
      "positions_in_conflict": [
        {
          "participant": "Business Strategist",
          "stance": "approve",
          "primary_evidence": ["EVD-001"],
          "core_reasoning": "Industry standard; maximizes perceived value"
        },
        {
          "participant": "Skeptic",
          "stance": "reject",
          "primary_evidence": ["EVD-002"],
          "core_reasoning": "No evidence of long-term equity benefit; Drop 001 succeeded without it"
        }
      ],
      "evidence_comparison": [
        {
          "evidence_id": "EVD-001",
          "interpretation_a": "Proof the scarcity model is viable and expected",
          "interpretation_b": "Correlation with popularity, not causation of equity"
        }
      ],
      "resolution_options": [
        { "id": "A", "description": "Full limited-drop model (cap at 1000 units)", "supported_by": ["Business Strategist"], "type": "position" },
        { "id": "B", "description": "Full inventory model (no artificial cap)", "supported_by": ["Skeptic"], "type": "position" },
        { "id": "C", "description": "Dual-tier: limited opening allocation + open restock window", "supported_by": [], "type": "compromise" }
      ],
      "jarvis_assessment": "Resolution C (dual-tier) is strongest: it captures scarcity-driven demand signal without betting the entire drop on artificial cap.",
      "strongest_option_id": "C"
    }
  ]
}
```

---

## Agreement (Schema 4)

```json
{
  "meeting_id": "MEETING-20260911-001",
  "full": [
    {
      "id": "AGR-FULL-001",
      "conclusion": "Adopt a controlled distribution model with security measures",
      "participants": ["Security Architect", "Systems Engineer"],
      "shared_reasoning": "Distribution needs operational control to avoid infrastructure and fraud risk"
    }
  ],
  "qualified": [
    {
      "id": "AGR-QUAL-001",
      "conclusion": "Adopt a limited-drop model",
      "reasoning_map": [
        { "participant": "Business Strategist", "reasoning": "Maximizes perceived brand value" },
        { "participant": "Security Architect", "reasoning": "Creates manageable verification bottleneck" }
      ]
    }
  ],
  "partial": [
    {
      "id": "AGR-PART-001",
      "agreed_items": [
        { "description": "Security measures needed", "consensus": "4/4 participants" }
      ],
      "disagreed_items": [
        { "description": "Whether scarcity should be artificial or natural", "consensus": "Split 3/1", "sides": ["Business Strategist", "Skeptic"] }
      ]
    }
  ],
  "disagreement": [
    {
      "id": "AGR-DIS-001",
      "participants": ["Business Strategist", "Skeptic"],
      "conflict": "Artificial scarcity strategy",
      "evidence_for": ["EVD-001"],
      "evidence_against": ["EVD-002"]
    }
  ],
  "abstentions": [],
  "summary": {
    "full_count": 1,
    "qualified_count": 1,
    "partial_count": 1,
    "disagreement_count": 1,
    "abstention_count": 0,
    "total_positions": 4,
    "core_question_alignment": "qualified",
    "implementation_alignment": "partial"
  }
}
```

---

## Confidence Propagation (Schema 5)

```json
{
  "meeting_id": "MEETING-20260911-001",
  "meeting_type": "strategic-direction",
  "weights": {
    "evidence_quality": 0.25,
    "persona_convergence": 0.35,
    "argument_strength": 0.20,
    "counterargument_weakness": 0.20
  },
  "evidence_quality": {
    "score": 0.83,
    "weight": 0.25,
    "calculation": "Mean confidence of EVD-001 (0.75), EVD-002 (0.85), EVD-003 (0.90) = 0.83",
    "inputs": ["EVD-001: 0.75", "EVD-002: 0.85", "EVD-003: 0.90"]
  },
  "persona_convergence": {
    "score": 0.75,
    "weight": 0.35,
    "calculation": "1 - (agreement groups 2 / total positions 4) = 0.50, +0.25 for unanimous security point",
    "inputs": ["full: 1", "qualified: 1", "disagreement: 1"]
  },
  "argument_strength": {
    "score": 0.70,
    "weight": 0.20,
    "calculation": "4 strong/moderate supports vs 3 counters = 0.57, adjusted +0.13 for unanimous security reasoning",
    "inputs": ["strong supports: 3", "moderate supports: 1", "counters: 3"]
  },
  "counterargument_weakness": {
    "score": 0.65,
    "weight": 0.20,
    "calculation": "Inverse of mean counter strength (2 moderate, 1 weak = 0.65 avg strength → weakness 0.35)",
    "inputs": ["counter strengths: moderate, moderate, weak"]
  },
  "meeting_confidence": 0.742,
  "confidence_label": "HIGH"
}
```

---

## Recommendation (Schema 7 nested)

```json
{
  "id": "council-recommendation-MEETING-20260911-001",
  "text": "Adopt a dual-tier distribution model: limited opening allocation (1000 units) followed by a 3-hour open restock window, with bot detection and rate limiting active for the opening.",
  "status": "candidate",
  "evidence_ids": ["EVD-001", "EVD-002", "EVD-003"],
  "type": "council-recommendation"
}
```

---

## Reversal Conditions (Schema 10)

```json
[
  {
    "id": "REV-SEC-01",
    "condition": "Drop 002 scalper ratio exceeds 30%",
    "threshold": ">30% of purchases by suspected bot accounts",
    "currently_met": false,
    "evidence_required": "Post-drop transaction analysis",
    "raised_by": "Security Architect",
    "source_meeting_id": "MEETING-20260911-001",
    "source_position_id": "POS-MEETING-20260911-001-persona.security-architect"
  },
  {
    "id": "REV-BIZ-01",
    "condition": "Customer surveys show negative sentiment toward artificial scarcity",
    "threshold": ">60% negative sentiment",
    "currently_met": false,
    "evidence_required": "Post-drop customer survey data",
    "raised_by": "Business Strategist",
    "source_meeting_id": "MEETING-20260911-001",
    "source_position_id": "POS-MEETING-20260911-001-persona.business-strategist"
  }
]
```

---

## Decision (Schema 8, after user approval)

```json
{
  "id": "DEC-005",
  "question": "Should 11:11 Division adopt a limited-drop model for Drop 002?",
  "recommendation_id": "council-recommendation-MEETING-20260911-001",
  "meeting_id": "MEETING-20260911-001",
  "decision": "Adopt dual-tier distribution model with bot protection",
  "rationale": "Captures scarcity demand signal without full artificial cap; security architect conditions accepted",
  "status": "active",
  "authority": "user-explicit",
  "approved_by": "user",
  "approved_at": "2026-09-12T09:00:00Z",
  "confidence": 0.742,
  "confidence_label": "HIGH",
  "evidence_ids": ["EVD-001", "EVD-002", "EVD-003"],
  "reversal_conditions": [
    { "condition": "Scalper ratio > 30%", "threshold": "quantitative", "currently_met": false }
  ],
  "created_at": "2026-09-11T11:00:00Z",
  "superseded_by": null,
  "superseded_at": null,
  "source_meeting_id": "MEETING-20260911-001",
  "vault_path": "vault/04 - Decisions/Active Decisions/DEC-005 - Drop Model.md"
}
```

---

## Knowledge File (Schema 9, after persistence)

```json
{
  "id": "vault::04 - Decisions/Active Decisions/DEC-005 - Drop Model.md",
  "path": "04 - Decisions/Active Decisions/DEC-005 - Drop Model.md",
  "filename": "DEC-005 - Drop Model.md",
  "type": "decision",
  "content_type": "markdown",
  "title": "DEC-005 - Drop Model",
  "description": "Dual-tier distribution model for 11:11 Division",
  "tags": ["decision", "drop-model", "distribution", "strategy"],
  "created_at": "2026-09-12T09:00:00Z",
  "updated_at": "2026-09-12T09:00:00Z",
  "author": "council",
  "content": "# DEC-005 - Drop Model\n\nAdopt dual-tier distribution...",
  "content_hash": "ab2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
  "source_meeting_id": "MEETING-20260911-001",
  "source_decision_id": "DEC-005",
  "superseded_by": null,
  "version": 1,
  "related_files": [],
  "referenced_by": []
}
```

---

## Conformance Notes

| Schema | Conforms | Notes |
|--------|----------|-------|
| Evidence (Schema 1) | ✅ | 3 items, mixed classes, phases, verified statuses |
| Position (Schema 2) | ✅ | 4 positions, mixed votes, reversal conditions on all |
| CrossExamination (Schema 3) | ✅ | 1 conflict, 3 resolution options, compromise present |
| Agreement (Schema 4) | ✅ | All 4 non-empty categories exercised |
| ConfidencePropagation (Schema 5) | ✅ | Strategic-direction weights used; weighted sum = 0.742 = HIGH |
| Vote (Schema 6) | ✅ | Implicit in positions; enforced in meeting-record |
| MeetingRecord (Schema 7) | ✅ | All composed objects present |
| Decision (Schema 8) | ✅ | Candidate → active transition with authority fields |
| KnowledgeFile (Schema 9) | ✅ | Decision persisted to vault with lineage |
| ReversalCondition (Schema 10) | ✅ | Aggregate tracker at meeting + decision level |