"""
ORION Persona Router

Selects and activates the appropriate persona for a given task.
Integrates with the Model Adapter to route work through the right expertise.

Architecture:
    TASK OBJECTIVE
        ↓
    PERSONA ROUTER
        ↓
    ANALYZE domain, complexity, required expertise
        ↓
    SELECT best persona
        ↓
    LOAD persona identity, memory, knowledge, skills, experience
        ↓
    ACTIVATE for task execution
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .model import ModelConfig, PersonaSelection, SimpleModelAdapter


class PersonaStatus(str, Enum):
    """Persona activation state."""
    INACTIVE = "inactive"
    STANDBY = "standby"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


@dataclass
class PersonaDefinition:
    """Complete persona definition loaded from disk."""
    name: str
    role: str
    purpose: str
    boundaries: List[str] = field(default_factory=list)
    style: str = ""
    tools: List[str] = field(default_factory=list)
    memory: str = ""
    knowledge: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    experience: List[str] = field(default_factory=list)
    evaluation_criteria: List[str] = field(default_factory=list)
    level: int = 1
    
    @classmethod
    def from_file(cls, path: Path) -> Optional["PersonaDefinition"]:
        """Load persona definition from a markdown file."""
        try:
            content = path.read_text(encoding="utf-8")
            return cls._parse_markdown(content, path.stem)
        except Exception:
            return None
    
    @classmethod
    def _parse_markdown(cls, content: str, name: str) -> "PersonaDefinition":
        """Parse markdown content into a PersonaDefinition."""
        persona = PersonaDefinition(name=name)
        
        lines = content.split("\n")
        current_section = None
        section_content = []
        
        for line in lines:
            # Section headers
            if line.startswith("# "):
                if current_section and section_content:
                    setattr(persona, current_section, "\n".join(section_content).strip())
                current_section = None
                section_content = []
                continue
            elif line.startswith("## "):
                if current_section and section_content:
                    setattr(persona, current_section, "\n".join(section_content).strip())
                current_section = line[3:].strip().lower().replace(" ", "_")
                section_content = []
                continue
            
            if current_section:
                section_content.append(line)
        
        # Handle last section
        if current_section and section_content:
            setattr(persona, current_section, "\n".join(section_content).strip())
        
        return persona
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "role": self.role,
            "purpose": self.purpose,
            "boundaries": self.boundaries,
            "style": self.style,
            "tools": self.tools,
            "memory": self.memory[:200] + "..." if len(self.memory) > 200 else self.memory,
            "knowledge": self.knowledge,
            "skills": self.skills,
            "experience": self.experience,
            "evaluation_criteria": self.evaluation_criteria,
            "level": self.level,
        }


@dataclass
class PersonaContext:
    """Runtime context loaded for an active persona."""
    persona: PersonaDefinition
    identity_content: str = ""
    memory_content: str = ""
    knowledge_content: str = ""
    skills_content: str = ""
    experience_content: str = ""
    shared_memory: str = ""
    shared_knowledge: str = ""
    
    def get_context_summary(self) -> str:
        """Get a brief summary of the loaded context."""
        parts = []
        if self.identity_content:
            parts.append("Identity loaded")
        if self.memory_content:
            parts.append(f"Memory: {len(self.memory_content)} chars")
        if self.shared_memory:
            parts.append(f"Shared memory: {len(self.shared_memory)} chars")
        if self.knowledge_content:
            parts.append(f"Knowledge: {len(self.knowledge_content)} chars")
        if self.experience_content:
            parts.append(f"Experience: {len(self.experience_content)} chars")
        return ", ".join(parts) if parts else "No context loaded"
    
    def total_tokens_estimate(self) -> int:
        """Estimate total tokens in context."""
        total_chars = sum(len(x) for x in [
            self.identity_content, self.memory_content,
            self.knowledge_content, self.skills_content,
            self.experience_content, self.shared_memory, self.shared_knowledge
        ])
        return total_chars // 4


class PersonaRouter:
    """
    Routes tasks to appropriate personas.
    
    Handles:
    1. Persona discovery (scanning definitions)
    2. Persona selection (matching task to persona)
    3. Context loading (loading persona knowledge)
    4. Activation (marking persona as active)
    """
    
    def __init__(
        self,
        root: Path,
        model_config: Optional[ModelConfig] = None,
        model_adapter: Optional[SimpleModelAdapter] = None,
    ):
        self.root = root
        self.personas_dir = root / ".agent" / "orion" / "personas" / "definitions"
        self.shared_dir = root / ".agent" / "shared"
        self.model_adapter = model_adapter or SimpleModelAdapter(
            model_config or ModelConfig(), root
        )
        self._definitions: Dict[str, PersonaDefinition] = {}
        self._active_persona: Optional[PersonaContext] = None
        self._load_definitions()
    
    def _load_definitions(self) -> None:
        """Load all persona definitions from disk."""
        if not self.personas_dir.exists():
            self.personas_dir.mkdir(parents=True, exist_ok=True)
            return
        
        for md_file in self.personas_dir.glob("*.md"):
            persona = PersonaDefinition.from_file(md_file)
            if persona:
                self._definitions[persona.name] = persona
    
    def get_available_personas(self) -> Dict[str, PersonaDefinition]:
        """Return all loaded persona definitions."""
        return dict(self._definitions)
    
    def select_persona(self, task_objective: str, task_context: dict) -> PersonaSelection:
        """
        Select the best persona for a given task.
        
        Uses model adapter for intelligent selection,
        falls back to keyword matching if model unavailable.
        """
        # Use model adapter if available
        if self.model_adapter and self.model_adapter.config.provider != "simple":
            try:
                selection = self.model_adapter.select_persona(task_objective, task_context)
                return selection
            except Exception:
                pass
        
        # Fallback to keyword-based selection
        return self._keyword_select(task_objective, task_context)
    
    def _keyword_select(self, objective: str, context: dict) -> PersonaSelection:
        """Simple keyword-based persona selection."""
        objective_lower = objective.lower()
        
        patterns = {
            "engineer": ["code", "python", "implement", "fix", "bug", "debug", "compile", "test"],
            "researcher": ["research", "investigate", "study", "analyze", "examine"],
            "architect": ["architecture", "design", "structure", "pattern", "framework"],
            "analyst": ["analyze", "review", "audit", "evaluate", "assess", "compare"],
            "security": ["security", "vulnerability", "attack", "penetration", "auth", "permission"],
            "operations": ["deploy", "release", "production", "run", "execute"],
            "manager": ["plan", "coordinate", "manage", "organize", "schedule"],
        }
        
        best_persona = "default"
        best_score = 0.3
        
        for persona, keywords in patterns.items():
            matches = sum(1 for kw in keywords if kw in objective_lower)
            if matches > 0:
                score = min(0.9, 0.3 + matches * 0.15)
                if score > best_score:
                    best_score = score
                    best_persona = persona
        
        # Check if persona exists in definitions
        if best_persona in self._definitions:
            best_score = 0.8
        
        return PersonaSelection(
            persona_name=best_persona,
            confidence=best_score,
            reasoning=f"Keyword match: {best_persona} (score: {best_score:.2f})",
            required_knowledge=[f"knowledge/{best_persona}"] if best_persona != "default" else [],
        )
    
    def activate_persona(self, persona_name: str) -> PersonaContext:
        """
        Activate a persona and load its full context.
        
        1. Load persona definition
        2. Load identity.md
        3. Load memory/ directory
        4. Load knowledge/ directory
        5. Load skills/ directory
        6. Load experience/ directory
        7. Load shared memory/knowledge
        8. Return PersonaContext
        """
        definition = self._definitions.get(persona_name)
        if not definition and persona_name != "default":
            return None
        
        if definition is None:
            definition = PersonaDefinition(name="default", role="Assistant")
        
        # Build persona context
        context = PersonaContext(persona=definition)
        
        # Load identity
        identity_path = self.personas_dir / persona_name / "identity.md"
        if identity_path.exists():
            context.identity_content = identity_path.read_text(encoding="utf-8")
        
        # Load memory directory
        memory_dir = self.personas_dir / persona_name / "memory"
        if memory_dir.exists():
            memory_parts = []
            for md_file in sorted(memory_dir.rglob("*.md")):
                try:
                    memory_parts.append(md_file.read_text(encoding="utf-8"))
                except Exception:
                    pass
            context.memory_content = "\n\n".join(memory_parts)
        
        # Also load from .agent/orion/memory/
        orion_memory_dir = self.root / ".agent" / "orion" / "memory"
        if orion_memory_dir.exists():
            for md_file in sorted(orion_memory_dir.rglob("*.md")):
                try:
                    context.memory_content += "\n\n" + md_file.read_text(encoding="utf-8")
                except Exception:
                    pass
        
        # Load knowledge directory
        knowledge_dir = self.personas_dir / persona_name / "knowledge"
        if knowledge_dir.exists():
            knowledge_parts = []
            for md_file in sorted(knowledge_dir.rglob("*.md")):
                try:
                    knowledge_parts.append(md_file.read_text(encoding="utf-8"))
                except Exception:
                    pass
            context.knowledge_content = "\n\n".join(knowledge_parts)
        
        # Load shared memory/knowledge
        shared_memory_dir = self.shared_dir / "memory"
        if shared_memory_dir.exists():
            shared_parts = []
            for md_file in sorted(shared_memory_dir.rglob("*.md")):
                try:
                    shared_parts.append(md_file.read_text(encoding="utf-8"))
                except Exception:
                    pass
            context.shared_memory = "\n\n".join(shared_parts)
        
        shared_knowledge_dir = self.shared_dir / "knowledge"
        if shared_knowledge_dir.exists():
            shared_parts = []
            for md_file in sorted(shared_knowledge_dir.rglob("*.md")):
                try:
                    shared_parts.append(md_file.read_text(encoding="utf-8"))
                except Exception:
                    pass
            context.shared_knowledge = "\n\n".join(shared_parts)
        
        self._active_persona = context
        return context
    
    def get_active_persona(self) -> Optional[PersonaContext]:
        """Get the currently active persona context."""
        return self._active_persona
    
    def deactivate_persona(self) -> None:
        """Deactivate the current persona."""
        self._active_persona = None
    
    def route_task(
        self,
        task_objective: str,
        task_context: dict
    ) -> dict:
        """
        Complete task routing: select persona, load context, activate.
        
        Returns:
            dict with persona selection, context, and activation status
        """
        # Select persona
        selection = self.select_persona(task_objective, task_context)
        
        # Activate persona
        context = self.activate_persona(selection.persona_name)
        
        return {
            "selection": selection.to_dict() if selection else None,
            "context": context.get_context_summary() if context else "No context loaded",
            "persona_name": selection.persona_name if selection else "default",
            "activated": context is not None,
            "context_tokens_estimate": context.total_tokens_estimate() if context else 0,
        }