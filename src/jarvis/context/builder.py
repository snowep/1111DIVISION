"""Runtime context builder.

Assembles the 9-layer runtime context per the architectural composition
order (runtime-spec.md).  Unlike a text-only concatenation, the builder
watches for lower layers attempting to override higher layers' values and
forces deterministic authority resolution.

The builder never mutates any layer's content — it loads each layer's
canonical text from the workspace (where possible), registers it, then
enforces structured precedence before the context is used.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable

from jarvis.errors import LayerOverrideError
from jarvis.io.workspace import Workspace
from jarvis.models.context import ContextLayer, LayerAssertion, RuntimeContext
from jarvis.validation.protocol import authority_is_valid

# Anchors (files) that make up each layer, in canonical order.
_LAYER_FILES = [
    (1, "platform-constraints", None),          # platform constraints = runtime env, no file
    (2, "constitution", ".jarvis/core/constitution.md"),
    (3, "system-prompt", ".jarvis/core/system-prompt.md"),
    (4, "world-model", ".jarvis/core/world-model.md"),
    (7, "task-context", None),                  # caller-supplied text
    (8, "persona-overlay", None),               # activated on demand
    (9, "user-request", None),                  # the agent receives this
]

# Layers 5 and 6 (memory and skills) are query-selected, not loaded
# wholesale.  This builder produces layer 5/6 placeholders that the caller
# fills from the actual memory/skills system.

# Layers 1, 2, and 3 are immutable (cannot be overridden by any lower layer).
_IMMUTABLE_LAYERS = frozenset({1, 2, 3})


class ContextBuilder:
    """Assemble a :class:`RuntimeContext` against the architecture contract.

    The builder loads the fixed layers (1–4) from the workspace. For layers
    5–8 (memory / skills / task context / persona overlay), the caller
    supplies their content after loading.
    """

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace
        self.context = RuntimeContext()

    @property
    def canonical_world_model(self) -> Path:
        return self.workspace.core() / "world-model.md"

    def build_core_layers(self) -> None:
        """Load and register layers 1–4 (immutable core)."""
        # Layer 1 — platform constraints: the runtime never inverts this.
        self.context.add_layer(
            ContextLayer(
                number=1,
                name="platform-constraints",
                content=(
                    "PLATFORM CONSTRAINTS: Open WebUI shell, model context limits, "
                    "tool availability, execution sandbox. Non-negotiable."
                ),
                immutable=True,
            )
        )

        # Layer 2 — constitution.md (immutable)
        self.context.add_layer(
            ContextLayer(
                number=2,
                name="constitution",
                content=self._read_file(self.workspace.core() / "constitution.md"),
                immutable=True,
            )
        )

        # Layer 3 — system prompt (immutable)
        self.context.add_layer(
            ContextLayer(
                number=3,
                name="system-prompt",
                content=self._read_file(self.workspace.core() / "system-prompt.md"),
                immutable=True,
            )
        )

        # Layer 4 — world model (derived — rebuildable, not authoritative)
        self.context.add_layer(
            ContextLayer(
                number=4,
                name="world-model",
                content=self._read_file(self.workspace.core() / "world-model.md"),
            )
        )

        # Register the layers' top-level ordered identifiers so assertion
        # tracking knows the forward order
        assertion_order = (4, 3, 2, 1)  # lower → higher
        for order_prefix, layer_number in zip(assertion_order, (4, 3, 2, 1)):
            self.context.assert_value(
                f"layer:{order_prefix}", layer_number, layer_number
            )

    def add_memory(self, memory_records: Iterable[object]) -> None:
        """Build layer 5 (Relevant Memory) from a set of active records."""
        content = "\n".join(
            f"MEM-{rec.id if hasattr(rec, 'id') else 'UNK'} — "
            f"{getattr(rec, 'status', 'unknown')} — {getattr(rec, 'content', '')[:120]}"
            for rec in memory_records
        )
        self.context.add_layer(
            ContextLayer(
                number=5, name="memory", content=content,
            )
        )
        self.context.assert_value("layer:5", 5, 4)  # memory outranks world model

    def add_skills(self, skills: Iterable[object]) -> None:
        """Build layer 6 (Relevant Skills)."""
        content = "\n".join(
            f"SKILL-{getattr(s, 'id', 'UNK')} — {getattr(s, 'name', 'unnamed')}"
            for s in skills
        )
        self.context.add_layer(
            ContextLayer(
                number=6, name="skills", content=content
            )
        )
        self.context.assert_value("layer:6", 6, 5)  # skills below memory

    def add_task_context(self, content: str) -> None:
        """Build layer 7 (Task Context) from caller-supplied content."""
        self.context.add_layer(
            ContextLayer(
                number=7, name="task-context", content=content,
                metadata={"source": "caller"}
            )
        )
        self.context.assert_value("layer:7", 7, 6)  # task below skills

    def add_persona_overlay(self, persona_id: str, content: str) -> None:
        """Build layer 8 (Persona Overlay)."""
        self.context.add_layer(
            ContextLayer(
                number=8, name="persona-overlay", content=content,
                metadata={"persona_id": persona_id},
            )
        )
        # The persona overlay can *never* override layers 1–3. The
        # constitution layer is layer 2 — this assertion would raise if the
        # persona tried to assert over, e.g., layer:2.
        self.context.assert_value(
            "persona_id", persona_id, 8
        )

    def add_user_request(self, content: str) -> None:
        """Build layer 9 (User Request)."""
        self.context.add_layer(
            ContextLayer(
                number=9, name="user-request", content=content,
                metadata={"source": "runtime"}
            )
        )

        # User Request (layer 9) may override layers 4-8 for task-specific
        # decisions — encoded as a special assertion the precedence system
        # will enforce automatically if a higher layer has already claimed
        # the same key.
        self.context.assert_value("user_request.active", True, 9)

    def assemble(self) -> RuntimeContext:
        """Return the fully assembled RuntimeContext.

        This is the immutable product of the builder.  It contains every
        layer, in priority order, plus any registered assertions.
        """
        return self.context

    # ---- internal helpers ----------------------------------------------

    def _read_file(self, path: Path) -> str:
        """Read a file if it exists; return '' when absent (not-null invariant)."""
        if path is None:
            return ""
        full_path = self.workspace.resolve_read(path, must_exist=False)
        return full_path.read_text(encoding="utf-8") if full_path.is_file() else ""

    # ---- Allowed layer overrides ------------------------------------------------

    def override_layer_value(
        self,
        key: str,
        value: Any,
        by_layer_number: int,
    ) -> None:
        """Explicitly register an override by another layer (caller-driven).

        Used to encode the one exception in runtime-spec.md:
        layer 9 (user request) can override layers 4–8 for task-specific
        decisions.  This is the *only* sanctioned override hook; any other
        attempt to override via ``assert_value`` will raise.
        """
        if not (1 <= by_layer_number <= 9):
            raise ValueError(f"Layer number must be 1–9, got {by_layer_number}")

        if by_layer_number in _IMMUTABLE_LAYERS:
            raise LayerOverrideError(
                f"Layer {by_layer_number} is immutable — it can never be "
                f"overridden by another layer.",
                path=key,
                code="immutable_override",
            )

        self.context.assert_value(key, value, by_layer_number)

    # ---- Private utilities -----------------------------------------------------

    def _register_assertion(self, key: str, value: Any, layer_number: int) -> None:
        """Register a value assertion via the precedence-enforcing path."""
        self.context.assert_value(key, value, layer_number)