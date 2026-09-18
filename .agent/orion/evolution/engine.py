"""
ORION Evolution Engine

Evolution is controlled, testable, and evidence-based.

Pipeline:
    OBSERVE PROBLEM → COLLECT EVIDENCE → PROPOSE CHANGE → TEST → EVALUATE → ACCEPT/REJECT → VERSION
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..evaluator import EvaluationResult


class EvolutionStatus(str, Enum):
    """Status of an evolution proposal."""
    OBSERVED = "OBSERVED"
    EVIDENCE_COLLECTED = "EVIDENCE_COLLECTED"
    PROPOSED = "PROPOSED"
    TESTING = "TESTING"
    EVALUATING = "EVALUATING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    VERSIONED = "VERSIONED"


class EvolutionDecision(str, Enum):
    """Decision on an evolution proposal."""
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"


@dataclass
class EvolutionProposal:
    """A controlled self-improvement proposal."""
    id: str
    title: str
    problem: str
    evidence: List[str]
    proposed_change: str
    expected_benefit: str
    risk: str
    test_plan: str
    status: EvolutionStatus = EvolutionStatus.OBSERVED
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    test_result: Optional[Dict[str, Any]] = None
    evaluation: Optional[Dict[str, Any]] = None
    decision: Optional[EvolutionDecision] = None
    decision_reason: str = ""
    version: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "problem": self.problem,
            "evidence": self.evidence,
            "proposed_change": self.proposed_change,
            "expected_benefit": self.expected_benefit,
            "risk": self.risk,
            "test_plan": self.test_plan,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "test_result": self.test_result,
            "evaluation": self.evaluation,
            "decision": self.decision.value if self.decision else None,
            "decision_reason": self.decision_reason,
            "version": self.version,
        }


@dataclass
class EvolutionTestResult:
    """Result of testing an evolution proposal."""
    passed: bool
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "metrics": self.metrics,
            "errors": self.errors,
            "notes": self.notes,
        }


class EvolutionEngine:
    """
    Manages controlled self-improvement proposals.

    The engine does not apply changes automatically. A proposal must pass
    testing and evaluation before it can be accepted and versioned.
    """

    def __init__(self, root: Path | str, state_file: Optional[Path] = None):
        self.root = Path(root)
        self.state_file = state_file or self.root / ".agent" / "orion" / "evolution" / "state.json"
        self._state = self._load_state()

    def _load_state(self) -> dict:
        if not self.state_file.exists():
            return {"proposals": [], "current_version": "0.1.0", "versions": []}

        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception:
            return {"proposals": [], "current_version": "0.1.0", "versions": []}

    def _save_state(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self._state, indent=2), encoding="utf-8")

    def create_proposal(
        self,
        title: str,
        problem: str,
        evidence: List[str],
        proposed_change: str,
        expected_benefit: str,
        risk: str,
        test_plan: str,
    ) -> EvolutionProposal:
        """Create a new evolution proposal."""
        proposal = EvolutionProposal(
            id=f"evolution-{datetime.now().strftime('%Y%m%d')}-{len(self._state.get('proposals', [])) + 1:03d}",
            title=title,
            problem=problem,
            evidence=list(evidence),
            proposed_change=proposed_change,
            expected_benefit=expected_benefit,
            risk=risk,
            test_plan=test_plan,
        )
        self._state.setdefault("proposals", []).append(proposal.to_dict())
        self._save_state()
        return proposal

    def collect_evidence(self, proposal_id: str, evidence: List[str]) -> EvolutionProposal:
        """Add evidence to an existing proposal."""
        proposal = self._get_proposal(proposal_id)
        proposal.evidence.extend(evidence)
        proposal.status = EvolutionStatus.EVIDENCE_COLLECTED
        proposal.updated_at = datetime.now().isoformat()
        self._upsert_proposal(proposal)
        return proposal

    def propose_change(
        self,
        proposal_id: str,
        proposed_change: str,
        expected_benefit: str,
        risk: str,
        test_plan: str,
    ) -> EvolutionProposal:
        """Set or update the proposed change."""
        proposal = self._get_proposal(proposal_id)
        proposal.proposed_change = proposed_change
        proposal.expected_benefit = expected_benefit
        proposal.risk = risk
        proposal.test_plan = test_plan
        proposal.status = EvolutionStatus.PROPOSED
        proposal.updated_at = datetime.now().isoformat()
        self._upsert_proposal(proposal)
        return proposal

    def start_test(self, proposal_id: str) -> EvolutionProposal:
        """Mark a proposal as testing."""
        proposal = self._get_proposal(proposal_id)
        proposal.status = EvolutionStatus.TESTING
        proposal.updated_at = datetime.now().isoformat()
        self._upsert_proposal(proposal)
        return proposal

    def record_test_result(self, proposal_id: str, result: EvolutionTestResult) -> EvolutionProposal:
        """Record the result of a test."""
        proposal = self._get_proposal(proposal_id)
        proposal.test_result = result.to_dict()
        proposal.status = EvolutionStatus.EVALUATING
        proposal.updated_at = datetime.now().isoformat()
        self._upsert_proposal(proposal)
        return proposal

    def evaluate(
        self,
        proposal_id: str,
        evaluation: EvaluationResult,
        decision: EvolutionDecision,
        reason: str,
    ) -> EvolutionProposal:
        """Evaluate a proposal and record a decision."""
        proposal = self._get_proposal(proposal_id)
        proposal.evaluation = evaluation.to_dict()
        proposal.decision = decision
        proposal.decision_reason = reason
        proposal.status = (
            EvolutionStatus.ACCEPTED
            if decision == EvolutionDecision.ACCEPT
            else EvolutionStatus.REJECTED
        )
        proposal.updated_at = datetime.now().isoformat()
        self._upsert_proposal(proposal)
        return proposal

    def accept(self, proposal_id: str, version: str) -> EvolutionProposal:
        """Accept a proposal and version it."""
        proposal = self._get_proposal(proposal_id)
        proposal.decision = EvolutionDecision.ACCEPT
        proposal.status = EvolutionStatus.VERSIONED
        proposal.version = version
        proposal.updated_at = datetime.now().isoformat()

        versions = self._state.setdefault("versions", [])
        versions.append({
            "version": version,
            "proposal_id": proposal_id,
            "title": proposal.title,
            "accepted_at": datetime.now().isoformat(),
        })
        self._state["current_version"] = version
        self._upsert_proposal(proposal)
        return proposal

    def reject(self, proposal_id: str, reason: str) -> EvolutionProposal:
        """Reject a proposal."""
        proposal = self._get_proposal(proposal_id)
        proposal.decision = EvolutionDecision.REJECT
        proposal.decision_reason = reason
        proposal.status = EvolutionStatus.REJECTED
        proposal.updated_at = datetime.now().isoformat()
        self._upsert_proposal(proposal)
        return proposal

    def get_proposal(self, proposal_id: str) -> EvolutionProposal:
        """Get a proposal by ID."""
        return self._get_proposal(proposal_id)

    def get_all_proposals(self) -> List[EvolutionProposal]:
        """Get all proposals."""
        return [
            self._proposal_from_dict(item)
            for item in self._state.get("proposals", [])
        ]

    def get_current_version(self) -> str:
        """Get the current ORION version."""
        return self._state.get("current_version", "0.1.0")

    def get_versions(self) -> List[dict]:
        """Get version history."""
        return list(self._state.get("versions", []))

    def _get_proposal(self, proposal_id: str) -> EvolutionProposal:
        for item in self._state.get("proposals", []):
            if item.get("id") == proposal_id:
                return self._proposal_from_dict(item)
        raise KeyError(f"Evolution proposal not found: {proposal_id}")

    def _upsert_proposal(self, proposal: EvolutionProposal) -> None:
        proposals = self._state.setdefault("proposals", [])
        data = proposal.to_dict()
        for i, item in enumerate(proposals):
            if item.get("id") == proposal.id:
                proposals[i] = data
                break
        else:
            proposals.append(data)
        self._save_state()

    def _proposal_from_dict(self, data: dict) -> EvolutionProposal:
        return EvolutionProposal(
            id=data["id"],
            title=data["title"],
            problem=data["problem"],
            evidence=list(data.get("evidence", [])),
            proposed_change=data["proposed_change"],
            expected_benefit=data["expected_benefit"],
            risk=data["risk"],
            test_plan=data["test_plan"],
            status=EvolutionStatus(data["status"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            test_result=data.get("test_result"),
            evaluation=data.get("evaluation"),
            decision=EvolutionDecision(data["decision"]) if data.get("decision") else None,
            decision_reason=data.get("decision_reason", ""),
            version=data.get("version"),
        )
