"""
ORION Evolution System

Controlled self-improvement through evidence-based proposals.

Pipeline:
    OBSERVE PROBLEM → COLLECT EVIDENCE → PROPOSE CHANGE → TEST → EVALUATE → ACCEPT/REJECT → VERSION
"""

from .engine import (
    EvolutionEngine,
    EvolutionProposal,
    EvolutionStatus,
    EvolutionTestResult,
    EvolutionDecision,
)

__all__ = [
    "EvolutionEngine",
    "EvolutionProposal",
    "EvolutionStatus",
    "EvolutionTestResult",
    "EvolutionDecision",
]
