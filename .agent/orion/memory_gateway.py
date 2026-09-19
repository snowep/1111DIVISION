"""
ORION Memory Gateway

Bridges persona memory retrieval with the retrieval engine.
Uses the hierarchy: PERSONA → SHARED → ORION → PROJECT
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional


class MemoryGateway:
    """Gate between persona context and stored memory/knowledge."""

    def __init__(self, root: Path):
        self.root = root
        self.personas_dir = root / ".agent" / "orion" / "personas"
        self.shared_dir = root / ".agent" / "shared"
        self.orion_dir = root / ".agent" / "orion"

    def retrieve_for_persona(self, persona_name: str, budget: str = "standard") -> dict:
        """Retrieve memory/knowledge/experience for a persona."""
        result = {"memory": [], "knowledge": [], "experience": [], "persona": persona_name}
        # Persona-specific
        persona_memory = self.personas_dir / persona_name / "memory"
        if persona_memory.exists():
            result["memory"].extend(self._load_dir(persona_memory))
        # Shared
        shared_memory = self.shared_dir / "memory"
        if shared_memory.exists():
            result["memory"].extend(self._load_dir(shared_memory))
        # Orion
        orion_memory = self.orion_dir / "memory"
        if orion_memory.exists():
            result["memory"].extend(self._load_dir(orion_memory))
        return result

    def _load_dir(self, dir_path: Path) -> List[str]:
        results = []
        for md_file in dir_path.rglob("*.md"):
            try:
                results.append(md_file.read_text(encoding="utf-8")[:2000])
            except Exception:
                pass
        return results
