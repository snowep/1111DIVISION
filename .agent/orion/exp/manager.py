"""
ORION Experience Points (EXP) Manager

Core rule:
    Task completed → Verified → Experience recorded → EXP awarded → Level updated

EXP measures verified useful experience, not activity volume.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..evaluator import EvaluationResult


class EXPEventResult(str, Enum):
    """Result of an EXP event."""
    AWARDED = "AWARDED"
    REJECTED = "REJECTED"
    DUPLICATE = "DUPLICATE"


@dataclass
class EXPLevel:
    """A level in the EXP progression system."""
    name: str
    min_exp: int
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "min_exp": self.min_exp,
            "description": self.description,
        }


@dataclass
class EXPRecord:
    """A single EXP record."""
    task_id: str
    exp_awarded: int
    event: str
    outcome: str
    lesson: str
    source: str = "task"
    awarded_at: str = field(default_factory=lambda: datetime.now().isoformat())
    verification_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "exp_awarded": self.exp_awarded,
            "event": self.event,
            "outcome": self.outcome,
            "lesson": self.lesson,
            "source": self.source,
            "awarded_at": self.awarded_at,
            "verification_score": round(self.verification_score, 4),
            "metadata": self.metadata,
        }


@dataclass
class EXPEvent:
    """An event that may produce EXP."""
    task_id: str
    event: str
    outcome: str
    lesson: str
    verification_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "event": self.event,
            "outcome": self.outcome,
            "lesson": self.lesson,
            "verification_score": self.verification_score,
            "metadata": self.metadata,
        }


class EXPManager:
    """
    Manages experience points and level progression.

    EXP is only awarded for verified, useful work. Activity alone never
    earns EXP.
    """

    DEFAULT_LEVELS = [
        EXPLevel("Novice", 0, "Beginning to build verified experience."),
        EXPLevel("Experienced", 100, "Consistently produces verified useful work."),
        EXPLevel("Reliable", 500, "Dependable across repeated task types."),
        EXPLevel("Specialized", 1500, "Deep verified experience in specific domains."),
        EXPLevel("Advanced", 5000, "Highly experienced with strong verification history."),
    ]

    def __init__(
        self,
        root: Path | str,
        levels: Optional[List[EXPLevel]] = None,
        awards: Optional[Dict[str, int]] = None,
        state_file: Optional[Path] = None,
    ):
        self.root = Path(root)
        self.levels = levels or list(self.DEFAULT_LEVELS)
        self.awards = awards or {
            "simple_verified": 10,
            "normal_verified": 25,
            "complex_verified": 50,
            "major_contribution": 100,
            "recovery": 10,
            "reusable_improvement": 10,
            "important_discovery": 10,
            "exceptional_verification": 10,
        }
        self.state_file = state_file or self.root / ".agent" / "orion" / "exp" / "state.json"
        self.records_file = self.root / ".agent" / "orion" / "exp" / "records.json"
        self._state = self._load_state()

    def _load_state(self) -> dict:
        if not self.state_file.exists():
            return {"total_exp": 0, "level": self.levels[0].name, "tasks_verified": 0}

        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception:
            return {"total_exp": 0, "level": self.levels[0].name, "tasks_verified": 0}

    def _save_state(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self._state, indent=2), encoding="utf-8")

    def _save_records(self) -> None:
        self.records_file.parent.mkdir(parents=True, exist_ok=True)
        records = self._state.get("records", [])
        self.records_file.write_text(json.dumps(records, indent=2), encoding="utf-8")

    def get_level_for_exp(self, total_exp: int) -> EXPLevel:
        """Return the level corresponding to an EXP total."""
        current = self.levels[0]
        for level in self.levels:
            if total_exp >= level.min_exp:
                current = level
        return current

    def get_current_level(self) -> EXPLevel:
        """Return the current level."""
        return self.get_level_for_exp(int(self._state.get("total_exp", 0)))

    def is_verified_useful(self, evaluation: EvaluationResult) -> bool:
        """
        Determine whether work qualifies for EXP.

        EXP requires:
        1. The task passed evaluation.
        2. Verification evidence exists.
        3. The result is not a duplicate of already-awarded work.
        """
        return evaluation.passed and evaluation.score >= 0.8

    def award(
        self,
        task_id: str,
        evaluation: EvaluationResult,
        event: str = "task_completed",
        outcome: str = "success",
        lesson: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EXPEventResult:
        """
        Award EXP for a verified task.

        Returns:
            EXPEventResult indicating whether EXP was awarded, rejected, or duplicate.
        """
        if not self.is_verified_useful(evaluation):
            return EXPEventResult.REJECTED

        if self._has_task_record(task_id):
            return EXPEventResult.DUPLICATE

        amount = self._calculate_amount(evaluation, event)
        if amount <= 0:
            return EXPEventResult.REJECTED

        record = EXPRecord(
            task_id=task_id,
            exp_awarded=amount,
            event=event,
            outcome=outcome,
            lesson=lesson,
            verification_score=evaluation.score,
            metadata=metadata or {},
        )

        records = self._state.setdefault("records", [])
        records.append(record.to_dict())
        self._state["total_exp"] = int(self._state.get("total_exp", 0)) + amount
        self._state["tasks_verified"] = int(self._state.get("tasks_verified", 0)) + 1
        self._state["level"] = self.get_level_for_exp(self._state["total_exp"]).name
        self._state["last_awarded_at"] = datetime.now().isoformat()

        self._save_state()
        self._save_records()
        return EXPEventResult.AWARDED

    def _calculate_amount(self, evaluation: EvaluationResult, event: str) -> int:
        """Calculate EXP amount based on verified usefulness."""
        base = self.awards.get(event, self.awards.get("normal_verified", 0))

        # Verification quality adjusts the award, but never below the base.
        quality_multiplier = 1.0 + max(0.0, evaluation.score - 0.8)
        return max(base, int(base * quality_multiplier))

    def _has_task_record(self, task_id: str) -> bool:
        return any(
            record.get("task_id") == task_id
            for record in self._state.get("records", [])
        )

    def get_records(self) -> List[dict]:
        """Return all EXP records."""
        return list(self._state.get("records", []))

    def get_total_exp(self) -> int:
        """Return total accumulated EXP."""
        return int(self._state.get("total_exp", 0))

    def get_progress(self) -> dict:
        """Return current level and progress toward the next level."""
        total = self.get_total_exp()
        current = self.get_level_for_exp(total)
        next_levels = [level for level in self.levels if level.min_exp > current.min_exp]
        next_level = next_levels[0] if next_levels else None

        return {
            "total_exp": total,
            "level": current.to_dict(),
            "next_level": next_level.to_dict() if next_level else None,
            "progress_to_next": (
                (total - current.min_exp) / (next_level.min_exp - current.min_exp)
                if next_level
                else 1.0
            ),
            "tasks_verified": int(self._state.get("tasks_verified", 0)),
        }

    def reset(self) -> None:
        """Reset EXP state. Intended for tests and explicit user reset."""
        self._state = {
            "total_exp": 0,
            "level": self.levels[0].name,
            "tasks_verified": 0,
            "records": [],
        }
        self._save_state()
        self._save_records()
