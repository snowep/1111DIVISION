"""
ORION Model Adapter

The bridge between ORION's internal systems and an LLM.
This enables the runtime loop: model → persona → memory → tools → verification → experience → evolution.

Architecture:
    USER INPUT
        ↓
    MODEL ADAPTER ←→ (LLM/Chat API)
        ↓
    PERSONA ROUTER
        ↓
    MEMORY GATEWAY
        ↓
    TOOL ENGINE
        ↓
    VERIFICATION
        ↓
    EXPERIENCE
        ↓
    EVOLUTION
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Literal
from pathlib import Path


class ModelRole(str, Enum):
    """Roles in the ORION conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolCallMode(str, Enum):
    """How tool calls are handled."""
    STRUCTURED = "structured"  # JSON tool calls
    NATURAL = "natural"        # Natural language tool invocation


@dataclass
class ModelConfig:
    """Configuration for the Model Adapter."""
    provider: str = "openai"  # openai, anthropic, ollama, etc.
    model: str = "gpt-4"
    temperature: float = 0.1
    max_tokens: int = 4096
    tool_mode: ToolCallMode = ToolCallMode.STRUCTURED
    timeout: int = 30
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    # Rate limiting
    rpm: int = 60  # requests per minute
    tpm: int = 10000  # tokens per minute
    
    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "tool_mode": self.tool_mode.value,
            "timeout": self.timeout,
            "base_url": self.base_url,
            "api_key": "[REDACTED]" if self.api_key else None,
            "rpm": self.rpm,
            "tpm": self.tpm,
        }


@dataclass
class ModelMessage:
    """A single message in the conversation."""
    role: ModelRole
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_results: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "role": self.role.value,
            "content": self.content,
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results,
            "metadata": self.metadata,
        }


@dataclass
class ModelResponse:
    """Response from the model."""
    content: str
    tool_calls: List[Dict] = field(default_factory=list)
    finish_reason: str = "stop"
    usage: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "tool_calls": self.tool_calls,
            "finish_reason": self.finish_reason,
            "usage": self.usage,
            "metadata": self.metadata,
        }


@dataclass
class PersonaSelection:
    """Result of persona selection analysis."""
    persona_name: str
    confidence: float  # 0.0 - 1.0
    reasoning: str
    required_knowledge: List[str] = field(default_factory=list)


class ModelAdapterInterface:
    """
    Interface that the actual model implementation must follow.
    
    This is the contract for connecting to any LLM provider.
    """
    
    def __init__(self, config: ModelConfig, root: Path):
        self.config = config
        self.root = root
        self._messages: List[ModelMessage] = []
    
    def initialize(self) -> bool:
        """Initialize the model connection. Returns True if successful."""
        raise NotImplementedError
    
    def reset(self) -> None:
        """Clear conversation history."""
        self._messages = []
    
    def append_message(self, message: ModelMessage) -> None:
        """Add a message to the conversation."""
        self._messages.append(message)
    
    def get_messages(self, include_tool_results: bool = True) -> List[ModelMessage]:
        """Get conversation messages, optionally including tool results."""
        if not include_tool_results:
            return [m for m in self._messages if m.tool_results is None]
        return list(self._messages)
    
    def count_tokens(self, messages: List[ModelMessage]) -> dict:
        """Estimate token usage for messages."""
        # Simple approximation: ~4 chars/word ~ 0.75 tokens/word
        total_chars = sum(len(str(m.content)) for m in messages)
        estimated_tokens = total_chars // 4
        return {
            "total": estimated_tokens,
            "prompt_tokens": int(estimated_tokens * 0.7),
            "completion_tokens": int(estimated_tokens * 0.3),
        }
    
    def select_persona(self, objective: str, context: dict) -> PersonaSelection:
        """
        Analyze the task and select the most appropriate persona.
        
        This is a fallback to simple keyword matching when persona
        definitions are not available.
        """
        raise NotImplementedError
    
    def invoke(
        self,
        messages: Optional[List[ModelMessage]] = None,
        stream: bool = False,
        tools: Optional[List[dict]] = None,
    ) -> ModelResponse:
        """Generate a response from the model."""
        raise NotImplementedError
    
    def can_handle_tool_calls(self) -> bool:
        """Check if this model can handle structured tool calls."""
        return self.config.tool_mode == ToolCallMode.STRUCTURED
    
    def format_tool_result(self, tool_name: str, result: dict, success: bool) -> ModelMessage:
        """Format a tool result as a message."""
        return ModelMessage(
            role=ModelRole.TOOL,
            content=f"Tool {tool_name} result: {result.get('output') or 'completed'}",
            tool_results={"tool": tool_name, "result": result, "success": success},
        )


class SimpleModelAdapter(ModelAdapterInterface):
    """
    A simple model adapter that provides basic functionality.
    
    This is used when an actual LLM is not available, providing
    basic reasoning and persona selection capabilities.
    """
    
    def initialize(self) -> bool:
        """Simple initialization - always succeeds."""
        return True
    
    def select_persona(self, objective: str, context: dict) -> PersonaSelection:
        """Simple keyword-based persona selection."""
        objective_lower = objective.lower()
        
        # Keyword patterns for persona selection
        patterns = {
            "code": ["code", "python", "javascript", "rust", "go", "java", "c++", "implement", "fix", "debug", "refactor"],
            "research": ["research", "investigate", "analyze", "study", "examine", "compare"],
            "analysis": ["analyze", "analyze", "audit", "review", "evaluate", "assessment", "assessment"],
            "architecture": ["architecture", "design", "design", "structure", "pattern", "framework"],
            "security": ["security", "vulnerability", "attack", "penetration", "auth", "permission", "credential"],
            "operations": ["deploy", "release", "production", "run", "execute", "build", "test"],
            "debug": ["bug", "error", "fail", "crash", "issue", "problem"],
        }
        
        best_match = "default"
        best_score = 0.5
        matching_knowledge = []
        
        for persona_type, keywords in patterns.items():
            matches = sum(1 for kw in keywords if kw in objective_lower)
            if matches > 0:
                score = 0.3 + (matches / len(keywords)) * 0.5
                if score > best_score:
                    best_score = score
                    best_match = persona_type
                    matching_knowledge = [f"knowledge/{persona_type}", f"skills/{persona_type}"]
        
        # Check for existing persona files
        personas_dir = self.root / ".agent" / "orion" / "personas" / "definitions"
        if personas_dir.exists():
            persona_files = [f.stem for f in personas_dir.glob("*.md")]
            persona_types = {f.replace("-", " ") for f in persona_files}
            for p in persona_types:
                if p in objective_lower:
                    best_match = p
                    best_score = 0.9
                    matching_knowledge = [f"persona/{p}/", "experience/"]
                    break
        
        return PersonaSelection(
            persona_name=best_match,
            confidence=best_score,
            reasoning=f"Matched {best_match} with score {best_score:.2f}",
            required_knowledge=matching_knowledge,
        )
    
    def invoke(
        self,
        messages: Optional[List[ModelMessage]] = None,
        stream: bool = False,
        tools: Optional[List[dict]] = None,
    ) -> ModelResponse:
        """Generate a response using available tools."""
        messages = messages or self._messages
        
        # Collect all tool results
        tool_results = {}
        for m in messages:
            if m.tool_results:
                tool_results[m.tool_results.get("tool")] = m.tool_results.get("result")
        
        # Build the effective context
        context_parts = []
        for m in messages:
            if m.role == ModelRole.USER:
                context_parts.append(f"**INPUT:** {m.content}")
            elif m.role == ModelRole.SYSTEM:
                context_parts.append(f"**SYSTEM:** {m.content}")
            elif m.role == ModelRole.ASSISTANT:
                context_parts.append(f"**THINKING:** {m.content}")
            elif m.role == ModelRole.TOOL:
                result = m.tool_results
                if result:
                    context_parts.append(f"**TOOL {result.get('tool')}:** `{result.get('result', {}).get('output')}`")
        
        full_context = "\n\n".join(context_parts)
        
        # Simple reasoning: identify what needs to be done
        analysis = {
            "context": full_context[:2000],  # Limit context size
            "has_tool_results": len(tool_results) > 0,
            "tool_results": tool_results,
        }
        
        # Generate response based on context
        if tools:
            # We have tools available - suggest next action
            response = self._suggest_next_action(full_context, tool_results)
        else:
            response = self._generate_response(full_context)
        
        return ModelResponse(
            content=response,
            tool_calls=[],
            finish_reason="stop",
            usage=self.count_tokens(messages),
            metadata=analysis,
        )
    
    def _suggest_next_action(self, context: str, tool_results: dict) -> str:
        """Suggest the next action based on context."""
        if tool_results:
            last_result = list(tool_results.values())[-1]
            if isinstance(last_result, dict):
                if last_result.get("success"):
                    return "Tool executed successfully. Please specify next action."
                else:
                    return f"Tool failed: {last_result.get('error')}. Suggesting alternative approach."
        
        # Check for completion patterns
        completion_keywords = ["done", "complete", "finished", "success"]
        if any(kw in context.lower() for kw in completion_keywords):
            return "Task appears to be complete. Verify results and summarize."
        
        # Default: continue
        return "Continue with next logical step in the workflow."
    
    def _generate_response(self, context: str) -> str:
        """Generate a standard response."""
        return "I have analyzed the context. Please let me know what you'd like me to do next."


# Placeholder for actual LLM integration
class OpenAIAdapter(ModelAdapterInterface):
    """OpenAI API adapter (placeholder for actual implementation)."""
    
    def initialize(self) -> bool:
        """Initialize OpenAI client."""
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=self.config.api_key or "",
                base_url=self.config.base_url,
            )
            return True
        except ImportError:
            return False
    
    def invoke(
        self,
        messages: Optional[List[ModelMessage]] = None,
        stream: bool = False,
        tools: Optional[List[dict]] = None,
    ) -> ModelResponse:
        """Invoke OpenAI API."""
        raise NotImplementedError("OpenAI adapter not fully implemented")


class AnthropicAdapter(ModelAdapterInterface):
    """Anthropic API adapter (placeholder)."""
    
    def initialize(self) -> bool:
        try:
            import anthropic
            self.client = anthropic.Anthropic(
                api_key=self.config.api_key or "",
                base_url=self.config.base_url,
            )
            return True
        except ImportError:
            return False
    
    def invoke(
        self,
        messages: Optional[List[ModelMessage]] = None,
        stream: bool = False,
        tools: Optional[List[dict]] = None,
    ) -> ModelResponse:
        """Invoke Anthropic API."""
        raise NotImplementedError("Anthropic adapter not fully implemented")


def create_model_adapter(config: ModelConfig, root: Path) -> ModelAdapterInterface:
    """Factory function to create the appropriate model adapter."""
    adapters = {
        "openai": OpenAIAdapter,
        "anthropic": AnthropicAdapter,
        "simple": SimpleModelAdapter,
    }
    
    adapter_class = adapters.get(config.provider, SimpleModelAdapter)
    adapter = adapter_class(config, root)
    
    if config.provider in ["openai", "anthropic"]:
        adapter.initialize()
    
    return adapter