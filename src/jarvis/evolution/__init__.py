"""evolution: propose → validate → apply → revert, no silent edits."""
from jarvis.evolution.engine import (
    EvolutionError,
    FileChange,
    Proposal,
    apply,
    propose,
    revert,
    validate,
)

__all__ = [
    "EvolutionError", "FileChange", "Proposal",
    "apply", "propose", "revert", "validate",
]